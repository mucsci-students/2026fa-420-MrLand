import asyncio
from collections.abc import Callable
from types import SimpleNamespace
from typing import Any, cast
from unittest.mock import Mock

import pytest
from nicegui import ElementFilter, ui
from nicegui.elements.upload_files import SmallFileUpload
from nicegui.events import UploadEventArguments
from nicegui.testing import user_simulation

import src.views.schedule_viewer as viewer
from src.controllers.schedule_controller import ScheduleController
from src.controllers.schedule_generator_controller import (
    ScheduleGeneratorController,
)
from src.models.schedule_files import records_to_csv
from src.models.schedule_viewer_model import ScheduleViewerModel
from tests.conftest import active_client


@pytest.mark.parametrize("reopen", [False, True])
def test_cancel_pending_upload_preserves_schedule_and_allows_next_load(
    monkeypatch, tmp_path, reopen
):
    content = records_to_csv(
        [
            {
                "course": "CMSC 420",
                "faculty": "Dr. Smith",
                "room": "Room 101",
                "lab": "",
                "times": "MON 09:00-09:50",
            }
        ]
    )
    controller = ScheduleController(
        model=ScheduleViewerModel(directory=tmp_path),
        generator=cast(
            ScheduleGeneratorController,
            SimpleNamespace(generated_schedules=[]),
        ),
    )
    original, error = controller.load_uploaded_file("original.csv", content)
    assert error is None
    monkeypatch.setattr(viewer, "controller", controller)
    load = Mock(wraps=controller.load_uploaded_file)
    monkeypatch.setattr(controller, "load_uploaded_file", load)
    read_upload = viewer.read_upload

    async def simulate():
        started = asyncio.Event()
        release = asyncio.Event()

        async def delayed_read(event):
            started.set()
            await release.wait()
            return await read_upload(event)

        monkeypatch.setattr(viewer, "read_upload", delayed_read)
        async with user_simulation(root=viewer.schedule_viewer) as user:
            await user.open("/")
            user.find(kind=ui.button, content="Load").click()
            await user.should_see("Load Schedule")
            client = active_client(user)
            with client:
                upload = next(iter(ElementFilter(kind=ui.upload)))
                load_dialog = next(a for a in upload.ancestors() if isinstance(a, ui.dialog))
                assert load_dialog.value
                event = UploadEventArguments(
                    sender=upload,
                    client=client,
                    file=SmallFileUpload("canceled.csv", "text/csv", content),
                )
                upload_handler = cast(
                    Callable[[UploadEventArguments], Any],
                    upload._upload_handlers[0],
                )
                pending = asyncio.create_task(upload_handler(event))
            try:
                await asyncio.wait_for(started.wait(), timeout=2)
                user.find("Cancel").click()
                assert not load_dialog.value
                if reopen:
                    user.find(kind=ui.button, content="Load").click()
                    await user.should_see("Load Schedule")
                release.set()
                await asyncio.wait_for(pending, timeout=2)
            finally:
                release.set()
                if not pending.done():
                    pending.cancel()
                    await asyncio.gather(pending, return_exceptions=True)
            load.assert_not_called()
            assert controller.current is original
            assert controller.selected_index == 0
            assert len(controller.model.entries) == 1
            await user.should_not_see("Loaded canceled.csv")

            # A new upload still loads normally after canceling the previous one.
            monkeypatch.setattr(viewer, "read_upload", read_upload)
            if not reopen:
                user.find(kind=ui.button, content="Load").click()
                await user.should_see("Load Schedule")
            with active_client(user):
                await upload.handle_uploads(
                    [
                        SmallFileUpload("next.csv", "text/csv", content),
                    ]
                )
            await user.should_see("Loaded next.csv")
            load.assert_called_once_with("next.csv", content)
            assert controller.current is not None
            assert controller.current.file_name == "next.csv"
            assert controller.selected_index == 1
            assert not load_dialog.value

    asyncio.run(simulate())
