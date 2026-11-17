"""Export the viewer's schedule filtered to one faculty member.

What this file does
-------------------
In the Schedule Viewer, a user can set "Filter By" to Faculty and pick a
person. When they then click Export, this file builds a download that
contains ONLY that person's classes, instead of the whole schedule.

How it fits into the app
------------------------
    schedule_viewer.py (the page / buttons)
        -> calls export_faculty_schedule() in this file
            -> filters the schedule's records to one faculty member
            -> hands them to schedule_export_strategy() (the team's existing
               CSV/JSON writer in src/models/schedule_files.py)
        <- returns the file bytes back to the viewer, which starts the download

Formats: CSV and JSON now. PDF will be added once the team's PDF export
(Sohil's feature) is ready -- search this file for "TODO" to see where.

Used by: GUI (src/views/schedule_viewer.py)."""

# File name: schedule_filtered_export_controller.py
# Primary author: Renee

import re
from pathlib import Path

# The team's existing CSV/JSON writer. We reuse it so a filtered export is in
# exactly the same format as a normal export (and can be loaded back in).
from src.models.schedule_files import schedule_export_strategy

# One schedule shown in the viewer. The parts we use here are:
#   entry.records     -> list of dicts, one per course section
#                        (keys include "course", "faculty", "room", "lab", "times")
#   entry.file_name   -> set if the schedule was loaded from a file, else None
#   entry.config_name -> name of the configuration the schedule came from
from src.models.schedule_viewer_model import ScheduleEntry

# File formats this export supports, mapped to the "media type" the browser
# needs in order to download the file correctly.
# TODO: add "pdf": "application/pdf" here once Sohil's PDF export is ready.
FILTERED_FORMATS = {
    "csv": "text/csv",
    "json": "application/json",
}


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


def filter_records_by_faculty(records: list[dict], faculty: str) -> list[dict]:
    """Keep only the course records taught by this faculty member.

    Note: there are two shapes of schedule data in this project.
      - "records" (used here): one dict per course section, the same shape
        that gets saved to CSV/JSON files.
      - "rows" (used by the table/calendar): one dict per meeting time, built
        by create_resource_schedule() in schedule_filters_controller.py.
    We filter the records, not the rows, so the exported file can be loaded
    back into the viewer with the Load button.
    """
    return [record for record in records if record.get("faculty") == faculty]


def default_faculty_file_name(entry: ScheduleEntry, faculty: str, file_format: str) -> str:
    """Suggest a file name for the export dialog.

    Uses the loaded file's name if there is one, otherwise the config name,
    then adds the faculty member's name.
    Example: 'fall_config_schedule1_Hobbes.csv'
    """
    base = Path(entry.file_name).stem if entry.file_name else entry.config_name
    return f"{_safe_name(base)}_{_safe_name(faculty)}.{file_format}"


# ---------------------------------------------------------
# Export (the function the viewer calls)
# ---------------------------------------------------------


def export_faculty_schedule(
    entry: ScheduleEntry | None,
    faculty: str | None,
    file_format: str,
    file_name: str,
) -> tuple[tuple[bytes, str, str] | None, str | None]:
    """Build a download of one faculty member's classes.

    Parameters:
        entry       -- the schedule currently selected in the viewer
                       (controller.current), or None if nothing is loaded
        faculty     -- the faculty member picked in the "Filter Value" dropdown
        file_format -- "csv" or "json" (from the export dialog)
        file_name   -- what the user typed in the export dialog (may be blank)

    Returns one of:
        ((file bytes, file name, media type), None)  -- success
        (None, "error message")                      -- something went wrong

    This is the same return shape as schedule_controller.export_current(),
    so the viewer's on_export() can handle both exports with the same code.
    We return error messages instead of raising so the viewer can just show
    the message in the dialog.
    """
    # --- Check the inputs first so the user gets a clear message ---
    if entry is None:
        return None, "There is no schedule to export."
    if not faculty:
        return None, "Please choose a faculty member."
    if file_format not in FILTERED_FORMATS:
        return None, "Please choose CSV or JSON."

    # --- Filter the schedule down to this faculty member ---
    records = filter_records_by_faculty(entry.records, faculty)
    if not records:
        return None, f"{faculty} has no classes in this schedule."

    # --- Clean up the file name ---
    # Use the user's name if they typed one, otherwise our suggested name.
    # Path(...).name strips any folders, so "../../x.csv" becomes "x.csv".
    file_name = Path(
        (file_name or "").strip() or default_faculty_file_name(entry, faculty, file_format)
    ).name
    # Make sure the extension matches the chosen format (e.g. add ".csv").
    if Path(file_name).suffix.lower() != f".{file_format}":
        file_name = f"{file_name}.{file_format}"
    # A name like ".csv" (no actual name) isn't valid.
    if file_name.startswith("."):
        return None, "Please enter a valid file name."

    # --- Turn the filtered records into file contents ---
    try:
        # TODO: when Sohil's PDF export is ready, add a branch like:
        #     if file_format == "pdf":
        #         content = build_schedule_pdf(records, f"Schedule for {faculty}")
        #     else:
        content = schedule_export_strategy(file_format).serialize(records)
    except (OSError, ValueError, KeyError) as error:
        return None, f"Could not export: {error}"

    return (content, file_name, FILTERED_FORMATS[file_format]), None
