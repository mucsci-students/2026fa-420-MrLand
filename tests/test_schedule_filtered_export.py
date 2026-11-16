"""Unit tests for export by faculty (schedule_filtered_export_controller.py).

These test the controller logic only (filtering, file names, errors), not the
NiceGUI page, so no browser or running app is needed.

Run with:  uv run pytest tests/test_schedule_filtered_export.py -v
"""

# File name: test_schedule_filtered_export.py
# Primary author: Renee

import json

import pytest

from src.controllers.schedule_filtered_export_controller import (
    FILTERED_FORMATS,
    _safe_name,
    default_faculty_file_name,
    export_faculty_schedule,
    filter_records_by_faculty,
)
from src.models.schedule_files import parse_schedule_file
from src.models.schedule_viewer_model import ScheduleEntry

# ---------------------------------------------------------
# Sample data
# ---------------------------------------------------------
# Course records in the same shape the viewer stores in entry.records
# (one dict per course section). "^" marks a lab meeting.
# NOTE: if the team's CSV/JSON writer needs extra columns, copy a record from
# tests/test_schedule_viewer_export.py and add the faculty names below.
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
        "faculty": "Smith",
        "room": "Roddy 136",
        "lab": "",
        "times": "MON 10:00-10:50,WED 10:00-10:50,FRI 10:00-10:50",
    },
]


@pytest.fixture
def generated_entry() -> ScheduleEntry:
    """A schedule that came from the generator (no file name)."""
    return ScheduleEntry(
        label="fall_config — schedule 1 (generated)",
        config_name="fall_config",
        source="generated",
        records=[record.copy() for record in SAMPLE_RECORDS],
    )


@pytest.fixture
def loaded_entry() -> ScheduleEntry:
    """A schedule that was loaded from a file."""
    return ScheduleEntry(
        label="fall_config_schedule3.json (file)",
        config_name="fall_config",
        source="file",
        records=[record.copy() for record in SAMPLE_RECORDS],
        file_name="fall_config_schedule3.json",
    )


# ---------------------------------------------------------
# filter_records_by_faculty
# ---------------------------------------------------------


def test_filter_keeps_only_that_faculty_members_courses():
    result = filter_records_by_faculty(SAMPLE_RECORDS, "Hobbes")

    assert [record["course"] for record in result] == ["CMSC 140-01", "CMSC 161-01"]
    assert all(record["faculty"] == "Hobbes" for record in result)


def test_filter_unknown_faculty_returns_empty_list():
    assert filter_records_by_faculty(SAMPLE_RECORDS, "Nobody") == []


def test_filter_does_not_change_the_original_records():
    original = [record.copy() for record in SAMPLE_RECORDS]

    filter_records_by_faculty(SAMPLE_RECORDS, "Hobbes")

    assert SAMPLE_RECORDS == original


# ---------------------------------------------------------
# File names
# ---------------------------------------------------------


def test_safe_name_replaces_characters_not_allowed_in_file_names():
    assert _safe_name("Dr. Smith/Jones") == "Dr._Smith_Jones"
    assert _safe_name('a:b*c?"d') == "a_b_c__d"


def test_safe_name_falls_back_when_empty():
    assert _safe_name("") == "schedule"


def test_default_name_for_generated_schedule_uses_config_name(generated_entry):
    assert default_faculty_file_name(generated_entry, "Hobbes", "csv") == (
        "fall_config_Hobbes.csv"
    )


def test_default_name_for_loaded_schedule_uses_file_name(loaded_entry):
    assert default_faculty_file_name(loaded_entry, "Hobbes", "json") == (
        "fall_config_schedule3_Hobbes.json"
    )


# ---------------------------------------------------------
# export_faculty_schedule: successful exports
# ---------------------------------------------------------


@pytest.mark.parametrize("file_format", ["csv", "json"])
def test_export_only_contains_selected_faculty(generated_entry, file_format):
    export, error = export_faculty_schedule(generated_entry, "Hobbes", file_format, "")

    assert error is None
    content, file_name, media_type = export
    text = content.decode("utf-8")

    assert "CMSC 140-01" in text
    assert "CMSC 161-01" in text
    assert "CMSC 330-01" not in text  # Smith's class is filtered out
    assert "Smith" not in text
    assert media_type == FILTERED_FORMATS[file_format]
    assert file_name == f"fall_config_Hobbes.{file_format}"


def test_exported_json_can_be_loaded_back_into_the_viewer(generated_entry):
    export, error = export_faculty_schedule(generated_entry, "Hobbes", "json", "")
    assert error is None
    content, file_name, _ = export

    # Use the same parser the viewer's Load button uses.
    _, records = parse_schedule_file(file_name, content)

    assert len(records) == 2
    assert all(record["faculty"] == "Hobbes" for record in records)


def test_export_does_not_change_the_loaded_schedule(generated_entry):
    before = [record.copy() for record in generated_entry.records]

    export_faculty_schedule(generated_entry, "Hobbes", "csv", "")

    assert generated_entry.records == before


def test_typed_file_name_is_used(generated_entry):
    export, error = export_faculty_schedule(generated_entry, "Hobbes", "csv", "my_schedule.csv")

    assert error is None
    assert export[1] == "my_schedule.csv"


def test_missing_extension_is_added(generated_entry):
    export, error = export_faculty_schedule(generated_entry, "Hobbes", "json", "hobbes")

    assert error is None
    assert export[1] == "hobbes.json"


def test_folders_are_stripped_from_file_name(generated_entry):
    export, error = export_faculty_schedule(
        generated_entry, "Hobbes", "csv", "../../secret/hobbes.csv"
    )

    assert error is None
    assert export[1] == "hobbes.csv"


# ---------------------------------------------------------
# export_faculty_schedule: error cases
# ---------------------------------------------------------


def test_error_when_no_schedule_loaded():
    export, error = export_faculty_schedule(None, "Hobbes", "csv", "")

    assert export is None
    assert error == "There is no schedule to export."


@pytest.mark.parametrize("faculty", [None, ""])
def test_error_when_no_faculty_selected(generated_entry, faculty):
    export, error = export_faculty_schedule(generated_entry, faculty, "csv", "")

    assert export is None
    assert error == "Please choose a faculty member."


def test_error_for_unsupported_format(generated_entry):
    # PDF isn't supported until Sohil's PDF export is added.
    # When it is, change this test to use a format like "txt".
    export, error = export_faculty_schedule(generated_entry, "Hobbes", "pdf", "")

    assert export is None
    assert error == "Please choose CSV or JSON."


def test_error_when_faculty_has_no_classes(generated_entry):
    export, error = export_faculty_schedule(generated_entry, "Nobody", "csv", "")

    assert export is None
    assert error == "Nobody has no classes in this schedule."


def test_error_for_file_name_with_no_name():
    entry = ScheduleEntry(
        label="x",
        config_name="x",
        source="generated",
        records=[record.copy() for record in SAMPLE_RECORDS],
    )

    export, error = export_faculty_schedule(entry, "Hobbes", "csv", ".csv")

    assert export is None
    assert error == "Please enter a valid file name."


def test_json_export_is_valid_json(generated_entry):
    export, error = export_faculty_schedule(generated_entry, "Hobbes", "json", "")

    assert error is None
    json.loads(export[0])  # raises if the file isn't valid JSON