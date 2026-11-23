"""Tests for the Schedule Comparison tab."""

from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from src.views.schedule_analysis import comparison_tab
from src.views.schedule_calendar_view import ScheduleCalendarView

# ---------------------------------------------------------
# Mock NiceGUI components
# ---------------------------------------------------------


class FakeContext:
    """Mock a NiceGUI context manager."""

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def classes(self, *args):
        return self

    def props(self, *args):
        return self

    def style(self, *args):
        return self


class FakeSelect:
    """Mock a NiceGUI select component."""

    def __init__(self, options=None, value=None, label=None):
        self.options = options
        self.value = value
        self.label = label
        self.callback = None
        self.update_count = 0
        self.enabled = True

    def classes(self, *args):
        return self

    def props(self, *args):
        return self

    def update(self):
        self.update_count += 1

    def on_value_change(self, callback):
        self.callback = callback

    def enable(self):
        self.enabled = True
        return self

    def disable(self):
        self.enabled = False
        return self

    def trigger(self):
        if self.callback:
            self.callback(None)


class FakeLabel:
    """Mock a NiceGUI label."""

    def __init__(self, text=""):
        self.text = text
        self.update_count = 0

    def classes(self, *args):
        return self

    def style(self, *args):
        return self

    def update(self):
        self.update_count += 1


class FakeButton(FakeContext):
    """Mock a NiceGUI button."""

    def __init__(self, *args, on_click=None, **kwargs):
        self.callback = on_click

    def click(self):
        if self.callback:
            self.callback()


class FakeCalendar:
    """Record calendar updates."""

    def __init__(self):
        self.updates = []

    def update(
        self,
        rows,
        selected_day=None,
        *,
        display_mode="Entire Schedule",
        color_schedule=None,
        time_range=None,
    ):
        self.updates.append(
            {
                "rows": list(rows),
                "selected_day": selected_day,
                "display_mode": display_mode,
                "color_schedule": color_schedule,
                "time_range": time_range,
            }
        )

    @staticmethod
    def _to_minutes(time_value):
        return ScheduleCalendarView._to_minutes(time_value)


class FakeUI:
    """Mock the NiceGUI components used by comparison_tab."""

    def __init__(self):
        self.selects = []
        self.labels = []
        self.buttons = []
        self.notifications = []

    def add_head_html(self, *args, **kwargs):
        pass

    def element(self, *args):
        return FakeContext()

    def row(self, *args):
        return FakeContext()

    def column(self, *args):
        return FakeContext()

    def tabs(self, *args):
        return FakeContext()

    def tab(self, *args, **kwargs):
        return FakeContext()

    def tab_panels(self, *args, **kwargs):
        return FakeContext()

    def tab_panel(self, *args):
        return FakeContext()

    def select(self, options=None, value=None, label=None, **kwargs):
        select = FakeSelect(options, value, label)
        self.selects.append(select)
        return select

    def label(self, text=""):
        label = FakeLabel(text)
        self.labels.append(label)
        return label

    def button(self, *args, **kwargs):
        button = FakeButton(*args, **kwargs)
        self.buttons.append(button)
        return button

    def notify(self, message, **kwargs):
        self.notifications.append((message, kwargs))


# ---------------------------------------------------------
# Mock schedule controller
# ---------------------------------------------------------


class FakeScheduleController:
    """Provide predictable schedules and meeting rows."""

    def __init__(self):
        self.options = {
            0: "Schedule A",
            1: "Schedule B",
            2: "Schedule C",
        }

        self.entries = {
            0: SimpleNamespace(
                label="Schedule A",
                records=[
                    {
                        "course": "CS101",
                        "room": "Room 1",
                        "lab": "Lab 1",
                    },
                    {
                        "course": "CS102",
                        "room": "Room 2",
                        "lab": None,
                    },
                ],
            ),
            1: SimpleNamespace(
                label="Schedule B",
                records=[
                    {
                        "course": "CS101",
                        "room": "Room 3",
                        "lab": "Lab 2",
                    },
                    {
                        "course": "MATH201",
                        "room": "Room 4",
                        "lab": None,
                    },
                ],
            ),
            2: SimpleNamespace(
                label="Schedule C",
                records=[
                    {
                        "course": "MATH201",
                        "room": "Room 5",
                        "lab": None,
                    },
                ],
            ),
        }

        self.rows = {
            0: [
                {
                    "course": "CS101",
                    "faculty": "Smith",
                    "resource": "Room 1",
                    "day": "MON",
                    "start": "08:00",
                    "end": "09:00",
                },
                {
                    "course": "CS101",
                    "faculty": "Smith",
                    "resource": "Lab 1",
                    "day": "TUE",
                    "start": "10:00",
                    "end": "11:00",
                },
                {
                    "course": "CS102",
                    "faculty": "Jones",
                    "resource": "Room 2",
                    "day": "TUE",
                    "start": "12:00",
                    "end": "13:00",
                },
            ],
            1: [
                {
                    "course": "CS101",
                    "faculty": "Brown",
                    "resource": "Room 3",
                    "day": "MON",
                    "start": "09:00",
                    "end": "10:00",
                },
                {
                    "course": "CS101",
                    "faculty": "Brown",
                    "resource": "Lab 2",
                    "day": "WED",
                    "start": "11:00",
                    "end": "12:00",
                },
                {
                    "course": "MATH201",
                    "faculty": "Smith",
                    "resource": "Room 4",
                    "day": "WED",
                    "start": "13:00",
                    "end": "14:00",
                },
            ],
            2: [
                {
                    "course": "MATH201",
                    "faculty": "Jones",
                    "resource": "Room 5",
                    "day": "FRI",
                    "start": "14:00",
                    "end": "15:00",
                },
            ],
        }

        self.selected_index = 0
        self.has_schedules = True

    def schedule_options(self):
        return self.options.copy()

    def entry_at(self, index):
        return self.entries.get(index)

    def rows_for(self, index):
        return list(self.rows.get(index, []))


# ---------------------------------------------------------
# Fixtures
# ---------------------------------------------------------


@pytest.fixture
def comparison(monkeypatch):
    """Build the comparison tab with mocked dependencies."""

    fake_ui = FakeUI()
    controller = FakeScheduleController()

    calendars = []
    statistics_refreshers = []
    statistics_titles = []

    def fake_calendar(*args, **kwargs):
        calendar = FakeCalendar()
        calendars.append(calendar)
        return calendar

    def fake_statistics_panel(initial_title):
        refresh = Mock()
        title = Mock()
        statistics_refreshers.append(refresh)
        statistics_titles.append(title)
        return refresh, title

    monkeypatch.setattr(comparison_tab, "ui", fake_ui)
    monkeypatch.setattr(comparison_tab, "schedule_controller", controller)
    monkeypatch.setattr(
        comparison_tab,
        "surface_card",
        lambda *args, **kwargs: FakeContext(),
    )
    monkeypatch.setattr(
        comparison_tab,
        "schedule_calendar_view",
        fake_calendar,
    )
    monkeypatch.setattr(
        comparison_tab,
        "build_statistics_comparison_panel",
        fake_statistics_panel,
    )

    load_callback = Mock()

    refresh = comparison_tab.build_comparison_tab(load_callback)

    return SimpleNamespace(
        ui=fake_ui,
        controller=controller,
        calendars=calendars,
        statistics=statistics_refreshers,
        statistics_titles=statistics_titles,
        load_callback=load_callback,
        refresh=refresh,
        first_select=fake_ui.selects[0],
        second_select=fake_ui.selects[1],
        filter_type=fake_ui.selects[2],
        filter_value=fake_ui.selects[3],
        day_filter=fake_ui.selects[4],
    )


# ---------------------------------------------------------
# Initial state
# ---------------------------------------------------------


def test_initial_schedule_selections(comparison):
    """The first two available schedules are initially selected."""

    assert comparison.first_select.value == 0
    assert comparison.second_select.value == 1


def test_initial_calendar_and_statistics_updates(comparison):
    """Initial construction refreshes both calendars and statistics."""

    assert len(comparison.calendars) == 2
    assert len(comparison.calendars[0].updates) == 1
    assert len(comparison.calendars[1].updates) == 1

    assert comparison.statistics[0].call_count == 1
    assert comparison.statistics[1].call_count == 1


# ---------------------------------------------------------
# Selector behavior
# ---------------------------------------------------------


def test_first_selector_change_preserves_second(comparison):
    """Changing the first schedule does not overwrite the second."""

    comparison.first_select.value = 2
    comparison.first_select.trigger()

    assert comparison.first_select.value == 2
    assert comparison.second_select.value == 1


def test_second_selector_change_preserves_first(comparison):
    """Changing the second schedule does not overwrite the first."""

    comparison.second_select.value = 2
    comparison.second_select.trigger()

    assert comparison.first_select.value == 0
    assert comparison.second_select.value == 2


def test_selector_options_exclude_opposite_selection(comparison):
    """Each selector excludes the schedule selected in the other."""

    comparison.first_select.value = 2
    comparison.first_select.trigger()

    assert 1 not in comparison.first_select.options
    assert 2 in comparison.first_select.options

    assert 2 not in comparison.second_select.options
    assert 1 in comparison.second_select.options


def test_duplicate_first_selection_is_rejected(comparison):
    """The first selector restores its previous value on duplication."""

    comparison.first_select.value = 1
    comparison.first_select.trigger()

    assert comparison.first_select.value == 0
    assert comparison.second_select.value == 1
    assert len(comparison.ui.notifications) == 1


def test_duplicate_second_selection_is_rejected(comparison):
    """The second selector restores its previous value on duplication."""

    comparison.second_select.value = 0
    comparison.second_select.trigger()

    assert comparison.first_select.value == 0
    assert comparison.second_select.value == 1
    assert len(comparison.ui.notifications) == 1


# ---------------------------------------------------------
# Schedule selection helpers and refresh behavior
# ---------------------------------------------------------


def test_full_refresh_preserves_valid_selections(comparison):
    """A full refresh preserves both valid selections."""

    comparison.refresh()

    assert comparison.first_select.value == 0
    assert comparison.second_select.value == 1


def test_refresh_removes_invalid_selection(comparison):
    """A selection missing from the schedule list is cleared."""

    comparison.controller.options = {
        0: "Schedule A",
        2: "Schedule C",
    }

    comparison.refresh()

    assert comparison.first_select.value == 0
    assert comparison.second_select.value is None


def test_targeted_refresh_updates_both_calendars(comparison):
    """A targeted refresh updates both calendars because they share a time axis."""

    first_count = len(comparison.calendars[0].updates)
    second_count = len(comparison.calendars[1].updates)

    comparison.refresh(comparison.first_select, 2)

    assert comparison.first_select.value == 2
    assert comparison.second_select.value == 1

    assert len(comparison.calendars[0].updates) == first_count + 1
    assert len(comparison.calendars[1].updates) == second_count + 1

    assert comparison.statistics[0].call_count == 2
    assert comparison.statistics[1].call_count == 1


def test_targeted_refresh_updates_only_second_statistics(comparison):
    """A targeted second-column refresh updates only its statistics."""

    first_calendar_count = len(comparison.calendars[0].updates)
    second_calendar_count = len(comparison.calendars[1].updates)

    comparison.refresh(comparison.second_select, 2)

    assert comparison.first_select.value == 0
    assert comparison.second_select.value == 2

    assert len(comparison.calendars[0].updates) == first_calendar_count + 1
    assert len(comparison.calendars[1].updates) == second_calendar_count + 1

    assert comparison.statistics[0].call_count == 1
    assert comparison.statistics[1].call_count == 2


def test_targeted_refresh_with_duplicate_selection(comparison):
    """A targeted refresh does not allow both columns to select one schedule."""

    comparison.refresh(comparison.first_select, 1)

    assert comparison.first_select.value == 1
    assert comparison.second_select.value is None


def test_targeted_refresh_with_missing_index(comparison):
    """A missing uploaded schedule index clears the target selection."""

    comparison.refresh(comparison.first_select, 99)

    assert comparison.first_select.value is None
    assert comparison.second_select.value == 1


# ---------------------------------------------------------
# Schedule names and statistics
# ---------------------------------------------------------


def test_full_refresh_updates_schedule_statistics(comparison):
    """A full refresh sends the correct entries to both statistics panels."""

    comparison.refresh()

    assert comparison.statistics[0].call_args.args[0] is (comparison.controller.entries[0])
    assert comparison.statistics[1].call_args.args[0] is (comparison.controller.entries[1])


def test_targeted_refresh_updates_correct_statistics(comparison):
    """A targeted refresh sends only the target entry to its statistics panel."""

    comparison.refresh(comparison.second_select, 2)

    assert comparison.statistics[1].call_args.args[0] is (comparison.controller.entries[2])

    assert comparison.statistics[0].call_args.args[0] is (comparison.controller.entries[0])


# ---------------------------------------------------------
# Filter behavior
# ---------------------------------------------------------


def test_faculty_filter_values(comparison):
    """Faculty filter choices are collected from both schedules."""

    comparison.filter_type.value = "Faculty"
    comparison.filter_type.trigger()

    assert comparison.filter_value.options == [
        "Brown",
        "Jones",
        "Smith",
    ]


def test_resource_filter_values(comparison):
    """Room and lab choices include configured resources from both schedules."""

    comparison.filter_type.value = "Room / Lab"
    comparison.filter_type.trigger()

    assert comparison.filter_value.options == [
        "Lab 1",
        "Lab 2",
        "Room 1",
        "Room 2",
        "Room 3",
        "Room 4",
    ]


def test_entire_schedule_disables_value_filter(comparison):
    """Entire Schedule removes and disables the faculty/resource selector."""

    comparison.filter_type.value = "Entire Schedule"
    comparison.filter_type.trigger()

    assert comparison.filter_value.options == []
    assert comparison.filter_value.value is None
    assert comparison.filter_value.enabled is False


def test_clearing_filter_type_removes_filter_values(comparison):
    """Clearing the view type removes the available filter values."""

    comparison.filter_type.value = None
    comparison.filter_type.trigger()

    assert comparison.filter_value.options == []
    assert comparison.filter_value.value is None
    assert comparison.filter_value.enabled is False


def test_faculty_filter_updates_both_calendars(comparison):
    """Selecting a faculty member filters both schedules independently."""

    comparison.filter_type.value = "Faculty"
    comparison.filter_type.trigger()

    comparison.filter_value.value = "Smith"
    comparison.filter_value.trigger()

    first_rows = comparison.calendars[0].updates[-1]["rows"]
    second_rows = comparison.calendars[1].updates[-1]["rows"]

    assert [row["course"] for row in first_rows] == ["CS101", "CS101"]
    assert [row["day"] for row in first_rows] == ["MON", "TUE"]
    assert [row["course"] for row in second_rows] == ["MATH201"]


def test_room_filter_displays_all_course_assignments(comparison):
    """Selecting a room displays all meetings for its associated course."""

    comparison.filter_type.value = "Room / Lab"
    comparison.filter_type.trigger()

    comparison.filter_value.value = "Room 1"
    comparison.filter_value.trigger()

    first_rows = comparison.calendars[0].updates[-1]["rows"]
    second_rows = comparison.calendars[1].updates[-1]["rows"]

    # CS101 uses Room 1 and Lab 1 in Schedule A.
    assert [row["resource"] for row in first_rows] == [
        "Room 1",
        "Lab 1",
    ]

    # Schedule B has no course configured to use Room 1.
    assert second_rows == []


def test_lab_filter_displays_all_course_assignments(comparison):
    """Selecting a lab displays all meetings for its associated course."""

    comparison.filter_type.value = "Room / Lab"
    comparison.filter_type.trigger()

    comparison.filter_value.value = "Lab 1"
    comparison.filter_value.trigger()

    first_rows = comparison.calendars[0].updates[-1]["rows"]
    second_rows = comparison.calendars[1].updates[-1]["rows"]

    assert [row["resource"] for row in first_rows] == [
        "Room 1",
        "Lab 1",
    ]

    assert second_rows == []


def test_resource_filter_uses_each_schedules_own_records(comparison):
    """The same resource selection is evaluated independently for each schedule."""

    comparison.filter_type.value = "Room / Lab"
    comparison.filter_type.trigger()

    comparison.filter_value.value = "Room 3"
    comparison.filter_value.trigger()

    first_rows = comparison.calendars[0].updates[-1]["rows"]
    second_rows = comparison.calendars[1].updates[-1]["rows"]

    assert first_rows == []

    assert [row["resource"] for row in second_rows] == [
        "Room 3",
        "Lab 2",
    ]


def test_resource_filter_falls_back_to_meeting_resource(comparison):
    """A resource without a matching configuration record uses exact matching."""

    comparison.controller.entries[0].records = []

    comparison.filter_type.value = "Room / Lab"
    comparison.filter_type.trigger()

    comparison.filter_value.value = "Room 1"
    comparison.filter_value.trigger()

    first_rows = comparison.calendars[0].updates[-1]["rows"]

    assert len(first_rows) == 1
    assert first_rows[0]["resource"] == "Room 1"


def test_day_filter_updates_both_calendars(comparison):
    """Selecting a day filters both schedules."""

    comparison.day_filter.value = "MON"
    comparison.day_filter.trigger()

    first_rows = comparison.calendars[0].updates[-1]["rows"]
    second_rows = comparison.calendars[1].updates[-1]["rows"]

    assert all(row["day"] == "MON" for row in first_rows)
    assert all(row["day"] == "MON" for row in second_rows)

    assert comparison.calendars[0].updates[-1]["selected_day"] == "MON"
    assert comparison.calendars[1].updates[-1]["selected_day"] == "MON"


def test_combined_room_and_day_filters(comparison):
    """Room/lab and day filters are applied together."""

    comparison.filter_type.value = "Room / Lab"
    comparison.filter_type.trigger()

    comparison.filter_value.value = "Room 1"
    comparison.filter_value.trigger()

    comparison.day_filter.value = "TUE"
    comparison.day_filter.trigger()

    first_rows = comparison.calendars[0].updates[-1]["rows"]

    assert len(first_rows) == 1
    assert first_rows[0]["course"] == "CS101"
    assert first_rows[0]["resource"] == "Lab 1"
    assert first_rows[0]["day"] == "TUE"

    assert comparison.calendars[0].updates[-1]["selected_day"] == "TUE"


def test_invalid_previous_filter_value_is_cleared(comparison):
    """A filter value not present in the selected schedules is removed."""

    comparison.filter_type.value = "Faculty"
    comparison.filter_type.trigger()

    comparison.filter_value.value = "NOT A FACULTY MEMBER"
    comparison.refresh()

    assert comparison.filter_value.value == "Brown"


def test_resource_filter_displays_multiple_courses_sharing_resource(comparison):
    """Selecting a shared room displays meetings for every assigned course."""

    comparison.controller.entries[0].records.append(
        {
            "course": "CS102",
            "room": "Room 1",
            "lab": None,
        }
    )

    comparison.filter_type.value = "Room / Lab"
    comparison.filter_type.trigger()

    comparison.filter_value.value = "Room 1"
    comparison.filter_value.trigger()

    first_rows = comparison.calendars[0].updates[-1]["rows"]

    assert {row["course"] for row in first_rows} == {"CS101", "CS102"}


# ---------------------------------------------------------
# Shared calendar time range
# ---------------------------------------------------------


def test_both_calendars_receive_same_time_range(comparison):
    """Both calendars receive a shared time range from both schedules."""

    first_update = comparison.calendars[0].updates[-1]
    second_update = comparison.calendars[1].updates[-1]

    assert first_update["time_range"] == (480, 840)
    assert second_update["time_range"] == (480, 840)


def test_shared_time_range_updates_when_schedule_changes(comparison):
    """The shared time range is recalculated after changing a schedule."""

    comparison.refresh(comparison.second_select, 2)

    first_update = comparison.calendars[0].updates[-1]
    second_update = comparison.calendars[1].updates[-1]

    assert first_update["time_range"] == (480, 900)
    assert second_update["time_range"] == (480, 900)


# ---------------------------------------------------------
# Upload button callbacks
# ---------------------------------------------------------


def test_first_load_button_passes_first_selector(comparison):
    """The first Load Schedule button passes the first selector."""

    comparison.ui.buttons[0].click()

    comparison.load_callback.assert_called_once_with(comparison.first_select)


def test_second_load_button_passes_second_selector(comparison):
    """The second Load Schedule button passes the second selector."""

    comparison.ui.buttons[1].click()

    comparison.load_callback.assert_called_once_with(comparison.second_select)
