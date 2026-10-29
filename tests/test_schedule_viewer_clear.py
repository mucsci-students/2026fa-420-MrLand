import asyncio
from types import SimpleNamespace
from typing import cast

from nicegui import ElementFilter, ui
from nicegui.testing import user_simulation
from scheduler.models.course import CourseInstance

import src.views.schedule_viewer as viewer
from src.controllers.schedule_controller import ScheduleController
from src.controllers.schedule_generator_controller import (
    ScheduleGeneratorController,
)
from src.models.schedule_files import records_to_csv
from src.models.schedule_generator_model import ScheduleGeneratorModel
from src.models.schedule_result import ScheduleResult
from src.models.schedule_viewer_model import ScheduleViewerModel
from tests.conftest import active_client


def test_clear_generated_results_preserves_uploaded_schedules(
    monkeypatch, tmp_path
):
    generator_model = ScheduleGeneratorModel()
    generator_model._generated_schedules.append(
        ScheduleResult(
            config_name="generated",
            schedule=[
                cast(CourseInstance, SimpleNamespace(
                    course="CS101",
                    faculty="Dr. Smith",
                    room="Room 101",
                    lab=None,
                    time="MON 09:00-09:50",
                ))
            ],
        )
    )
    controller = ScheduleController(
        model=ScheduleViewerModel(directory=tmp_path),
        generator=ScheduleGeneratorController(generator_model),
    )
    entry, error = controller.load_uploaded_file(
        "imported.csv",
        records_to_csv(
            [
                {
                    "course": "CS202",
                    "faculty": "Dr. Jones",
                    "room": "Room 202",
                    "lab": "",
                    "times": "TUE 10:00-10:50",
                }
            ]
        ),
    )
    assert error is None
    monkeypatch.setattr(viewer, "controller", controller)

    async def simulate():
        async with user_simulation(root=viewer.schedule_viewer) as user:
            await user.open("/")
            with active_client(user):
                clear_button = next(
                    iter(
                        ElementFilter(
                            kind=ui.button,
                            content="Clear Generated Results",
                        )
                    )
                )
                assert clear_button.enabled

            user.find("Clear Generated Results").click()
            await user.should_see("Generated results cleared.")

            assert generator_model.generated_schedules == []
            assert controller.has_generated_schedules is False
            assert controller.current is entry
            assert controller.current is not None
            assert controller.current.file_name == "imported.csv"
            with active_client(user):
                assert not clear_button.enabled

    asyncio.run(simulate())
