"""
Tests for the Schedule Filters Controller

"""

import pytest

from src.controllers.schedule_filters_controller import (
    create_resource_schedule,
    filter_by_course,
    filter_by_faculty,
    filter_by_resource,
    sort_schedule,
)

# ---------------------------------------------------------
# Schedule Stub
# ---------------------------------------------------------

@pytest.fixture
def meeting_schedule():
    """Example schedule containing room, lab, and online meetings."""
    return [
        {
            "course": "CS101",
            "faculty": "Dr. Smith",
            "room": "Room 101",
            "lab": "Lab A",
            "times": "MON 09:00-09:50, WED 10:00-10:50, FRI 13:00-13:50^",
        },
        {
            "course": "CS102",
            "faculty": "Dr. Jones",
            "room": "Room 102",
            "lab": "Lab B",
            "times": "MON 11:00-11:50@online, TUE 09:00-10:50^",
        },
    ]

# ---------------------------------------------------------
# Formatted Schedule Stub
# ---------------------------------------------------------

@pytest.fixture
def resource_schedule():
    """Example schedule already converted into individual meeting rows."""
    return [
        {
            "resource": "Room 101",
            "course": "CS101",
            "faculty": "Dr. Smith",
            "day": "MON",
            "start": "09:00",
            "end": "09:50",
        },
        {
            "resource": "Room 101",
            "course": "CS101",
            "faculty": "Dr. Smith",
            "day": "WED",
            "start": "10:00",
            "end": "10:50",
        },
        {
            "resource": "Lab A",
            "course": "CS101",
            "faculty": "Dr. Smith",
            "day": "FRI",
            "start": "13:00",
            "end": "13:50",
        },
        {
            "resource": "Online",
            "course": "CS102",
            "faculty": "Dr. Jones",
            "day": "MON",
            "start": "11:00",
            "end": "11:50",
        },
        {
            "resource": "Lab B",
            "course": "CS102",
            "faculty": "Dr. Jones",
            "day": "TUE",
            "start": "09:00",
            "end": "10:50",
        },
    ]

# ---------------------------------------------------------
# Formatting Tests
# ---------------------------------------------------------

class TestCreateResourceSchedule:
    def test_creates_one_row_per_meeting(self, meeting_schedule):
        result = create_resource_schedule(meeting_schedule)

        # CS101 has three meetings; CS102 has two.
        assert len(result) == 5

    def test_assigns_rooms_to_regular_meetings(self, meeting_schedule):
        result = create_resource_schedule(meeting_schedule)

        monday_meeting = next(
            row for row in result
            if row["course"] == "CS101" and row["day"] == "MON"
        )

        assert monday_meeting["resource"] == "Room 101"

    def test_assigns_labs_to_lab_meetings(self, meeting_schedule):
        result = create_resource_schedule(meeting_schedule)

        lab_meetings = [
            row for row in result
            if row["resource"].startswith("Lab")
        ]

        assert len(lab_meetings) == 2
        assert {
            row["resource"] for row in lab_meetings
        } == {"Lab A", "Lab B"}

    def test_assigns_online_resource(self, meeting_schedule):
        result = create_resource_schedule(meeting_schedule)

        online_meeting = next(
            row for row in result
            if row["course"] == "CS102" and row["day"] == "MON"
        )

        assert online_meeting["resource"] == "Online"
        assert online_meeting["start"] == "11:00"
        assert online_meeting["end"] == "11:50"

    def test_skips_empty_time_entries(self):
        schedule = [
            {
                "course": "CS103",
                "faculty": "Dr. Lee",
                "room": "Room 103",
                "lab": "Lab C",
                "times": "MON 09:00-09:50, , WED 10:00-10:50, ",
            }
        ]

        result = create_resource_schedule(schedule)

        assert len(result) == 2
        assert {row["day"] for row in result} == {"MON", "WED"}

    def test_empty_schedule_returns_empty_list(self):
        assert create_resource_schedule([]) == []

# ---------------------------------------------------------
# Filtering
# ---------------------------------------------------------

class TestScheduleFilters:
    def test_filters_by_resource(self, resource_schedule):
        result = filter_by_resource(resource_schedule, "Room 101")

        assert len(result) == 2
        assert all(row["resource"] == "Room 101" for row in result)

    def test_filters_by_faculty(self, resource_schedule):
        result = filter_by_faculty(resource_schedule, "Dr. Smith")

        assert len(result) == 3
        assert all(row["faculty"] == "Dr. Smith" for row in result)

    def test_filters_by_course(self, resource_schedule):
        result = filter_by_course(resource_schedule, "CS102")

        assert len(result) == 2
        assert all(row["course"] == "CS102" for row in result)

    def test_resource_and_day_filter_together(self, resource_schedule):
        # The controller filters by resource; the viewer can then
        # restrict those results to the selected day.
        resource_results = filter_by_resource(
            resource_schedule, "Room 101"
        )
        result = [
            row for row in resource_results
            if row["day"] == "MON"
        ]

        assert len(result) == 1
        assert result[0]["start"] == "09:00"

    def test_faculty_and_day_filter_together(self, resource_schedule):
        faculty_results = filter_by_faculty(
            resource_schedule, "Dr. Smith"
        )
        result = [
            row for row in faculty_results
            if row["day"] == "WED"
        ]

        assert len(result) == 1
        assert result[0]["course"] == "CS101"
        assert result[0]["start"] == "10:00"

    def test_unknown_filters_return_empty_lists(self, resource_schedule):
        assert filter_by_resource(resource_schedule, "Room 999") == []
        assert filter_by_faculty(resource_schedule, "Unknown Faculty") == []
        assert filter_by_course(resource_schedule, "CS999") == []

    def test_filters_accept_empty_schedule(self):
        assert filter_by_resource([], "Room 101") == []
        assert filter_by_faculty([], "Dr. Smith") == []
        assert filter_by_course([], "CS101") == []


# ---------------------------------------------------------
# Sorting
# ---------------------------------------------------------

class TestSortSchedule:
    def test_default_sort_orders_by_day_then_start_time(
        self, resource_schedule
    ):
        result = sort_schedule(resource_schedule)

        assert [
            (row["day"], row["start"]) for row in result
        ] == [
            ("MON", "09:00"),
            ("MON", "11:00"),
            ("TUE", "09:00"),
            ("WED", "10:00"),
            ("FRI", "13:00"),
        ]

    def test_sorts_by_day_descending(self, resource_schedule):
        result = sort_schedule(
            resource_schedule, column="day", descending=True
        )

        assert [row["day"] for row in result] == [
            "FRI", "WED", "TUE", "MON", "MON"
        ]

    def test_sorts_by_course(self, resource_schedule):
        result = sort_schedule(resource_schedule, column="course")

        assert [row["course"] for row in result] == [
            "CS101", "CS101", "CS101", "CS102", "CS102"
        ]

    def test_empty_schedule_returns_empty_list(self):
        assert sort_schedule([]) == []