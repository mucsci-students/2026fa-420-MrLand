"""
Unit tests for the ScheduleGeneratorController class.

"""

from types import SimpleNamespace
from typing import cast

import pytest
from scheduler.config import OptimizerFlags

from src.controllers.schedule_generator_controller import (
    ScheduleGeneratorController,
)
from src.models.schedule_generator_model import ScheduleGeneratorModel


class FakeGeneratorModel:
    def __init__(self, running=False, config=None, begin_result=True):
        self.running = running
        self.config = config or SimpleNamespace(limit=10)
        self.begin_result = begin_result
        self.begin_calls = []
        self.generate_calls = []
        self.generate_configuration_calls = []
        self.load_error = None
        self.generated_schedules = []
        self.clear_generated_schedules_result = True
        self.clear_generated_schedules_calls = 0

    def state_snapshot(self):
        return SimpleNamespace(
            running=self.running,
            error=None,
        )

    def begin_generation(self, config_name, limit):
        self.begin_calls.append((config_name, limit))

        if self.running or not self.begin_result:
            return False

        self.running = True
        return True

    def load_config(self, config_name):
        if self.load_error:
            raise self.load_error
        return self.config

    def generate(self, config_name, limit_override, optimizer_override):
        self.generate_calls.append(
            (config_name, limit_override, optimizer_override)
        )

    def generate_configuration(self, config_name, config):
        self.generate_configuration_calls.append((config_name, config))

    def clear_generated_schedules(self):
        self.clear_generated_schedules_calls += 1
        if self.clear_generated_schedules_result:
            self.generated_schedules.clear()
        return self.clear_generated_schedules_result


@pytest.fixture
def model():
    return FakeGeneratorModel()


@pytest.fixture
def controller(model):
    return ScheduleGeneratorController(model=cast(ScheduleGeneratorModel, model))


class TestStartGenerationValidation:
    def test_requires_configuration(self, controller, model):
        requested, error = controller.start_generation(
            None, None, None
        )

        assert requested is None
        assert error == "Please select a configuration."
        assert model.begin_calls == []

    def test_rejects_request_when_already_running(self):
        model = FakeGeneratorModel(running=True)
        controller = ScheduleGeneratorController(model=cast(ScheduleGeneratorModel, model))

        requested, error = controller.start_generation(
            "config.json", None, None
        )

        assert requested is None
        assert error is not None
        assert "already in progress" in error
        assert model.begin_calls == []

    @pytest.mark.parametrize("invalid_limit", [
        "abc", "0", "-1", "1.5", object()
    ])
    def test_rejects_invalid_temporary_limit(
        self, controller, model, invalid_limit
    ):
        requested, error = controller.start_generation(
            "config.json", invalid_limit, None
        )

        assert requested is None
        assert error == (
            "Temporary generation limit must be a positive whole number."
        )
        assert model.begin_calls == []

    def test_configuration_load_failure_is_reported(
        self, controller, model
    ):
        model.load_error = ValueError("invalid configuration")

        requested, error = controller.start_generation(
            "config.json", None, None
        )

        assert requested is None
        assert "Could not load configuration" in error
        assert "invalid configuration" in error
        assert model.begin_calls == []

    def test_begin_generation_rejection_is_handled(
        self, controller, model
    ):
        model.begin_result = False

        requested, error = controller.start_generation(
            "config.json", None, None
        )

        assert requested is None
        assert error is None


class TestStartGeneration:
    def test_uses_configuration_limit_when_no_override(
        self, controller, model, monkeypatch
    ):
        started_threads = []

        class FakeThread:
            def __init__(self, target, args, daemon):
                self.target = target
                self.args = args
                self.daemon = daemon

            def start(self):
                started_threads.append(self)

        monkeypatch.setattr(
            "src.controllers.schedule_generator_controller.threading.Thread",
            FakeThread,
        )

        requested, error = controller.start_generation(
            "config.json", None, None
        )

        assert requested == 10
        assert error is None
        assert model.begin_calls == [("config.json", 10)]
        assert len(started_threads) == 1
        assert started_threads[0].target == model.generate
        assert started_threads[0].args == ("config.json", None, None)
        assert started_threads[0].daemon is True

    def test_uses_valid_limit_override(
        self, controller, model, monkeypatch
    ):
        class FakeThread:
            def __init__(self, target, args, daemon):
                self.target = target
                self.args = args
                self.daemon = daemon

            def start(self):
                pass

        monkeypatch.setattr(
            "src.controllers.schedule_generator_controller.threading.Thread",
            FakeThread,
        )

        requested, error = controller.start_generation(
            "config.json", "25", ["optimizer-a"]
        )

        assert requested == 25
        assert error is None
        assert model.begin_calls == [("config.json", 25)]

    def test_generates_from_uploaded_configuration_without_mutating_it(
        self, controller, model, monkeypatch
    ):
        started_threads = []

        class FakeThread:
            def __init__(self, target, args, daemon):
                self.target = target
                self.args = args
                self.daemon = daemon

            def start(self):
                started_threads.append(self)

        monkeypatch.setattr(
            "src.controllers.schedule_generator_controller.threading.Thread",
            FakeThread,
        )
        uploaded_config = SimpleNamespace(
            limit=10,
            optimizer_flags=["original"],
            time_slot_config=SimpleNamespace(
                max_time_gap=30,
                min_time_overlap=10,
            ),
        )
        model.load_error = RuntimeError("saved config should not be loaded")

        requested, error = controller.start_generation(
            "uploaded", "25", [OptimizerFlags.FACULTY_COURSE.value], "45", "15",
            loaded_config=uploaded_config,
        )

        assert requested == 25
        assert error is None
        assert model.begin_calls == [("uploaded", 25)]
        assert len(started_threads) == 1
        assert started_threads[0].target == model.generate_configuration
        generated_config = started_threads[0].args[1]
        assert generated_config.limit == 25
        assert generated_config.optimizer_flags == [OptimizerFlags.FACULTY_COURSE]
        assert generated_config.time_slot_config.max_time_gap == 45
        assert generated_config.time_slot_config.min_time_overlap == 15
        assert started_threads[0].daemon is True
        assert uploaded_config.limit == 10
        assert uploaded_config.optimizer_flags == ["original"]
        assert uploaded_config.time_slot_config.max_time_gap == 30
        assert uploaded_config.time_slot_config.min_time_overlap == 10

    def test_duplicate_request_does_not_start_another_thread(
        self, model, monkeypatch
    ):
        controller = ScheduleGeneratorController(model=model)
        started_threads = []

        class FakeThread:
            def __init__(self, target, args, daemon):
                self.target = target
                self.args = args
                self.daemon = daemon

            def start(self):
                started_threads.append(self)

        monkeypatch.setattr(
            "src.controllers.schedule_generator_controller.threading.Thread",
            FakeThread,
        )

        first_result = controller.start_generation(
            "config.json", None, None
        )
        second_result = controller.start_generation(
            "config.json", None, None
        )

        assert first_result == (10, None)
        assert second_result[0] is None
        assert second_result[1] is not None
        assert "already in progress" in second_result[1]
        assert len(started_threads) == 1


class TestGenerateActiveConfiguration:
    def test_rejects_request_when_already_running(self):
        model = FakeGeneratorModel(running=True)
        controller = ScheduleGeneratorController(model=cast(ScheduleGeneratorModel, model))
        config = SimpleNamespace(limit=5)

        state, error = controller.generate_active_configuration(
            config, "active"
        )

        assert state is None
        assert error is not None
        assert "already in progress" in error
        assert model.begin_calls == []
        assert model.generate_configuration_calls == []

    def test_begins_and_generates_active_configuration(
        self, controller, model
    ):
        config = SimpleNamespace(limit=5)

        state, error = controller.generate_active_configuration(
            config, "active"
        )

        assert state is not None
        assert state.running is True
        assert error is None
        assert model.begin_calls == [("active", 5)]
        assert model.generate_configuration_calls == [("active", config)]


class TestClearGeneratedSchedules:
    def test_clears_generated_schedules(self, controller, model):
        model.generated_schedules.append("old result")

        assert controller.clear_generated_schedules() is True
        assert model.generated_schedules == []
        assert model.clear_generated_schedules_calls == 1

    def test_reports_when_clear_is_rejected(self, controller, model):
        model.clear_generated_schedules_result = False

        assert controller.clear_generated_schedules() is False
        assert model.clear_generated_schedules_calls == 1
