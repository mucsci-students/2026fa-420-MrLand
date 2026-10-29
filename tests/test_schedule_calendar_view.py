"""
Tests for the Calendar View

"""


import pytest

from src.views.schedule_calendar_view import ScheduleCalendarView

# ---------------------------------------------------------
# Calendar Helpers
# ---------------------------------------------------------

class TestCalendarTimeHelpers:

    @pytest.mark.parametrize(
        ("time_value", "expected"),
        [
            ("08:00", 480),
            ("09:30", 570),
            ("12:00", 720),
            ("13:45", 825),
            ("23:59", 1439),
        ],
    )
    def test_to_minutes(self, time_value, expected):
        assert ScheduleCalendarView._to_minutes(time_value) == expected

    @pytest.mark.parametrize(
        ("minutes", "expected"),
        [
            (0, "12:00 AM"),
            (480, "8:00 AM"),
            (720, "12:00 PM"),
            (780, "1:00 PM"),
            (1439, "11:59 PM"),
        ],
    )
    def test_format_time(self, minutes, expected):
        assert ScheduleCalendarView._format_time(minutes) == expected

    @pytest.mark.parametrize(
        "time_value",
        [
            "25:00",
            "12:60",
            "invalid",
            "",
        ],
    )
    def test_to_minutes_rejects_invalid_times(self, time_value):
        with pytest.raises((ValueError, TypeError)):
            ScheduleCalendarView._to_minutes(time_value)

# ---------------------------------------------------------
# Calendar Event Layout
# ---------------------------------------------------------

class TestCalendarEventLayout:

    def test_non_overlapping_meetings_reuse_lane(self):
        meetings = [
            ({"course": "CS101"}, 540, 600),
            ({"course": "CS102"}, 600, 660),
        ]

        result = ScheduleCalendarView._layout_day_events(meetings)

        assert len(result) == 2
        assert result[0][3] == 0
        assert result[1][3] == 0

    def test_overlapping_meetings_use_separate_lanes(self):
        meetings = [
            ({"course": "CS101"}, 540, 660),
            ({"course": "CS102"}, 600, 720),
        ]

        result = ScheduleCalendarView._layout_day_events(meetings)

        assert len(result) == 2
        assert result[0][3] != result[1][3]
        assert result[0][4] == 2
        assert result[1][4] == 2

    def test_empty_meeting_list_returns_empty_result(self):
        assert ScheduleCalendarView._layout_day_events([]) == []
