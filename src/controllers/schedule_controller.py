"""Coordinate the Schedule Viewer: navigation, loading, and exporting.

Used by: GUI."""

from src.controllers.schedule_filters_controller import create_resource_schedule
from src.controllers.schedule_generator_controller import (
    ScheduleGeneratorController,
    schedule_generator_controller,
)
from src.models.schedule_viewer_model import ScheduleEntry, ScheduleViewerModel


class ScheduleController:
    def __init__(
        self,
        model: ScheduleViewerModel | None = None,
        generator: ScheduleGeneratorController | None = None,
    ) -> None:
        self.model = model or ScheduleViewerModel()
        self.generator = generator or schedule_generator_controller

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------

    def sync_generated(self) -> bool:
        """Pull the generator's latest results. True if the viewer should redraw."""
        return self.model.set_generated(self.generator.generated_schedules)

    @property
    def has_schedules(self) -> bool:
        return bool(self.model.entries)

    @property
    def current(self) -> ScheduleEntry | None:
        return self.model.current

    @property
    def selected_index(self) -> int:
        return self.model.selected_index

    def schedule_options(self) -> dict[int, str]:
        return {index: entry.label for index, entry in enumerate(self.model.entries)}

    def select(self, index: int) -> None:
        self.model.select(index)

    def step(self, offset: int) -> None:
        self.model.select(self.model.selected_index + offset)

    def can_step(self, offset: int) -> bool:
        target = self.model.selected_index + offset
        return 0 <= target < len(self.model.entries)

    def current_rows(self) -> list[dict]:
        """The selected schedule as one row per meeting, in the viewer's table format."""
        entry = self.model.current
        if entry is None:
            return []
        rows = create_resource_schedule(entry.records)
        for row_id, row in enumerate(rows, start=1):
            row["id"] = row_id
        return rows

    # ------------------------------------------------------------------
    # Loading
    # ------------------------------------------------------------------

    def list_saved_files(self) -> list[str]:
        return self.model.list_saved_files()

    def load_saved_file(self, file_name: str | None) -> tuple[ScheduleEntry | None, str | None]:
        if not file_name:
            return None, "Please choose a schedule file."
        try:
            return self.model.load_saved_file(file_name), None
        except (OSError, ValueError) as error:
            return None, f"Could not load '{file_name}': {error}"

    def load_uploaded_file(self, file_name: str, content: bytes) -> tuple[ScheduleEntry | None, str | None]:
        try:
            return self.model.load_bytes(file_name, content), None
        except ValueError as error:
            return None, f"Could not load '{file_name}': {error}"

    # ------------------------------------------------------------------
    # Exporting
    # ------------------------------------------------------------------

    def default_export_file_name(self, file_format: str) -> str:
        entry = self.model.current
        return self.model.default_export_file_name(entry, file_format) if entry else ""

    def export_current(self, file_format: str, file_name: str) -> tuple[tuple[bytes, str, str] | None, str | None]:
        """(content, file name, media type) for a browser download."""
        entry = self.model.current
        if entry is None:
            return None, "There is no schedule to export."
        try:
            return self.model.export(entry, file_format, file_name), None
        except ValueError as error:
            return None, str(error)


schedule_controller = ScheduleController()
