import asyncio
import json

import pytest
from nicegui import ElementFilter, ui
from nicegui.testing import UserInteraction, user_simulation

import src.views.configuration_editor as editor
from src.controllers.configuration_controller import ConfigurationController
from src.models import configuration_repository as config_repo
from tests.test_configuration import make_valid_config


@pytest.fixture
def editor_controller(monkeypatch, tmp_path):
    monkeypatch.setattr(config_repo, "CONFIG_DIR", tmp_path)
    test_controller = ConfigurationController()
    test_controller.configuration = make_valid_config()
    test_controller._has_valid_configuration = True
    test_controller.save_configuration("demo")
    monkeypatch.setattr(editor, "controller", test_controller)
    monkeypatch.setattr(test_controller, "list_names", lambda: ["demo"])
    return test_controller


def run_editor_simulation(action):
    refresh_callbacks = []

    def root():
        refresh = editor.configuration_editor(lambda: None)
        refresh_callbacks.append(refresh)

    async def simulate():
        async with user_simulation(root=root) as user:
            await user.open("/")
            await action(user, refresh_callbacks[0])

    asyncio.run(simulate())


async def load_demo_config(user, mark_unsaved=None):
    user.find("Load configuration").click()
    await user.should_see("Select Configuration")
    user.find(kind=ui.select, content="Select Configuration").click()
    user.find("demo").click()
    await user.should_see("Loaded 'demo'.")
    if mark_unsaved is not None:
        mark_unsaved()
        await user.should_see("Draft - not saved")


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


def find_dialog_with_label(user, label):
    with user.client:
        for dialog in user.find(ui.dialog).elements:
            labels = ElementFilter(kind=ui.label, content=label).within(instance=dialog)
            if next(iter(labels), None) is not None:
                return dialog
    raise AssertionError(f"No dialog contains {label!r}.")


def test_load_prompts_for_unsaved_changes_and_cancel_keeps_draft(editor_controller):
    async def action(user, mark_unsaved):
        await load_demo_config(user, mark_unsaved)
        user.find("Load configuration").click()
        await user.should_see("Unsaved changes")
        dialog = click_open_dialog_button(user, "Cancel")
        await asyncio.sleep(0.1)
        assert not dialog.value
        await user.should_see("Draft - not saved")
        await user.should_not_see("Select Configuration")

    run_editor_simulation(action)


def test_load_without_edits_opens_selector_without_warning(editor_controller):
    async def action(user, _mark_unsaved):
        await load_demo_config(user)
        user.find("Load configuration").click()
        await user.should_see("Select Configuration")
        assert not find_dialog_with_label(user, "Unsaved changes").value

    run_editor_simulation(action)


def test_discard_and_load_opens_selector_without_saving(editor_controller, monkeypatch):
    def unexpected_local_save(*args, **kwargs):
        raise AssertionError("Discard and Load must not save the config locally.")

    monkeypatch.setattr(editor_controller, "save_configuration", unexpected_local_save)

    async def action(user, mark_unsaved):
        await load_demo_config(user, mark_unsaved)
        user.find("Load configuration").click()
        await user.should_see("Unsaved changes")
        dialog = click_open_dialog_button(user, "Discard and Load")
        await user.should_see("Select Configuration")
        assert not dialog.value

    run_editor_simulation(action)


def test_save_and_load_downloads_json_then_opens_selector(editor_controller, monkeypatch):
    def unexpected_local_save(*args, **kwargs):
        raise AssertionError("Popup Save must download instead of saving locally.")

    monkeypatch.setattr(editor_controller, "save_configuration", unexpected_local_save)

    async def action(user, mark_unsaved):
        await load_demo_config(user, mark_unsaved)
        user.find("Load configuration").click()
        await user.should_see("Unsaved changes")
        dialog = click_open_dialog_button(user, "Save Configuration")

        download = await user.download.next()
        assert not dialog.value
        assert download.status_code == 200
        assert json.loads(download.content) == editor_controller.configuration.model_dump(
            mode="json"
        )
        await user.should_see("Select Configuration")
        await user.should_see("Downloading 'demo.json'")

    run_editor_simulation(action)
