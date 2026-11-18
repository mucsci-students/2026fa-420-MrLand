"""Export the viewer's schedule filtered to one faculty member or one room/lab.

What this file does
-------------------
In the Schedule Viewer, a user can set "Filter By" to Faculty (or Room / Lab)
and pick a person (or a room/lab). When they then click Export, this file
builds a download that contains ONLY that person's (or room's) classes,
instead of the whole schedule.

How it fits into the app
------------------------
    schedule_viewer.py (the page / buttons)
        -> calls export_faculty_schedule() or export_room_schedule() in this file
            -> both call _export_filtered(), which:
               -> filters the schedule's records
               -> CSV/JSON: hands them to schedule_export_strategy() (the team's
                  existing CSV/JSON writer in src/models/schedule_files.py)
               -> PDF: asks Sohil's print layout for just that one group
        <- returns the file bytes back to the viewer, which starts the download

Formats: CSV, JSON, and PDF.
  - CSV/JSON reuse the team's normal file writer, so the file can be loaded
    back into the viewer.
  - "PDF" reuses Sohil's print layout (schedule_print_export_controller.py).
    That feature downloads a print-ready .html page; the user opens it in a
    browser and chooses Print > Save as PDF. We just ask it for one faculty
    member's (or one room's) section instead of everyone.

Room/lab note
-------------
A course record has both a "room" and a "lab". For CSV/JSON we keep the whole
course record if ANY of its meetings happen in the chosen room/lab (so the
file still loads back into the viewer). The PDF lists only the meetings that
actually happen in that room/lab, which is what a door sign needs.

Used by: GUI (src/views/schedule_viewer.py)."""

# File name: schedule_filtered_export_controller.py
# Primary author: Renee

import re
from pathlib import Path

# The same function the viewer's table uses to work out which room/lab each
# meeting is in. Reusing it keeps the room/lab export matching the screen.
from src.controllers.schedule_filters_controller import create_resource_schedule

# Sohil's print layout (the "PDF" option). We pass it a group key like
# "faculty:Hobbes" or "Room:Roddy 136" so it only builds that one section.
from src.controllers.schedule_print_export_controller import (
    PRINT_MEDIA_TYPE,
    export_print_schedule,
    print_group_options,
)

# The team's existing CSV/JSON writer. We reuse it so a filtered export is in
# exactly the same format as a normal export (and can be loaded back in).
from src.models.schedule_files import schedule_export_strategy

# One schedule shown in the viewer. The parts we use here are:
#   entry.records     -> list of dicts, one per course section
#                        (keys: "course", "faculty", "room", "lab", "times")
#   entry.file_name   -> set if the schedule was loaded from a file, else None
#   entry.config_name -> name of the configuration the schedule came from
from src.models.schedule_viewer_model import ScheduleEntry

# File formats this export supports, mapped to the "media type" the browser
# needs in order to download the file correctly.
# "pdf" is really an HTML print layout (see the note at the top of the file),
# so it uses Sohil's media type, "text/html".
FILTERED_FORMATS = {
    "csv": "text/csv",
    "json": "application/json",
    "pdf": PRINT_MEDIA_TYPE,
}

# Return type shared by the export functions:
#   ((file bytes, file name, media type), None)  -- success
#   (None, "error message")                      -- something went wrong
ExportResult = tuple[tuple[bytes, str, str] | None, str | None]


# ---------------------------------------------------------
# Helpers
# ---------------------------------------------------------


def _safe_name(text: str) -> str:
    """Make text safe to use inside a file name.

    Replaces characters Windows/macOS don't allow in file names
    (like / \\ : * ? " < > |) with "_", and spaces with "_".
    Example: 'Dr. Smith / Jones' -> 'Dr._Smith___Jones'
    Falls back to "schedule" if nothing is left.
    """
    cleaned = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", text or "").strip(" .")
    return cleaned.replace(" ", "_") or "schedule"


def export_extension(file_format: str) -> str:
    """The file extension for a format.

    "pdf" downloads as a .html print layout, so its extension is "html".
    Everything else uses its own name ("csv" -> "csv").
    The viewer also uses this to keep the file name box in sync.
    """
    return "html" if file_format == "pdf" else file_format


def default_filtered_file_name(entry: ScheduleEntry, filter_value: str, file_format: str) -> str:
    """Suggest a file name for the export dialog.

    Uses the loaded file's name if there is one, otherwise the config name,
    then adds the faculty member's or room's name.
    Examples: 'fall_config_schedule1_Hobbes.csv'
              'fall_config_schedule1_Roddy_136_print.html' (the PDF option)
    """
    base = Path(entry.file_name).stem if entry.file_name else entry.config_name
    name = f"{_safe_name(base)}_{_safe_name(filter_value)}"
    if file_format == "pdf":
        name += "_print"
    return f"{name}.{export_extension(file_format)}"


# The faculty export was written first; keep its name working for the viewer/tests.
default_faculty_file_name = default_filtered_file_name


# ---------------------------------------------------------
# Filtering
# ---------------------------------------------------------
# Note: there are two shapes of schedule data in this project.
#   - "records" (filtered here): one dict per course section, the same shape
#     that gets saved to CSV/JSON files.
#   - "rows" (used by the table/calendar): one dict per meeting time, built
#     by create_resource_schedule() in schedule_filters_controller.py.
# We filter records, not rows, so the exported file can be loaded back into
# the viewer with the Load button.


def filter_records_by_faculty(records: list[dict], faculty: str) -> list[dict]:
    """Keep only the course records taught by this faculty member."""
    return [record for record in records if record.get("faculty") == faculty]


def filter_records_by_resource(records: list[dict], resource: str) -> list[dict]:
    """Keep the course records that have at least one meeting in this room/lab.

    `resource` is the value from the viewer's "Room / Lab" dropdown, e.g.
    "Roddy 136", "Online", or "Unassigned". We work out where each meeting
    happens with create_resource_schedule() -- the same function the viewer's
    table uses -- so the export always matches what the user sees on screen.
    """
    return [
        record
        for record in records
        if any(row["resource"] == resource for row in create_resource_schedule([record]))
    ]


def _print_group_key(entry: ScheduleEntry, filter_type: str, value: str) -> str | None:
    """Turn the viewer's filter value into the group key Sohil's print layout uses.

    Faculty groups are keyed "faculty:<name>".
    Room/lab groups are keyed "<type>:<name>", e.g. "Room:Roddy 136",
    "Lab:Roddy 147", "Online:Online", or "Unassigned:Unassigned". The viewer's
    dropdown only has the name, so we look up which key has that name.
    Returns None if the schedule has no matching group.
    """
    if filter_type == "faculty":
        return f"faculty:{value}"

    for key in print_group_options(entry, "resource"):
        if ":" in key and key.split(":", 1)[1] == value:
            return key
    return None


# ---------------------------------------------------------
# Export (the functions the viewer calls)
# ---------------------------------------------------------


def export_faculty_schedule(
    entry: ScheduleEntry | None,
    faculty: str | None,
    file_format: str,
    file_name: str,
) -> ExportResult:
    """Build a download of one faculty member's classes.

    Parameters:
        entry       -- the schedule currently selected in the viewer
                       (controller.current), or None if nothing is loaded
        faculty     -- the faculty member picked in the "Filter Value" dropdown
        file_format -- "csv", "json", or "pdf" (from the export dialog)
        file_name   -- what the user typed in the export dialog (may be blank)
    """
    return _export_filtered(entry, "faculty", faculty, file_format, file_name)


def export_room_schedule(
    entry: ScheduleEntry | None,
    room: str | None,
    file_format: str,
    file_name: str,
) -> ExportResult:
    """Build a download of the classes that meet in one room or lab.

    Same parameters as export_faculty_schedule(), except `room` is the room/lab
    picked in the "Filter Value" dropdown (e.g. "Roddy 136" or "Online").
    """
    return _export_filtered(entry, "resource", room, file_format, file_name)


def _export_filtered(
    entry: ScheduleEntry | None,
    filter_type: str,
    filter_value: str | None,
    file_format: str,
    file_name: str,
) -> ExportResult:
    """Shared steps for faculty and room/lab exports.

    filter_type is "faculty" or "resource" (room/lab).

    Returns the same shape as schedule_controller.export_current(), so the
    viewer's on_export() can handle every export with the same code.
    We return error messages instead of raising so the viewer can just show
    the message in the dialog.
    """
    what = "faculty member" if filter_type == "faculty" else "room or lab"

    # --- Check the inputs first so the user gets a clear message ---
    if entry is None:
        return None, "There is no schedule to export."
    if not filter_value:
        return None, f"Please choose a {what}."
    if file_format not in FILTERED_FORMATS:
        return None, "Please choose CSV, JSON, or PDF."

    # --- Filter the schedule down to this faculty member or room/lab ---
    if filter_type == "faculty":
        records = filter_records_by_faculty(entry.records, filter_value)
    else:
        records = filter_records_by_resource(entry.records, filter_value)
    if not records:
        return None, f"{filter_value} has no classes in this schedule."

    # --- Clean up the file name ---
    # Use the user's name if they typed one, otherwise our suggested name.
    # Path(...).name strips any folders, so "../../x.csv" becomes "x.csv".
    file_name = Path(
        (file_name or "").strip() or default_filtered_file_name(entry, filter_value, file_format)
    ).name
    # Make sure the extension matches the chosen format (e.g. add ".csv").
    extension = export_extension(file_format)
    if Path(file_name).suffix.lower() != f".{extension}":
        file_name = f"{file_name}.{extension}"
    # A name like ".csv" (no actual name) isn't valid.
    if file_name.startswith("."):
        return None, "Please enter a valid file name."

    # --- Turn the filtered records into file contents ---
    if file_format == "pdf":
        # Ask Sohil's print layout for just this one group. We only keep the
        # content; the file name is the one chosen in our dialog.
        try:
            group_key = _print_group_key(entry, filter_type, filter_value)
        except ValueError as error:
            return None, f"Could not prepare the print layout: {error}"
        if group_key is None:
            return None, f"{filter_value} has no classes in this schedule."
        orientation = "faculty" if filter_type == "faculty" else "resource"
        print_export, error = export_print_schedule(entry, orientation, group_key)
        if error or print_export is None:
            return None, error or "Could not prepare the print layout."
        content = print_export[0]
    else:
        try:
            content = schedule_export_strategy(file_format).serialize(records)
        except (OSError, ValueError, KeyError) as error:
            return None, f"Could not export: {error}"

    return (content, file_name, FILTERED_FORMATS[file_format]), None
