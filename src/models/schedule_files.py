"""Schedule file format: convert generated schedules to records and back.

A *record* is one course section in the same shape as the CLI's CSV export:

    {"course": "CMSC 152.01", "faculty": "Hardy", "room": "Roddy 147",
     "lab": "Mac", "times": "MON 09:00-09:50,THU 09:00-10:50^,FRI 09:00-09:50"}

`times` uses the scheduler's own TimeSlot format: comma-separated meetings,
`^` marks the lab meeting, and `@online` marks an online meeting.
Records are what get saved, loaded, and turned into viewer rows.
"""

import csv
import io
import json
import re
from pathlib import Path

from src.models.schedule_result import ScheduleResult

RECORD_FIELDS = ("course", "faculty", "room", "lab", "times")

# "MON 09:00-09:50", optionally followed by "@online" and/or the "^" lab marker.
MEETING_PATTERN = re.compile(
    r"^(MON|TUE|WED|THU|FRI) \d{2}:\d{2}-\d{2}:\d{2}(@online)?\^?$"
)

# Older JSON exports wrote str(instance.times), a Python list repr like
# "[TimeInstance(day=TUE, start=TimePoint(timepoint=540), duration=Duration(duration=150), ...)]".
LEGACY_MEETING_PATTERN = re.compile(
    r"TimeInstance\(day=(\w+), start=TimePoint\(timepoint=(\d+)\), "
    r"duration=Duration\(duration=(\d+)\)(?:, delivery='(\w+)')?\)"
)

# "<config>_schedule<n>" (CLI) or "<config>_schedule_<n>" (generator download).
SAVED_NAME_PATTERN = re.compile(r"^(?P<config>.+?)_schedule_?(?P<number>\d+)$")


# ---------------------------------------------------------------------------
# Generated schedules -> records
# ---------------------------------------------------------------------------

def instance_times(instance) -> str:
    """The meeting string for one CourseInstance, e.g. 'MON 09:00-09:50,THU 09:00-10:50^'."""
    time_text = str(instance.time)
    if instance.lab is None:
        # The slot may carry a lab marker even when no lab was assigned.
        time_text = time_text.replace("^", "")
    return time_text


def records_from_result(result: ScheduleResult) -> list[dict[str, str]]:
    return [
        {
            "course": str(instance.course),
            "faculty": str(instance.faculty),
            "room": instance.room or "",
            "lab": instance.lab or "",
            "times": instance_times(instance),
        }
        for instance in result.schedule
    ]


# ---------------------------------------------------------------------------
# Records -> file contents
# ---------------------------------------------------------------------------

def records_to_csv(records: list[dict[str, str]], extra: dict[str, str] | None = None) -> bytes:
    """CSV with the CLI header. `extra` adds leading columns (e.g. schedule, config)."""
    extra = extra or {}
    output = io.StringIO(newline="")
    writer = csv.writer(output, lineterminator="\n")
    writer.writerow([*extra.keys(), *RECORD_FIELDS])
    for record in records:
        writer.writerow([*extra.values(), *(record[field] for field in RECORD_FIELDS)])
    return output.getvalue().encode("utf-8")


def records_to_json(records: list[dict[str, str]]) -> bytes:
    return json.dumps(records, indent=4).encode("utf-8")


# ---------------------------------------------------------------------------
# File contents -> records
# ---------------------------------------------------------------------------

def _clean(value: object) -> str:
    text = "" if value is None else str(value).strip()
    return "" if text in {"None", "null"} else text


def _clock(minutes: int) -> str:
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


def _normalize_times(text: str) -> str:
    """Convert the legacy list-repr format to the standard meeting string.

    The legacy format has no lab marker, so lab meetings in those files show
    the lecture room. Re-save them from the viewer to get the standard format.
    """
    if "TimeInstance(" not in text:
        return text
    meetings = []
    for day, start, duration, delivery in LEGACY_MEETING_PATTERN.findall(text):
        start_minutes = int(start)
        stop_minutes = start_minutes + int(duration)
        suffix = "@online" if delivery == "online" else ""
        meetings.append(f"{day} {_clock(start_minutes)}-{_clock(stop_minutes)}{suffix}")
    return ",".join(meetings)


def _normalize_record(raw: dict) -> dict[str, str]:
    record = {field: _clean(raw.get(field)) for field in RECORD_FIELDS}
    record["times"] = _normalize_times(record["times"])
    return record


def config_name_from_file_name(file_name: str) -> str:
    stem = Path(file_name).stem
    match = SAVED_NAME_PATTERN.match(stem)
    return match.group("config") if match else stem


def parse_schedule_file(file_name: str, content: bytes) -> tuple[str, list[dict[str, str]]]:
    """Parse a saved CSV or JSON schedule. Returns (config_name, records).

    Accepts the CLI export format, the generator's download format
    (JSON wrapped as {"schedule", "config", "meetings"}; CSV with extra
    schedule/config columns), and legacy list-repr times.
    Raises ValueError with a user-readable message if the file can't be used.
    """
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError as error:
        raise ValueError("The file is not UTF-8 text.") from error

    suffix = Path(file_name).suffix.lower()
    config_name: str | None = None

    if suffix == ".json":
        try:
            data = json.loads(text)
        except json.JSONDecodeError as error:
            raise ValueError(f"Invalid JSON: {error.msg} (line {error.lineno}).") from error
        if isinstance(data, dict):
            config_name = _clean(data.get("config")) or None
            raw_records = data.get("meetings")
        else:
            raw_records = data
        if not isinstance(raw_records, list):
            raise ValueError("Expected a list of course sections in the JSON file.")

    elif suffix == ".csv":
        reader = csv.DictReader(io.StringIO(text))
        missing = [field for field in RECORD_FIELDS if field not in (reader.fieldnames or [])]
        if missing:
            raise ValueError(f"The CSV file is missing column(s): {', '.join(missing)}.")
        raw_records = list(reader)
        if raw_records and _clean(raw_records[0].get("config")):
            config_name = _clean(raw_records[0]["config"])

    else:
        raise ValueError("Only .csv and .json schedule files can be loaded.")

    records = [_normalize_record(raw) for raw in raw_records if isinstance(raw, dict)]
    records = [record for record in records if record["course"]]
    if not records:
        raise ValueError("The file does not contain any course sections.")

    for record in records:
        for meeting in record["times"].split(","):
            if not MEETING_PATTERN.match(meeting.strip()):
                raise ValueError(
                    f"Unrecognized meeting time '{meeting.strip()}' for {record['course']}."
                )

    return config_name or config_name_from_file_name(file_name), records
