from types import SimpleNamespace

import pytest

from src.controllers.schedule_generator_controller import (
    ScheduleGeneratorController,
)
from src.models import schedule_generator_model
from src.models.schedule_generator_model import ScheduleGeneratorModel


def test_controller_passes_time_slot_overrides_to_generation(monkeypatch):
    model = ScheduleGeneratorModel()
    monkeypatch.setattr(
        model,
        "load_config",
        lambda _config_name: SimpleNamespace(limit=4),
    )
    captured = {}

    class FakeThread:
        def __init__(self, *, target, args, daemon):
            captured.update(target=target, args=args, daemon=daemon)

        def start(self):
            captured["started"] = True

    monkeypatch.setattr(
        "src.controllers.schedule_generator_controller.threading.Thread",
        FakeThread,
    )
    controller = ScheduleGeneratorController(model)

    requested, error = controller.start_generation(
        "sample",
        "",
        None,
        "20",
        "45",
    )

    assert (requested, error) == (4, None)
    assert captured["args"] == ("sample", None, None, 20, 45)
    assert captured["started"] is True


@pytest.mark.parametrize(
    ("setting", "value", "expected_error"),
    [
        ("max_time_gap_override_value", "0", "maximum time gap"),
        ("max_time_gap_override_value", "1.5", "maximum time gap"),
        ("min_time_overlap_override_value", "-5", "minimum time overlap"),
        ("min_time_overlap_override_value", "nope", "minimum time overlap"),
    ],
)
def test_controller_rejects_invalid_time_slot_overrides(
    setting, value, expected_error
):
    controller = ScheduleGeneratorController()
    overrides = {
        "max_time_gap_override_value": "",
        "min_time_overlap_override_value": "",
    }
    overrides[setting] = value

    requested, error = controller.start_generation(
        "sample",
        "",
        None,
        **overrides,
    )

    assert requested is None
    assert error == (
        f"Temporary {expected_error} must be a positive whole number."
    )


def test_model_applies_time_slot_overrides(monkeypatch):
    config = SimpleNamespace(
        limit=3,
        optimizer_flags=[],
        time_slot_config=SimpleNamespace(
            max_time_gap=30,
            min_time_overlap=45,
        ),
    )
    monkeypatch.setattr(
        ScheduleGeneratorModel,
        "load_config",
        staticmethod(lambda _config_name: config),
    )

    class EmptyScheduler:
        def __init__(self, received_config):
            assert received_config is config

        def get_models(self):
            return iter(())

        def diagnose(self):
            return None

    monkeypatch.setattr(schedule_generator_model, "Scheduler", EmptyScheduler)
    model = ScheduleGeneratorModel()

    model.generate("sample", None, None, 20, 60)

    assert config.time_slot_config.max_time_gap == 20
    assert config.time_slot_config.min_time_overlap == 60
