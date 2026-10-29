"""
Tests for the ScheduleGeneratorModel class, which manages the state of schedule generation

"""

import threading
from types import SimpleNamespace
from typing import Any, ClassVar

import pytest

from src.models.schedule_generator_model import ScheduleGeneratorModel


class FakeScheduler:
    """Controllable replacement for the real scheduler."""

    schedules: ClassVar[list[Any] | Exception] = []
    audit_valid: ClassVar[bool] = True
    diagnosis_result: ClassVar[dict[str, str]] = {"reason": "No compatible room assignments"}

    def __init__(self, config):
        self.config = config

    def get_models(self):
        if isinstance(self.schedules, Exception):
            raise self.schedules
        return iter(self.schedules)

    def audit_schedule(self, schedule):
        return SimpleNamespace(is_valid=self.audit_valid)

    def diagnose(self):
        return self.diagnosis_result


@pytest.fixture
def model():
    return ScheduleGeneratorModel()


@pytest.fixture
def config():
    return SimpleNamespace(
        limit=2,
        optimizer_flags=[],
    )


@pytest.fixture
def patch_scheduler(monkeypatch):
    """Install a fresh fake scheduler for each test."""
    FakeScheduler.schedules = []
    FakeScheduler.audit_valid = True
    FakeScheduler.diagnosis_result = {"reason": "No compatible room assignments"}

    monkeypatch.setattr(
        "src.models.schedule_generator_model.Scheduler",
        FakeScheduler,
    )


class TestBeginGeneration:
    def test_enters_running_state(self, model):
        assert model.begin_generation("test-config", 3) is True

        state = model.state_snapshot()

        assert state.running is True
        assert state.finished is False
        assert state.config_name == "test-config"
        assert state.requested == 3
        assert state.message == "Starting scheduler..."
        assert state.error is None

    def test_refuses_duplicate_generation(self, model):
        assert model.begin_generation("first", 2) is True

        original_state = model.state_snapshot()
        second_result = model.begin_generation("second", 5)
        current_state = model.state_snapshot()

        assert second_result is False
        assert current_state.generation_id == original_state.generation_id
        assert current_state.config_name == "first"
        assert current_state.running is True

    def test_new_generation_clears_previous_results(self, model):
        model._generated_schedules.append("old result")

        assert model.begin_generation("new-config", 2) is True

        assert model.generated_schedules == []

    def test_clear_generated_schedules_removes_results(self, model):
        model._generated_schedules.append("old result")

        assert model.clear_generated_schedules() is True
        assert model.generated_schedules == []

    def test_clear_generated_schedules_is_rejected_while_running(self, model):
        model.begin_generation("test-config", 2)
        model._generated_schedules.append("current result")

        assert model.clear_generated_schedules() is False
        assert model.generated_schedules == ["current result"]

    def test_generation_ids_increase(self, model):
        model.begin_generation("first", 1)
        first_id = model.state_snapshot().generation_id

        model.update_state(running=False)
        model.begin_generation("second", 1)
        second_id = model.state_snapshot().generation_id

        assert second_id == first_id + 1


class TestGenerateConfiguration:
    def test_success_clears_running_state(self, model, config, patch_scheduler):
        FakeScheduler.schedules = ["schedule-a", "schedule-b"]

        model.begin_generation("test-config", config.limit)
        model.generate_configuration("test-config", config)

        state = model.state_snapshot()

        assert state.running is False
        assert state.finished is True
        assert state.error is None
        assert state.generated == 2
        assert state.valid == 2
        assert len(model.generated_schedules) == 2
        assert state.message == "Generated 2 of 2 schedules."

    def test_no_feasible_schedules_clears_running_state(self, model, config, patch_scheduler):
        FakeScheduler.schedules = []
        expected_diagnosis = {"reason": "No compatible room assignments"}
        FakeScheduler.diagnosis_result = expected_diagnosis

        model.begin_generation("test-config", config.limit)
        model.generate_configuration("test-config", config)

        state = model.state_snapshot()

        assert state.running is False
        assert state.finished is True
        assert state.error is None
        assert state.generated == 0
        assert state.diagnosis == expected_diagnosis
        assert state.message == "No valid schedules could be generated."
        assert model.generated_schedules == []

    def test_scheduler_exception_clears_running_state(self, model, config, patch_scheduler):
        FakeScheduler.schedules = RuntimeError("scheduler failed")

        model.begin_generation("test-config", config.limit)
        model.generate_configuration("test-config", config)

        state = model.state_snapshot()

        assert state.running is False
        assert state.finished is True
        assert state.error == "scheduler failed"
        assert state.message == "Schedule generation failed."

    def test_audit_exception_clears_running_state(self, model, config, patch_scheduler):
        FakeScheduler.schedules = ["schedule-a"]

        def fail_audit(self, schedule):
            raise RuntimeError("audit failed")

        FakeScheduler.audit_schedule = fail_audit

        model.begin_generation("test-config", config.limit)
        model.generate_configuration("test-config", config)

        state = model.state_snapshot()

        assert state.running is False
        assert state.finished is True
        assert state.error == "audit failed"
        assert state.message == "Schedule generation failed."

    def test_records_invalid_schedules_in_valid_count(self, model, config, patch_scheduler):
        FakeScheduler.schedules = ["schedule-a"]
        FakeScheduler.audit_valid = False

        model.begin_generation("test-config", config.limit)
        model.generate_configuration("test-config", config)

        state = model.state_snapshot()

        assert state.generated == 1
        assert state.valid == 0
        assert state.running is False
        assert state.finished is True


class TestGenerate:
    def test_configuration_load_failure_clears_running_state(self, model):
        model.begin_generation("missing-config", 2)

        def fail_load(config_name):
            raise ValueError("configuration not found")

        model.load_config = fail_load
        model.generate("missing-config", None, None)

        state = model.state_snapshot()

        assert state.running is False
        assert state.finished is True
        assert state.error == "configuration not found"
        assert state.message == "Schedule generation failed."

    def test_applies_limit_and_optimizer_overrides(
        self, model, config, patch_scheduler, monkeypatch
    ):
        FakeScheduler.schedules = ["schedule-a"]

        monkeypatch.setattr(
            model,
            "load_config",
            lambda config_name: config,
        )

        model.begin_generation("test-config", 5)
        model.generate(
            "test-config",
            5,
            ["optimizer-a"],
        )

        assert config.limit == 5
        assert config.optimizer_flags == ["optimizer-a"]
        assert model.state_snapshot().running is False
        assert model.state_snapshot().finished is True


class TestConcurrentGeneration:
    def test_only_one_concurrent_begin_succeeds(self, model):
        barrier = threading.Barrier(3)
        results = []
        results_lock = threading.Lock()

        def attempt_start(name):
            barrier.wait()
            result = model.begin_generation(name, 2)

            with results_lock:
                results.append(result)

        first = threading.Thread(
            target=attempt_start,
            args=("config-a",),
        )
        second = threading.Thread(
            target=attempt_start,
            args=("config-b",),
        )

        first.start()
        second.start()

        # Release both threads at approximately the same time.
        barrier.wait()

        first.join()
        second.join()

        assert results.count(True) == 1
        assert results.count(False) == 1
        assert model.state_snapshot().running is True
