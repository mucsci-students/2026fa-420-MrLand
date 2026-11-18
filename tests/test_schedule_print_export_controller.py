import pytest

from src.controllers.schedule_print_export_controller import (
    ALL_GROUPS,
    export_print_schedule,
    print_group_options,
)
from src.models.schedule_viewer_model import ScheduleEntry


@pytest.fixture
def schedule_entry():
    return ScheduleEntry(
        label="Fall <schedule> (generated)",
        config_name="Fall schedule",
        source="generated",
        records=[
            {
                "course": "CMSC 420-01",
                "faculty": "Dr. Smith",
                "room": "Room 101",
                "lab": "Lab A",
                "times": "TUE 10:00-10:50,MON 09:00-09:50,TUE 11:00-11:50^",
            },
            {
                "course": "CMSC 430-02",
                "faculty": "Dr. Jones",
                "room": "",
                "lab": "",
                "times": "WED 13:00-13:50@online",
            },
        ],
    )


def test_resource_print_groups_include_rooms_labs_and_online(schedule_entry):
    options = print_group_options(schedule_entry, "resource")

    assert list(options.values()) == [
        "All rooms, labs, and online/unassigned meetings",
        "Room: Room 101",
        "Lab: Lab A",
        "Online: Online",
    ]


def test_resource_layout_sorts_meetings_and_identifies_sections(schedule_entry):
    group = "Room:Room 101"
    export, error = export_print_schedule(schedule_entry, "resource", group)

    assert error is None
    assert export is not None
    content, file_name, media_type = export
    layout = content.decode("utf-8")
    assert file_name == "Fall_schedule_rooms_labs_Room__Room_101_print.html"
    assert media_type == "text/html"
    assert "Schedule — Room and lab grouping" in layout
    assert "Room and lab — Room: Room 101" in layout
    assert "CMSC 420-01" in layout
    assert "Dr. Smith" in layout
    assert layout.index("MON") < layout.index("TUE")
    assert "&lt;schedule&gt;" in layout
    assert "thead { display: table-header-group; }" in layout
    assert "@page { size: Letter portrait; margin: 0.55in; }" in layout


def test_faculty_layout_identifies_resources_and_nonphysical_meetings(schedule_entry):
    group = "faculty:Dr. Smith"
    export, error = export_print_schedule(schedule_entry, "faculty", group)

    assert error is None
    assert export is not None
    layout = export[0].decode("utf-8")
    assert "Faculty — Dr. Smith" in layout
    assert "Room: Room 101" in layout
    assert "Lab: Lab A" in layout
    assert "CMSC 430-02" not in layout

    online_export, online_error = export_print_schedule(
        schedule_entry, "faculty", "faculty:Dr. Jones"
    )
    assert online_error is None
    assert online_export is not None
    assert "<td>Online</td>" in online_export[0].decode("utf-8")


def test_empty_schedule_returns_labeled_print_layout():
    entry = ScheduleEntry(
        label="Empty schedule",
        config_name="empty",
        source="file",
        records=[],
    )

    export, error = export_print_schedule(entry, "resource", ALL_GROUPS)

    assert error is None
    assert export is not None
    assert "No meetings are available in this schedule." in export[0].decode("utf-8")


def test_export_rejects_missing_group_and_malformed_meeting(schedule_entry):
    missing, missing_error = export_print_schedule(schedule_entry, "resource", "Room:missing")
    assert missing is None
    assert missing_error == "Please choose a group available in the selected schedule."

    schedule_entry.records[0]["times"] = "not-a-meeting"
    export, error = export_print_schedule(schedule_entry, "faculty", ALL_GROUPS)
    assert export is None
    assert error == "Could not prepare the print layout: Unrecognized meeting time 'not-a-meeting'."
