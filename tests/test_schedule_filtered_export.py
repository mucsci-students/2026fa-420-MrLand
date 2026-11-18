"""Unit tests for schedule_filtered_export_controller.py.

When the viewer is filtered by a faculty member or a room/lab, the
Print / Export PDF dialog should open on that person or room.
These test print_defaults_for_filter(), which picks those starting choices.

These test the controller logic only, not the NiceGUI page, so no browser or
running app is needed.

Run with:  uv run pytest tests/test_schedule_filtered_export.py -v
"""

# File name: test_schedule_filtered_export.py
# Primary author: Renee

import pytest

from src.controllers.schedule_filtered_export_controller import (
    DEFAULT_PRINT_CHOICES,
    print_defaults_for_filter,
)
from src.controllers.schedule_print_export_controller import (
    ALL_GROUPS,
    export_print_schedule,
    print_group_options,
)
from src.models.schedule_viewer_model import ScheduleEntry

# ---------------------------------------------------------
# Sample data
# ---------------------------------------------------------
# Course records in the same shape the viewer stores in entry.records
# (one dict per course section). "^" marks a lab meeting.
#   Roddy 136 -> CMSC 140 lectures and CMSC 330
#   Roddy 140 -> CMSC 161
#   Roddy 147 -> CMSC 140's THU lab meeting
#   Online    -> CMSC 499
SAMPLE_RECORDS = [
    {
        "course": "CMSC 140-01",
        "faculty": "Hobbes",
        "room": "Roddy 136",
        "lab": "Roddy 147",
        "times": "MON 09:00-09:50,WED 09:00-09:50,THU 14:00-15:50^",
    },
    {
        "course": "CMSC 161-01",
        "faculty": "Hobbes",
        "room": "Roddy 140",
        "lab": "",
        "times": "TUE 13:00-14:15,THU 13:00-14:15",
    },
    {
        "course": "CMSC 330-01",
        "faculty": "Dr. Jones",
        "room": "Roddy 136",
        "lab": "",
        "times": "MON 10:00-10:50,WED 10:00-10:50,FRI 10:00-10:50",
    },
    {
        "course": "CMSC 499-01",
        "faculty": "Dr. Jones",
        "room": "",
        "lab": "",
        "times": "TUE 18:00-19:15@online",
    },
]


@pytest.fixture
def entry() -> ScheduleEntry:
    return ScheduleEntry(
        label="fall_config — schedule 1 (generated)",
        config_name="fall_config",
        source="generated",
        records=[record.copy() for record in SAMPLE_RECORDS],
    )


# ---------------------------------------------------------
# Viewer filtered by faculty
# ---------------------------------------------------------


@pytest.mark.parametrize("faculty", ["Hobbes", "Dr. Jones"])
def test_faculty_filter_opens_on_that_faculty_member(entry, faculty):
    assert print_defaults_for_filter(entry, "Faculty", faculty) == (
        "faculty",
        f"faculty:{faculty}",
    )


def test_faculty_unknown_name_shows_all_faculty(entry):
    assert print_defaults_for_filter(entry, "Faculty", "Nobody") == ("faculty", ALL_GROUPS)


# ---------------------------------------------------------
# Viewer filtered by room / lab
# ---------------------------------------------------------


@pytest.mark.parametrize(
    ("room", "expected_key"),
    [
        ("Roddy 136", "Room:Roddy 136"),
        ("Roddy 140", "Room:Roddy 140"),
        ("Roddy 147", "Lab:Roddy 147"),  # only used as a lab
        ("Online", "Online:Online"),
    ],
)
def test_room_filter_opens_on_that_room_or_lab(entry, room, expected_key):
    assert print_defaults_for_filter(entry, "Room / Lab", room) == ("resource", expected_key)


def test_room_unknown_name_shows_all_rooms(entry):
    assert print_defaults_for_filter(entry, "Room / Lab", "Nowhere 101") == (
        "resource",
        ALL_GROUPS,
    )


# ---------------------------------------------------------
# Not filtering (or filtering by something the PDF can't group by)
# ---------------------------------------------------------


@pytest.mark.parametrize(
    ("filter_type", "filter_value"),
    [
        ("None", None),
        ("Course", "CMSC 140-01"),  # the PDF can't group by course
        ("Faculty", None),  # filter type picked but no value yet
        ("Room / Lab", ""),
    ],
)
def test_no_usable_filter_keeps_normal_default(entry, filter_type, filter_value):
    assert print_defaults_for_filter(entry, filter_type, filter_value) == DEFAULT_PRINT_CHOICES


def test_no_schedule_keeps_normal_default():
    assert print_defaults_for_filter(None, "Faculty", "Hobbes") == DEFAULT_PRINT_CHOICES


def test_unreadable_schedule_keeps_normal_default():
    bad_entry = ScheduleEntry(
        label="bad",
        config_name="bad",
        source="file",
        records=[{"course": "X", "faculty": "Hobbes", "room": "", "lab": "", "times": "nope"}],
    )

    assert print_defaults_for_filter(bad_entry, "Faculty", "Hobbes") == DEFAULT_PRINT_CHOICES


def test_default_is_what_the_dialog_used_before():
    assert DEFAULT_PRINT_CHOICES == ("resource", ALL_GROUPS)


# ---------------------------------------------------------
# The chosen defaults work with Sohil's dialog and export
# ---------------------------------------------------------


@pytest.mark.parametrize(
    ("filter_type", "filter_value"),
    [
        ("Faculty", "Hobbes"),
        ("Room / Lab", "Roddy 136"),
        ("Room / Lab", "Roddy 147"),
        ("None", None),
    ],
)
def test_defaults_are_choices_in_the_dialog(entry, filter_type, filter_value):
    group_by, group_key = print_defaults_for_filter(entry, filter_type, filter_value)

    assert group_key in print_group_options(entry, group_by)


def test_faculty_default_prints_only_that_faculty_member(entry):
    group_by, group_key = print_defaults_for_filter(entry, "Faculty", "Hobbes")

    export, error = export_print_schedule(entry, group_by, group_key)

    assert error is None
    assert export is not None
    text = export[0].decode("utf-8")
    assert "CMSC 140-01" in text
    assert "CMSC 161-01" in text
    assert "CMSC 330-01" not in text  # Dr. Jones's class


def test_room_default_prints_only_that_room(entry):
    group_by, group_key = print_defaults_for_filter(entry, "Room / Lab", "Roddy 136")

    export, error = export_print_schedule(entry, group_by, group_key)

    assert error is None
    assert export is not None
    text = export[0].decode("utf-8")
    assert "CMSC 140-01" in text
    assert "CMSC 330-01" in text
    assert "CMSC 161-01" not in text  # meets in Roddy 140
