import asyncio

import pytest
from nicegui import ElementFilter, ui
from nicegui.testing import user_simulation

import src.views.schedule_generator as schedule_generator_view
from src.controllers.schedule_generator_controller import (
    ScheduleGeneratorController,
)
from src.models.schedule_generator_model import ScheduleGeneratorModel
from tests.conftest import active_client
from tests.test_configuration import make_valid_config


def test_generation_limit_override_is_grouped_before_time_slot_settings():
    async def simulate():
        async with user_simulation(root=schedule_generator_view.schedule_generator) as user:
            await user.open("/")
            with active_client(user):
                configured_limit = next(
                    iter(
                        ElementFilter(
                            kind=ui.input,
                            content="Configured Generation Limit",
                        )
                    )
                )
                generation_override = next(
                    iter(
                        ElementFilter(
                            kind=ui.input,
                            content="Temporary Generation Limit Override",
                        )
                    )
                )
                time_slot_heading = next(
                    iter(
                        ElementFilter(
                            kind=ui.label,
                            content="Time Slot Settings",
                        )
                    )
                )

                assert configured_limit.id < generation_override.id < time_slot_heading.id

    asyncio.run(simulate())


def test_controller_passes_time_slot_overrides_to_generation(monkeypatch):
    model = ScheduleGeneratorModel()
    config = make_valid_config()
    config.limit = 4
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
        loaded_config=config,
    )

    assert (requested, error) == (4, None)
    assert captured["args"][0] == "sample"
    assert captured["args"][1].time_slot_config.max_time_gap == 20
    assert captured["args"][1].time_slot_config.min_time_overlap == 45
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
def test_controller_rejects_invalid_time_slot_overrides(setting, value, expected_error):
    controller = ScheduleGeneratorController()
    max_time_gap = value if setting == "max_time_gap_override_value" else ""
    min_time_overlap = value if setting == "min_time_overlap_override_value" else ""

    requested, error = controller.start_generation(
        "sample",
        "",
        None,
        max_time_gap_override_value=max_time_gap,
        min_time_overlap_override_value=min_time_overlap,
    )

    assert requested is None
    assert error == (f"Temporary {expected_error} must be a positive whole number.")
