"""Own the schedules shown in the Schedule Viewer and their serialization."""

import re
from dataclasses import dataclass
from pathlib import Path

from scheduler.models.course import CourseInstance
from scheduler.config import CombinedConfig
from src.models.schedule_files import (
    SAVED_NAME_PATTERN,
    parse_schedule_file,
    records_from_result,
    records_to_csv,
    records_to_json,
)
from src.models.schedule_result import ScheduleResult


SCHEDULE_DIRECTORY = Path(__file__).resolve().parents[1] / "schedules"
FORMATS = {"csv": "text/csv", "json": "application/json"}


@dataclass
class ScheduleEntry:
    """One schedule the viewer can show."""
    label: str
    config_name: str
    source: str                       # "generated" or "file"
    records: list[dict[str, str]]
    config: CombinedConfig | None = None
    schedule: list[CourseInstance] | None = None
    file_name: str | None = None      # set for schedules loaded from a file


def _natural_key(name: str) -> list:
    """Sort 'x_schedule2' before 'x_schedule10'."""
    return [int(part) if part.isdigit() else part.lower() for part in re.split(r"(\d+)", name)]


class ScheduleViewerModel:
    def __init__(self, directory: Path = SCHEDULE_DIRECTORY) -> None:
        self.directory = Path(directory)
        self._generated: list[ScheduleEntry] = []
        self._generated_results: list[ScheduleResult] = []
        self._loaded: list[ScheduleEntry] = []
        self.selected_index = 0

    # ------------------------------------------------------------------
    # Entries and selection
    # ------------------------------------------------------------------

    @property
    def entries(self) -> list[ScheduleEntry]:
        """Generated schedules first, then schedules loaded from files."""
        return self._generated + self._loaded

    @property
    def current(self) -> ScheduleEntry | None:
        entries = self.entries
        if not entries:
            return None
        self.selected_index = max(0, min(self.selected_index, len(entries) - 1))
        return entries[self.selected_index]

    def select(self, index: int) -> None:
        self.selected_index = max(0, min(index, len(self.entries) - 1))

    def set_generated(self, results: list[ScheduleResult]) -> bool:
        """Replace the generated entries if the generator's results changed.

        Returns True when something changed. Compares the result objects
        themselves, so polling this is cheap.
        """
        unchanged = len(results) == len(self._generated_results) and all(
            new is old for new, old in zip(results, self._generated_results)
        )
        if unchanged:
            return False

        self._generated_results = list(results)
        self._generated = [
            ScheduleEntry(
                label=f"{result.config_name} — schedule {number} (generated)",
                config_name=result.config_name,
                source="generated",
                records=records_from_result(result),
                config=result.config,
                schedule=result.schedule,
            )
            for number, result in enumerate(results, start=1)
        ]
        # Jump to the first new schedule; otherwise keep the viewer valid.
        self.selected_index = 0
        return True

    # ------------------------------------------------------------------
    # Loading
    # ------------------------------------------------------------------

    def list_saved_files(self) -> list[str]:
        try:
            names = [
                path.name
                for path in self.directory.iterdir()
                if path.is_file() and path.suffix.lower() in {".csv", ".json"}
            ]
        except OSError:
            return []
        return sorted(names, key=_natural_key)

    def load_saved_file(self, file_name: str) -> ScheduleEntry:
        path = (self.directory / file_name).resolve()
        if path.parent != self.directory.resolve():
            raise ValueError("Schedules can only be loaded from the schedules folder.")
        try:
            content = path.read_bytes()
        except FileNotFoundError as error:
            raise ValueError(f"'{file_name}' no longer exists.") from error
        return self.load_bytes(file_name, content)

    def load_bytes(self, file_name: str, content: bytes) -> ScheduleEntry:
        """Parse a schedule file and add it to the viewer (or refresh it if already loaded)."""
        config_name, records = parse_schedule_file(file_name, content)
        entry = ScheduleEntry(
            label=f"{file_name} (file)",
            config_name=config_name,
            source="file",
            records=records,
            file_name=file_name,
        )

        for position, existing in enumerate(self._loaded):
            if existing.file_name == file_name:
                self._loaded[position] = entry
                break
        else:
            self._loaded.append(entry)
            position = len(self._loaded) - 1

        self.selected_index = len(self._generated) + position
        return entry

    # ------------------------------------------------------------------
    # Exporting
    # ------------------------------------------------------------------

    @staticmethod
    def serialize(entry: ScheduleEntry, file_format: str) -> bytes:
        if file_format == "csv":
            return records_to_csv(entry.records)
        if file_format == "json":
            return records_to_json(entry.records)
        raise ValueError("Please choose CSV or JSON.")

    def default_export_file_name(self, entry: ScheduleEntry, file_format: str) -> str:
        """A loaded file keeps its name; a generated schedule gets the next free
        <config>_schedule<n> name, matching the CLI export."""
        if entry.file_name:
            return f"{Path(entry.file_name).stem}.{file_format}"

        taken = set()
        for name in self.list_saved_files():
            match = SAVED_NAME_PATTERN.match(Path(name).stem)
            if match and match.group("config") == entry.config_name:
                taken.add(int(match.group("number")))
        number = 1
        while number in taken:
            number += 1
        return f"{entry.config_name}_schedule{number}.{file_format}"

    def export(
        self, entry: ScheduleEntry, file_format: str, file_name: str
    ) -> tuple[bytes, str, str]:
        """Return file contents, a safe download name, and its media type."""
        if file_format not in FORMATS:
            raise ValueError("Please choose CSV or JSON.")

        file_name = Path(
            file_name.strip()
            or self.default_export_file_name(entry, file_format)
        ).name
        if Path(file_name).suffix.lower() != f".{file_format}":
            file_name = f"{file_name}.{file_format}"
        if not file_name or file_name.startswith("."):
            raise ValueError("Please enter a valid file name.")

        return self.serialize(entry, file_format), file_name, FORMATS[file_format]
