"""Build print-ready schedule layouts for the browser's Save as PDF workflow."""

import html
import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import ClassVar, Protocol

from src.models.schedule_viewer_model import ScheduleEntry

ALL_GROUPS = "__all__"
PRINT_MEDIA_TYPE = "text/html"
DAY_ORDER = {"MON": 0, "TUE": 1, "WED": 2, "THU": 3, "FRI": 4}
MEETING_PATTERN = re.compile(
    r"^(MON|TUE|WED|THU|FRI) (\d{2}:\d{2})-(\d{2}:\d{2})(@online)?(\^)?$"
)


@dataclass(frozen=True)
class PrintableMeeting:
    course: str
    faculty: str
    resource_type: str
    resource_name: str
    day: str
    start: str
    end: str


class PrintGroupingStrategy(Protocol):
    orientation: str
    columns: tuple[str, ...]

    def group(self, meetings: list[PrintableMeeting]) -> dict[str, list[PrintableMeeting]]: ...

    def label(self, key: str) -> str: ...

    def values(self, meeting: PrintableMeeting) -> tuple[str, ...]: ...


class ResourcePrintStrategy:
    orientation = "Room and lab"
    columns = ("Course / section", "Faculty", "Day", "Start", "End")
    _resource_order: ClassVar[dict[str, int]] = {
        "Room": 0,
        "Lab": 1,
        "Online": 2,
        "Unassigned": 3,
    }

    def group(self, meetings: list[PrintableMeeting]) -> dict[str, list[PrintableMeeting]]:
        groups: dict[str, list[PrintableMeeting]] = defaultdict(list)
        for meeting in meetings:
            groups[self._key(meeting)].append(meeting)
        return {
            key: groups[key]
            for key in sorted(
                groups,
                key=lambda group_key: (
                    self._resource_order[group_key.split(":", 1)[0]],
                    group_key.split(":", 1)[1].casefold(),
                ),
            )
        }

    def label(self, key: str) -> str:
        resource_type, name = key.split(":", 1)
        return f"{resource_type}: {name}"

    def values(self, meeting: PrintableMeeting) -> tuple[str, ...]:
        return meeting.course, meeting.faculty, meeting.day, meeting.start, meeting.end

    @staticmethod
    def _key(meeting: PrintableMeeting) -> str:
        return f"{meeting.resource_type}:{meeting.resource_name}"


class FacultyPrintStrategy:
    orientation = "Faculty"
    columns = ("Course / section", "Room / lab", "Day", "Start", "End")

    def group(self, meetings: list[PrintableMeeting]) -> dict[str, list[PrintableMeeting]]:
        groups: dict[str, list[PrintableMeeting]] = defaultdict(list)
        for meeting in meetings:
            groups[f"faculty:{meeting.faculty}"].append(meeting)
        return {key: groups[key] for key in sorted(groups, key=str.casefold)}

    def label(self, key: str) -> str:
        return key.removeprefix("faculty:")

    def values(self, meeting: PrintableMeeting) -> tuple[str, ...]:
        resource = (
            meeting.resource_name
            if meeting.resource_type in {"Online", "Unassigned"}
            else f"{meeting.resource_type}: {meeting.resource_name}"
        )
        return meeting.course, resource, meeting.day, meeting.start, meeting.end


PRINT_STRATEGIES: dict[str, PrintGroupingStrategy] = {
    "resource": ResourcePrintStrategy(),
    "faculty": FacultyPrintStrategy(),
}


def print_group_options(
    entry: ScheduleEntry | None, orientation: str
) -> dict[str, str]:
    """Return selectable groups for a schedule and print orientation."""
    strategy = _strategy(orientation)
    if entry is None:
        return {ALL_GROUPS: "All groups"}
    groups = strategy.group(_parse_meetings(entry.records))
    all_label = (
        "All rooms, labs, and online/unassigned meetings"
        if orientation == "resource"
        else "All faculty"
    )
    return {ALL_GROUPS: all_label, **{key: strategy.label(key) for key in groups}}


def export_print_schedule(
    entry: ScheduleEntry | None,
    orientation: str,
    group_key: str,
) -> tuple[tuple[bytes, str, str] | None, str | None]:
    """Return an HTML print layout to download, or a user-readable error."""
    if entry is None:
        return None, "There is no schedule to export."
    try:
        strategy = _strategy(orientation)
        meetings = _parse_meetings(entry.records)
        groups = strategy.group(meetings)
        if group_key == ALL_GROUPS:
            selected_groups = list(groups.items())
        elif group_key in groups:
            selected_groups = [(group_key, groups[group_key])]
        else:
            return None, "Please choose a group available in the selected schedule."

        content = _build_print_layout(entry, strategy, selected_groups)
        base_name = _safe_name(Path(entry.file_name).stem if entry.file_name else entry.config_name)
        grouping = "rooms_labs" if orientation == "resource" else "faculty"
        suffix = "" if group_key == ALL_GROUPS else f"_{_safe_name(strategy.label(group_key))}"
        file_name = f"{base_name}_{grouping}{suffix}_print.html"
    except ValueError as error:
        return None, f"Could not prepare the print layout: {error}"
    return (content.encode("utf-8"), file_name, PRINT_MEDIA_TYPE), None


def _strategy(orientation: str) -> PrintGroupingStrategy:
    try:
        return PRINT_STRATEGIES[orientation]
    except KeyError as error:
        raise ValueError("Choose room/lab or faculty grouping.") from error


def _parse_meetings(records: list[dict[str, str]]) -> list[PrintableMeeting]:
    meetings = []
    for record in records:
        for raw_meeting in record.get("times", "").split(","):
            raw_meeting = raw_meeting.strip()
            if not raw_meeting:
                continue
            match = MEETING_PATTERN.fullmatch(raw_meeting)
            if match is None:
                raise ValueError(f"Unrecognized meeting time '{raw_meeting}'.")
            day, start, end, online_marker, lab_marker = match.groups()
            if online_marker:
                resource_type, resource_name = "Online", "Online"
            elif lab_marker and record.get("lab", "").strip():
                resource_type, resource_name = "Lab", record["lab"].strip()
            elif not lab_marker and record.get("room", "").strip():
                resource_type, resource_name = "Room", record["room"].strip()
            else:
                resource_type, resource_name = "Unassigned", "Unassigned"
            meetings.append(
                PrintableMeeting(
                    course=record.get("course", "").strip(),
                    faculty=record.get("faculty", "").strip() or "Unassigned",
                    resource_type=resource_type,
                    resource_name=resource_name,
                    day=day,
                    start=start,
                    end=end,
                )
            )
    return meetings


def _build_print_layout(
    entry: ScheduleEntry,
    strategy: PrintGroupingStrategy,
    groups: list[tuple[str, list[PrintableMeeting]]],
) -> str:
    schedule_label = html.escape(entry.label)
    sections = []
    for key, meetings in groups:
        group_label = strategy.label(key)
        rows = sorted(
            meetings,
            key=lambda meeting: (
                DAY_ORDER[meeting.day],
                meeting.start,
                meeting.end,
                meeting.course.casefold(),
            ),
        )
        first_heading = html.escape(f"{strategy.orientation} — {group_label}")
        headings = "".join(
            f"<th scope='col'>{html.escape(column)}</th>" for column in strategy.columns
        )
        row_html = []
        for meeting in rows:
            cells = "".join(
                f"<td>{html.escape(value)}</td>" for value in strategy.values(meeting)
            )
            row_html.append(f"<tr>{cells}</tr>")
        sections.append(
            "<section><table><thead>"
            f"<tr><th class='group-heading' colspan='5'>{first_heading}</th></tr>"
            f"<tr>{headings}</tr></thead><tbody>{''.join(row_html)}</tbody></table></section>"
        )

    body = "".join(sections)
    if not groups:
        body = "<p class='empty'>No meetings are available in this schedule.</p>"
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Print schedule — {schedule_label}</title>
<style>
    @page {{ size: Letter portrait; margin: 0.55in; }}
    * {{ box-sizing: border-box; }}
    body {{ color: #111; background: #fff; font: 10pt/1.35 Arial, sans-serif; }}
    h1 {{ font-size: 19pt; margin: 0 0 4pt; }}
    .schedule-name {{ margin: 0 0 16pt; overflow-wrap: anywhere; }}
    .instructions {{ padding: 10px 12px; border: 1px solid #777; margin-bottom: 18px; }}
    section {{ margin: 0 0 15pt; }}
    table {{ width: 100%; border-collapse: collapse; table-layout: fixed; }}
    th, td {{ border: 1px solid #777; padding: 5px 6px; text-align: left;
        vertical-align: top; overflow-wrap: anywhere; }}
    thead {{ display: table-header-group; }}
    th {{ background: #eee; color: #111; }}
    .group-heading {{ background: #ddd; font-size: 12pt; }}
    tr {{ break-inside: avoid; page-break-inside: avoid; }}
    section {{ break-inside: auto; }}
    .empty {{ border: 1px solid #777; padding: 12px; }}
    @media print {{
        .instructions {{ display: none; }}
        body {{ margin: 0; }}
    }}
</style>
</head>
<body>
<h1>Schedule — {html.escape(strategy.orientation)} grouping</h1>
<p class="schedule-name"><strong>Schedule:</strong> {schedule_label}</p>
<p class="instructions">To create a PDF, open the browser's Print dialog (Ctrl+P or
use the browser menu), choose <strong>Save as PDF</strong>, and select the destination.
Paper size: Letter.</p>
{body}
</body>
</html>"""


def _safe_name(text: str) -> str:
    cleaned = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", text or "").strip(" .")
    return cleaned.replace(" ", "_") or "schedule"
