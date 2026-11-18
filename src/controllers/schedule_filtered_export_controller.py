"""Pick the Print / Export PDF dialog's starting choices from the viewer's filter.

What this file does
-------------------
The Schedule Viewer has a "Filter By" dropdown (None / Course / Faculty /
Room / Lab) and a "Filter Value" dropdown. Sohil's "Print / Export PDF"
dialog has its own "Group by" (Room / lab or Faculty) and "Resource or
faculty" dropdowns.

If the user is already filtering the viewer by a faculty member or a
room/lab, this file works out the matching choices so the PDF dialog opens
on that person or room. The user can still change them in the dialog.

    Viewer filter                  ->  PDF dialog opens on
    ---------------------------------------------------------------
    Faculty: Hobbes                ->  Group by Faculty, "Hobbes"
    Room / Lab: Roddy 136          ->  Group by Room / lab, "Room: Roddy 136"
    Room / Lab: Roddy 147 (a lab)  ->  Group by Room / lab, "Lab: Roddy 147"
    None or Course                 ->  Group by Room / lab, "All ..."  (same as before)

Export by faculty / Export by room or lab user stories.
The PDF itself is built by Sohil's schedule_print_export_controller.py.

Used by: GUI (src/views/schedule_viewer.py, open_print_export_dialog)."""

# File name: schedule_filtered_export_controller.py
# Primary author: Renee

# From Sohil's print layout:
#   ALL_GROUPS          -> the "All rooms/labs" or "All faculty" choice
#   print_group_options -> the choices in the "Resource or faculty" dropdown,
#                          as {group key: label}. Group keys look like
#                          "faculty:Hobbes", "Room:Roddy 136", "Lab:Roddy 147",
#                          "Online:Online", or "Unassigned:Unassigned".
from src.controllers.schedule_print_export_controller import (
    ALL_GROUPS,
    print_group_options,
)

# One schedule shown in the viewer (controller.current).
from src.models.schedule_viewer_model import ScheduleEntry

# What the PDF dialog shows when the viewer isn't filtered by faculty or
# room/lab. This matches what Sohil's dialog did before this feature.
DEFAULT_PRINT_CHOICES = ("resource", ALL_GROUPS)


def print_defaults_for_filter(
    entry: ScheduleEntry | None,
    filter_type: str | None,
    filter_value: str | None,
) -> tuple[str, str]:
    """Return (group by, group key) for the PDF dialog to start on.

    Parameters:
        entry        -- the schedule currently selected in the viewer
        filter_type  -- the viewer's "Filter By" value: "None", "Course",
                        "Faculty", or "Room / Lab"
        filter_value -- the viewer's "Filter Value" value, e.g. "Hobbes" or
                        "Roddy 136" (None if nothing is picked)

    Returns:
        group by  -- "faculty" or "resource" (the "Group by" dropdown's value)
        group key -- a key from print_group_options(), or ALL_GROUPS

    Always returns choices that exist in the dialog, so the viewer can set
    them without checking. If anything doesn't match, it falls back to the
    dialog's normal default.
    """
    if entry is None or not filter_value:
        return DEFAULT_PRINT_CHOICES

    if filter_type == "Faculty":
        group_by = "faculty"
    elif filter_type == "Room / Lab":
        group_by = "resource"
    else:
        # Not filtering, or filtering by Course (the PDF can't group by course)
        return DEFAULT_PRINT_CHOICES

    try:
        options = print_group_options(entry, group_by)
    except ValueError:
        # Sohil's code couldn't read this schedule; let his dialog show the error
        return DEFAULT_PRINT_CHOICES

    group_key = _find_group_key(options, group_by, filter_value)
    if group_key is None:
        # e.g. the filter value isn't in this schedule; still open on the
        # right "Group by", showing everyone
        return group_by, ALL_GROUPS
    return group_by, group_key


def _find_group_key(options: dict[str, str], group_by: str, filter_value: str) -> str | None:
    """Find the dialog's group key for the viewer's filter value.

    Faculty keys are simply "faculty:<name>".
    Room/lab keys are "<type>:<name>" (e.g. "Room:Roddy 136"), but the viewer's
    dropdown only has the name ("Roddy 136"), so we look for the key whose
    name part matches.
    """
    if group_by == "faculty":
        key = f"faculty:{filter_value}"
        return key if key in options else None

    for key in options:
        if key != ALL_GROUPS and key.split(":", 1)[-1] == filter_value:
            return key
    return None
