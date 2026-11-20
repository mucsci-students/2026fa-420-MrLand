import asyncio
import io
from types import SimpleNamespace
from typing import cast

import pytest
from nicegui import ElementFilter, ui
from nicegui.testing import user_simulation
from pypdf import PdfReader
from scheduler.models.course import CourseInstance

import src.views.schedule_viewer as viewer
from src.controllers.schedule_controller import ScheduleController
from src.controllers.schedule_generator_controller import ScheduleGeneratorController
from src.models.schedule_result import ScheduleResult
from src.models.schedule_viewer_model import ScheduleViewerModel
from tests.conftest import active_client


@pytest.mark.parametrize("update_method", ["sync_generated", "set_generated"])
def test_print_dialog_keeps_schedule_until_reopened(monkeypatch, tmp_path, update_method):
    def result(name):
        return ScheduleResult(
            config_name=name,
            schedule=[
                cast(
                    CourseInstance,
                    SimpleNamespace(
                        course=f"{name}101",
                        faculty=f"Dr. {name}",
                        room=f"Room {name}",
                        lab=None,
                        time="MON 09:00-09:50",
                    ),
                )
            ],
        )

    generator = SimpleNamespace(generated_schedules=[result("Original")])
    controller = ScheduleController(
        model=ScheduleViewerModel(directory=tmp_path),
        generator=cast(ScheduleGeneratorController, generator),
    )
    monkeypatch.setattr(viewer, "controller", controller)

    async def simulate():
        async with user_simulation(root=viewer.schedule_viewer) as user:
            await user.open("/")
            original = controller.current
            assert original is not None
            user.find(kind=ui.button, content="Print / Export PDF").click()
            await user.should_see(f"Selected schedule: {original.label}")

            generator.generated_schedules = [result("Replacement")]
            with active_client(user):
                if update_method == "sync_generated":
                    assert controller.sync_generated()
                else:
                    assert controller.model.set_generated(generator.generated_schedules)
                assert controller.current is not original
                orientation = next(
                    e for e in ElementFilter(kind=ui.select) if e.label == "Group by"
                )
                group = next(
                    e for e in ElementFilter(kind=ui.select) if e.label == "Resource or faculty"
                )
                orientation.value = "faculty"
            await user.should_see(f"Selected schedule: {original.label}")
            with active_client(user):
                assert isinstance(group.options, dict)
                assert "Dr. Original" in group.options.values()
                assert "Dr. Replacement" not in group.options.values()
                group.value = next(k for k, v in group.options.items() if v == "Dr. Original")
            user.find(kind=ui.button, content="Download PDF").click()
            await user.should_see("Downloaded")
            download = await user.download.next()
            assert download.status_code == 200
            assert download.content.startswith(b"%PDF-")
            content = "\n".join(
                page.extract_text() for page in PdfReader(io.BytesIO(download.content)).pages
            )
            assert "Original101" in content
            assert "Replacement101" not in content

            user.find(kind=ui.button, content="Print / Export PDF").click()
            current = controller.current
            assert current is not None
            await user.should_see(f"Selected schedule: {current.label}")

            with active_client(user):
                orientation = next(
                    e for e in ElementFilter(kind=ui.select) if e.label == "Group by"
                )
                group = next(
                    e for e in ElementFilter(kind=ui.select) if e.label == "Resource or faculty"
                )

                orientation.value = "resource"

                assert isinstance(group.options, dict)
                assert "Room: Room Replacement" in group.options.values()
                assert "Room: Room Original" not in group.options.values()

    asyncio.run(simulate())
