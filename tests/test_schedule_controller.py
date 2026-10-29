"""
Tests for ScheduleController.py

"""
import pytest

from src.controllers.schedule_controller import ScheduleController
from src.models.schedule_viewer_model import ScheduleEntry


class FakeModel:
    """Small model substitute for testing ScheduleController."""

    def __init__(self, entries=None):
        self.entries = entries or []
        self.selected_index = 0
        self.generated_received = None

    @property
    def current(self):
        if not self.entries:
            return None
        return self.entries[self.selected_index]

    def select(self, index):
        if 0 <= index < len(self.entries):
            self.selected_index = index

    def set_generated(self, schedules):
        self.generated_received = schedules
        return True


class FakeGenerator:
    def __init__(self, generated_schedules=None):
        self.generated_schedules = generated_schedules or []
        self.clear_generated_schedules_calls = 0

    def clear_generated_schedules(self):
        self.clear_generated_schedules_calls += 1
        self.generated_schedules.clear()
        return True


def make_entry(label, records):
    return ScheduleEntry(label=label, records=records, config_name=label, source="test")


@pytest.fixture
def sample_records():
    return [
        {
            "course": "CS101",
            "faculty": "Dr. Smith",
            "room": "Room 101",
            "lab": "Lab A",
            "times": "MON 09:00-09:50, WED 10:00-10:50",
        }
    ]


@pytest.fixture
def controller(sample_records):
    entries = [
        make_entry("Schedule 1", sample_records),
        make_entry(
            "Schedule 2",
            [
                {
                    "course": "CS102",
                    "faculty": "Dr. Jones",
                    "room": "Room 202",
                    "lab": "Lab B",
                    "times": "TUE 11:00-11:50",
                }
            ],
        ),
    ]

    model = FakeModel(entries)
    generator = FakeGenerator()
    return ScheduleController(model=model, generator=generator)


class TestScheduleNavigation:
    def test_has_schedules_when_entries_exist(self, controller):
        assert controller.has_schedules is True

    def test_no_schedules_when_entries_are_empty(self):
        controller = ScheduleController(
            model=FakeModel(),
            generator=FakeGenerator(),
        )

        assert controller.has_schedules is False
        assert controller.current is None
        assert controller.current_rows() == []

    def test_schedule_options(self, controller):
        assert controller.schedule_options() == {
            0: "Schedule 1",
            1: "Schedule 2",
        }

    def test_select_schedule(self, controller):
        controller.select(1)

        assert controller.selected_index == 1
        assert controller.current.label == "Schedule 2"

    def test_step_forward(self, controller):
        controller.step(1)

        assert controller.selected_index == 1

    def test_step_backward(self, controller):
        controller.select(1)
        controller.step(-1)

        assert controller.selected_index == 0

    def test_can_step_respects_schedule_boundaries(self, controller):
        assert controller.can_step(1) is True
        assert controller.can_step(-1) is False

        controller.select(1)

        assert controller.can_step(1) is False
        assert controller.can_step(-1) is True


class TestCurrentRows:
    def test_converts_schedule_records_into_meeting_rows(
        self, controller
    ):
        rows = controller.current_rows()

        assert len(rows) == 2
        assert rows[0]["course"] == "CS101"
        assert rows[0]["day"] == "MON"
        assert rows[0]["start"] == "09:00"
        assert rows[0]["end"] == "09:50"

        assert rows[1]["day"] == "WED"
        assert rows[1]["start"] == "10:00"
        assert rows[1]["end"] == "10:50"

    def test_assigns_unique_row_ids(self, controller):
        rows = controller.current_rows()

        assert [row["id"] for row in rows] == [1, 2]

    def test_switching_schedule_returns_new_rows(self, controller):
        first_rows = controller.current_rows()

        controller.select(1)
        second_rows = controller.current_rows()

        assert first_rows[0]["course"] == "CS101"
        assert len(second_rows) == 1
        assert second_rows[0]["course"] == "CS102"
        assert second_rows[0]["day"] == "TUE"


class TestGeneratedScheduleSync:
    def test_sync_generated_passes_results_to_model(self, controller):
        generated = [{"example": "generated schedule"}]
        controller.generator.generated_schedules = generated

        changed = controller.sync_generated()

        assert changed is True
        assert controller.model.generated_received == generated

    def test_clear_generated_schedules_delegates_to_generator(self, controller):
        assert controller.clear_generated_schedules() is True
        assert controller.generator.clear_generated_schedules_calls == 1
