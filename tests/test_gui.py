import asyncio
import importlib
import sys
from types import ModuleType

import pytest
from nicegui import ElementFilter, ui
from nicegui.client import Client
from nicegui.testing import UserInteraction, user_simulation


@pytest.fixture
def app_gui(monkeypatch):
    ai_assistant_stub = ModuleType("src.views.ai_assistant")
    ai_assistant_stub.scheduler_ai_assistant = lambda *_args: lambda: None
    monkeypatch.setitem(
        sys.modules, "src.views.ai_assistant", ai_assistant_stub
    )
    return importlib.import_module("src.views.gui")


@pytest.mark.parametrize(
    ("choice", "expected_tab"),
    [
        ("Stay in Configuration", "configuration"),
        ("Leave without saving", "generator"),
    ],
)
def test_leaving_configuration_tab_requires_confirmation(
    monkeypatch, app_gui, choice, expected_tab
):
    saved = {"value": False}
    monkeypatch.setattr(Client, "on_connect", lambda _self, _handler: None)

    def fake_configuration_editor(_on_unlock):
        ui.label("Fake configuration editor")

        def refresh(*, saved_status=False):
            pass

        refresh.is_saved = lambda: saved["value"]
        return refresh

    monkeypatch.setattr(
        app_gui, "configuration_editor", fake_configuration_editor
    )
    monkeypatch.setattr(
        app_gui, "schedule_generator", lambda: ui.label("Fake generator")
    )

    def fake_schedule_viewer():
        ui.label("Fake viewer")
        return lambda: None

    monkeypatch.setattr(app_gui, "schedule_viewer", fake_schedule_viewer)
    monkeypatch.setattr(
        app_gui,
        "scheduler_ai_assistant",
        lambda *_args: lambda: None,
    )
    monkeypatch.setattr(app_gui, "controller", object())

    async def simulate():
        async with user_simulation(root=app_gui.build_app) as user:
            await user.open("/")

            user.find("Schedule Generator").click()
            await user.should_see("Unsaved configuration")
            dialog = click_open_dialog_button(user, choice)
            with user.client:
                assert (
                    next(iter(user.find(ui.tabs).elements)).value
                    == expected_tab
                )
                assert not dialog.value
            await user.should_see(
                "Fake configuration editor"
                if expected_tab == "configuration"
                else "Fake generator"
            )

    asyncio.run(simulate())


def click_open_dialog_button(user, label):
    with user.client:
        dialogs = [dialog for dialog in user.find(ui.dialog).elements if dialog.value]
        assert len(dialogs) == 1
        dialog = dialogs[0]
        buttons = set(
            ElementFilter(kind=ui.button, content=label).within(instance=dialog)
        )
        assert len(buttons) == 1
        UserInteraction(user, buttons, label).click()
    return dialog
