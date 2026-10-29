import asyncio
import importlib
import sys
from types import ModuleType

import pytest
from nicegui import ElementFilter, ui
from nicegui.client import Client
from nicegui.elements.upload_files import SmallFileUpload
from nicegui.testing import UserInteraction, user_simulation

from src.controllers.configuration_controller import ConfigurationController
from src.models import configuration_repository as config_repo
from src.views import configuration_editor
from tests.conftest import active_client
from tests.test_configuration import make_valid_config


@pytest.fixture
def app_gui(monkeypatch):
    ai_assistant_stub = ModuleType("src.views.ai_assistant")
    ai_assistant_stub.__dict__["scheduler_ai_assistant"] = lambda *_args: lambda: None
    monkeypatch.setitem(sys.modules, "src.views.ai_assistant", ai_assistant_stub)
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

        class FakeRefresh:
            def __call__(self, *, saved=False):
                pass

            def is_saved(self):
                return saved["value"]

        return FakeRefresh()

    monkeypatch.setattr(app_gui, "configuration_editor", fake_configuration_editor)
    monkeypatch.setattr(app_gui, "schedule_generator", lambda: ui.label("Fake generator"))

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
            with active_client(user):
                assert next(iter(user.find(ui.tabs).elements)).value == expected_tab
                assert not dialog.value
            await user.should_see(
                "Fake configuration editor" if expected_tab == "configuration" else "Fake generator"
            )

    asyncio.run(simulate())


def test_leaving_edited_loaded_configuration_requires_confirmation(monkeypatch, tmp_path, app_gui):
    monkeypatch.setattr(Client, "on_connect", lambda _self, _handler: None)
    monkeypatch.setattr(config_repo, "CONFIG_DIR", tmp_path)
    controller = ConfigurationController()
    controller.configuration = make_valid_config()
    monkeypatch.setattr(configuration_editor, "controller", controller)
    monkeypatch.setattr(app_gui, "controller", object())
    monkeypatch.setattr(app_gui, "schedule_generator", lambda: ui.label("Fake generator"))
    monkeypatch.setattr(app_gui, "schedule_viewer", lambda: lambda: None)

    async def simulate():
        async with user_simulation(root=app_gui.build_app) as user:
            await user.open("/")
            user.find("Load configuration").click()
            await user.should_see("Load Configuration")
            with active_client(user):
                upload = next(iter(ElementFilter(kind=ui.upload)))
                config = controller.configuration
                assert config is not None
                await upload.handle_uploads(
                    [
                        SmallFileUpload(
                            "demo.json",
                            "application/json",
                            config.model_dump_json().encode(),
                        )
                    ]
                )
            await user.should_see("Editing: demo")

            user.find("Schedule Generator").click()
            assert not find_dialog_with_label(user, "Unsaved configuration").value
            user.find("Configuration Editor").click()

            user.find("Labs").click()
            with active_client(user):
                edit_button = next(
                    iter(ElementFilter(kind=ui.button, content="edit", only_visible=True))
                )
                UserInteraction(user, {edit_button}, "edit").click()
            user.find("Schedule Generator").click()
            assert not find_dialog_with_label(user, "Unsaved configuration").value
            user.find("Configuration Editor").click()

            user.find("Labs").click()
            with active_client(user):
                capacity = next(
                    iter(ElementFilter(kind=ui.number, content="Capacity", only_visible=True))
                )
                capacity.value = 35
            await user.should_see("Draft - not saved")

            user.find("Schedule Generator").click()
            assert find_dialog_with_label(user, "Unsaved configuration").value

    asyncio.run(simulate())


def find_dialog_with_label(user, label):
    with active_client(user):
        for dialog in user.find(ui.dialog).elements:
            if next(
                iter(ElementFilter(kind=ui.label, content=label).within(instance=dialog)),
                None,
            ):
                return dialog
    raise AssertionError(f"No dialog contains {label!r}.")


def click_open_dialog_button(user, label):
    with active_client(user):
        dialogs = [dialog for dialog in user.find(ui.dialog).elements if dialog.value]
        assert len(dialogs) == 1
        dialog = dialogs[0]
        buttons = set(ElementFilter(kind=ui.button, content=label).within(instance=dialog))
        assert len(buttons) == 1
        UserInteraction(user, buttons, label).click()
    return dialog
