"""Generate directly downloadable PDFs for schedule print layouts."""

import re
from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import ClassVar
from xml.sax.saxutils import escape

import reportlab
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from src.models.schedule_viewer_model import ScheduleEntry

ALL_GROUPS = "__all__"
PRINT_MEDIA_TYPE = "application/pdf"
DAY_ORDER = {"MON": 0, "TUE": 1, "WED": 2, "THU": 3, "FRI": 4}
MEETING_PATTERN = re.compile(r"^(MON|TUE|WED|THU|FRI) (\d{2}:\d{2})-(\d{2}:\d{2})(@online)?(\^)?$")

REPORTLAB_FONTS = Path(reportlab.__file__).parent / "fonts"
pdfmetrics.registerFont(TTFont("Vera", str(REPORTLAB_FONTS / "Vera.ttf")))
pdfmetrics.registerFont(
    TTFont("Vera-Bold", str(REPORTLAB_FONTS / "VeraBd.ttf"))
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


class PrintLayoutTemplate(ABC):
    """Template method for building a schedule print layout."""

    orientation: str

    @abstractmethod
    def group(self, meetings: list[PrintableMeeting]) -> dict[str, list[PrintableMeeting]]:
        """Group meetings and return them in the intended section order."""

    @abstractmethod
    def label(self, key: str) -> str:
        """Return the heading for a group key."""

    @abstractmethod
    def columns(self) -> tuple[str, ...]:
        """Return the table headings for this grouping."""

    @abstractmethod
    def row_values(self, meeting: PrintableMeeting) -> tuple[str, ...]:
        """Return cell values for one meeting."""

    def build(
        self,
        entry: ScheduleEntry,
        meetings: list[PrintableMeeting],
        group_key: str,
    ) -> bytes:
        """Run the common layout algorithm using subclass grouping details."""
        groups = self.group(meetings)
        if group_key == ALL_GROUPS:
            selected_groups = list(groups.items())
        elif group_key in groups:
            selected_groups = [(group_key, groups[group_key])]
        else:
            raise ValueError("Please choose a group available in the selected schedule.")

        buffer = BytesIO()
        document = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            leftMargin=0.55 * inch,
            rightMargin=0.55 * inch,
            topMargin=0.55 * inch,
            bottomMargin=0.55 * inch,
            title=f"Print schedule - {entry.label}",
        )
        title_style = ParagraphStyle(
            "ScheduleTitle",
            fontName="Vera-Bold",
            fontSize=19,
            leading=23,
            spaceAfter=4,
        )
        schedule_style = ParagraphStyle(
            "ScheduleName",
            fontName="Vera",
            fontSize=9,
            leading=12,
            spaceAfter=16,
        )
        group_style = ParagraphStyle(
            "GroupHeading",
            fontName="Vera-Bold",
            fontSize=12,
            leading=15,
        )
        column_style = ParagraphStyle(
            "ColumnHeading",
            fontName="Vera-Bold",
            fontSize=8,
            leading=10,
        )
        cell_style = ParagraphStyle(
            "TableCell",
            fontName="Vera",
            fontSize=8,
            leading=10,
        )
        story = [
            Paragraph(f"Schedule - {escape(self.orientation)} grouping", title_style),
            Paragraph(f"<b>Schedule:</b> {escape(entry.label)}", schedule_style),
        ]
        for index, (key, group_meetings) in enumerate(selected_groups):
            rows = sorted(
                group_meetings,
                key=lambda meeting: (
                    DAY_ORDER[meeting.day],
                    meeting.start,
                    meeting.end,
                    meeting.course.casefold(),
                ),
            )
            group_heading = f"{self.orientation} - {self.label(key)}"
            table_data = [
                [Paragraph(escape(group_heading), group_style), "", "", "", ""],
                [Paragraph(escape(column), column_style) for column in self.columns()],
            ]
            for meeting in rows:
                table_data.append(
                    [Paragraph(escape(value), cell_style) for value in self.row_values(meeting)]
                )
            table = Table(
                table_data,
                colWidths=(2.37 * inch, 1.92 * inch, 0.89 * inch, 1.11 * inch, 1.11 * inch),
                repeatRows=2,
            )
            table.setStyle(
                TableStyle(
                    [
                        ("SPAN", (0, 0), (-1, 0)),
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#dddddd")),
                        ("BACKGROUND", (0, 1), (-1, 1), colors.HexColor("#eeeeee")),
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#777777")),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("LEFTPADDING", (0, 0), (-1, -1), 6),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                        ("TOPPADDING", (0, 0), (-1, -1), 5),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                    ]
                )
            )
            story.append(table)
            if index < len(selected_groups) - 1:
                story.append(Spacer(1, 15))

        if not selected_groups:
            empty_style = ParagraphStyle(
                "EmptySchedule",
                fontName="Vera",
                fontSize=10,
                leading=14,
                borderColor=colors.HexColor("#777777"),
                borderWidth=0.5,
                borderPadding=12,
            )
            story.append(Paragraph("No meetings are available in this schedule.", empty_style))

        document.build(story)
        return buffer.getvalue()


class ResourcePrintLayoutTemplate(PrintLayoutTemplate):
    orientation = "Room and lab"
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

    def columns(self) -> tuple[str, ...]:
        return "Course / section", "Faculty", "Day", "Start", "End"

    def label(self, key: str) -> str:
        resource_type, name = key.split(":", 1)
        return f"{resource_type}: {name}"

    def row_values(self, meeting: PrintableMeeting) -> tuple[str, ...]:
        return meeting.course, meeting.faculty, meeting.day, meeting.start, meeting.end

    @staticmethod
    def _key(meeting: PrintableMeeting) -> str:
        return f"{meeting.resource_type}:{meeting.resource_name}"


class FacultyPrintLayoutTemplate(PrintLayoutTemplate):
    orientation = "Faculty"

    def group(self, meetings: list[PrintableMeeting]) -> dict[str, list[PrintableMeeting]]:
        groups: dict[str, list[PrintableMeeting]] = defaultdict(list)
        for meeting in meetings:
            groups[f"faculty:{meeting.faculty}"].append(meeting)
        return {key: groups[key] for key in sorted(groups, key=str.casefold)}

    def label(self, key: str) -> str:
        return key.removeprefix("faculty:")

    def columns(self) -> tuple[str, ...]:
        return "Course / section", "Room / lab", "Day", "Start", "End"

    def row_values(self, meeting: PrintableMeeting) -> tuple[str, ...]:
        resource = (
            meeting.resource_name
            if meeting.resource_type in {"Online", "Unassigned"}
            else f"{meeting.resource_type}: {meeting.resource_name}"
        )
        return meeting.course, resource, meeting.day, meeting.start, meeting.end


PRINT_LAYOUT_TEMPLATES: dict[str, type[PrintLayoutTemplate]] = {
    "resource": ResourcePrintLayoutTemplate,
    "faculty": FacultyPrintLayoutTemplate,
}


def print_group_options(entry: ScheduleEntry | None, orientation: str) -> dict[str, str]:
    """Return selectable groups for a schedule and print orientation."""
    template = _layout_template(orientation)
    if entry is None:
        return {ALL_GROUPS: "All groups"}
    groups = template.group(_parse_meetings(entry.records))
    all_label = (
        "All rooms, labs, and online/unassigned meetings"
        if orientation == "resource"
        else "All faculty"
    )
    return {ALL_GROUPS: all_label, **{key: template.label(key) for key in groups}}


def export_print_schedule(
    entry: ScheduleEntry | None,
    orientation: str,
    group_key: str,
) -> tuple[tuple[bytes, str, str] | None, str | None]:
    """Return a PDF schedule to download, or a user-readable error."""
    if entry is None:
        return None, "There is no schedule to export."
    try:
        template = _layout_template(orientation)
        meetings = _parse_meetings(entry.records)
        content = template.build(entry, meetings, group_key)
        base_name = _safe_name(Path(entry.file_name).stem if entry.file_name else entry.config_name)
        grouping = "rooms_labs" if orientation == "resource" else "faculty"
        suffix = "" if group_key == ALL_GROUPS else f"_{_safe_name(template.label(group_key))}"
        file_name = f"{base_name}_{grouping}{suffix}.pdf"
    except ValueError as error:
        return None, f"Could not prepare the PDF: {error}"
    return (content, file_name, PRINT_MEDIA_TYPE), None


def _layout_template(orientation: str) -> PrintLayoutTemplate:
    try:
        return PRINT_LAYOUT_TEMPLATES[orientation]()
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


def _safe_name(text: str) -> str:
    cleaned = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", text or "").strip(" .")
    return cleaned.replace(" ", "_") or "schedule"
