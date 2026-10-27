import asyncio
import json
from unittest.mock import Mock

import pytest
from nicegui import ElementFilter, ui
from nicegui.elements.upload_files import SmallFileUpload
from nicegui.events import UploadEventArguments
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


async def load_demo_config(user, controller, mark_unsaved=None):
    content = controller.configuration.model_dump_json().encode()
    user.find("Load configuration").click()
    await user.should_see("Load Configuration")
    await upload_config(user, "demo.json", content)
    await user.should_see("Editing: demo")
    user.find("Save configuration").click()
    await user.should_see("Save Configuration")
    click_open_dialog_button(user, "Save")
    download = await user.download.next()
    assert download.status_code == 200
    if mark_unsaved is not None:
        mark_unsaved()
        await user.should_see("Draft - not saved")


async def upload_config(user, file_name, content):
    with user.client:
        upload = next(iter(ElementFilter(kind=ui.upload)))
        await upload.handle_uploads([SmallFileUpload(file_name, "application/json", content)])


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
        await load_demo_config(user, editor_controller, mark_unsaved)
        user.find("Load configuration").click()
        await user.should_see("Unsaved changes")
        dialog = click_open_dialog_button(user, "Cancel")
        await asyncio.sleep(0.1)
        assert not dialog.value
        await user.should_see("Draft - not saved")
        await user.should_not_see("Select Configuration")

    run_editor_simulation(action)


def test_load_without_edits_opens_upload_without_warning(editor_controller):
    async def action(user, _mark_unsaved):
        user.find("Load configuration").click()
        await user.should_see("Load Configuration")
        assert not find_dialog_with_label(user, "Unsaved changes").value
        await user.should_not_see("Select Configuration")

    run_editor_simulation(action)


def test_discard_and_load_opens_upload_without_saving(editor_controller, monkeypatch):
    def unexpected_local_save(*args, **kwargs):
        raise AssertionError("Discard and Load must not save the config locally.")

    monkeypatch.setattr(editor_controller, "save_configuration", unexpected_local_save)

    async def action(user, mark_unsaved):
        await load_demo_config(user, editor_controller, mark_unsaved)
        user.find("Load configuration").click()
        await user.should_see("Unsaved changes")
        dialog = click_open_dialog_button(user, "Discard and Load")
        await user.should_see("Load Configuration")
        assert not dialog.value

    run_editor_simulation(action)


def test_save_and_load_downloads_json_then_opens_upload(editor_controller, monkeypatch):
    def unexpected_local_save(*args, **kwargs):
        raise AssertionError("Popup Save must download instead of saving locally.")

    monkeypatch.setattr(editor_controller, "save_configuration", unexpected_local_save)

    async def action(user, mark_unsaved):
        await load_demo_config(user, editor_controller, mark_unsaved)
        user.find("Load configuration").click()
        await user.should_see("Unsaved changes")
        dialog = click_open_dialog_button(user, "Save Configuration")

        download = await user.download.next()
        assert not dialog.value
        assert download.status_code == 200
        assert json.loads(download.content) == editor_controller.configuration.model_dump(
            mode="json"
        )
        await user.should_see("Load Configuration")
        await user.should_see("Downloading 'demo.json'")

    run_editor_simulation(action)


@pytest.mark.parametrize("suffix", ["json", "JSON", "JsOn"])
def test_uploaded_name_strips_json_suffix_before_saving(editor_controller, monkeypatch, suffix):
    content = editor_controller.configuration.model_dump_json().encode()
    export = Mock(wraps=editor_controller.export_configuration)
    monkeypatch.setattr(editor_controller, "export_configuration", export)

    async def action(user, _mark_unsaved):
        user.find("Load configuration").click()
        await user.should_see("Load Configuration")
        await upload_config(user, f"plan.final.{suffix}", content)
        await user.should_see("Editing: plan.final")
        expected = editor_controller.configuration.model_dump(mode="json")
        user.find("Save configuration").click()
        await user.should_see("Save Configuration")
        click_open_dialog_button(user, "Save")
        download = await user.download.next()
        assert download.status_code == 200
        export.assert_called_once_with("plan.final.json")
        assert json.loads(download.content) == expected

    run_editor_simulation(action)


@pytest.mark.parametrize("file_name, content", [("bad.json", b"{"), ("bad.txt", b"{}")])
def test_failed_upload_resets_control_and_allows_retry(
    editor_controller, monkeypatch, file_name, content
):
    valid_content = editor_controller.configuration.model_dump_json().encode()

    async def action(user, _mark_unsaved):
        await load_demo_config(user, editor_controller)
        draft = editor_controller.configuration
        with user.client:
            upload = next(iter(ElementFilter(kind=ui.upload)))
        reset = Mock(wraps=upload.reset)
        monkeypatch.setattr(upload, "reset", reset)
        user.find("Load configuration").click()
        await user.should_see("Load Configuration")
        reset.assert_called_once_with()
        await upload_config(user, file_name, content)
        await user.should_see(
            "Please select a .json file." if file_name.endswith(".txt")
            else "Unable to load configuration"
        )
        assert reset.call_count == 2
        assert find_dialog_with_label(user, "Load Configuration").value
        assert editor_controller.configuration is draft
        await upload_config(user, "retry.json", valid_content)
        await user.should_see("Editing: retry")
        assert reset.call_count == 3
        user.find("Load configuration").click()
        await user.should_see("Unsaved changes")
        click_open_dialog_button(user, "Discard and Load")
        await user.should_see("Load Configuration")
        assert reset.call_count == 4

    run_editor_simulation(action)


@pytest.mark.parametrize("choice", ["Cancel", "Discard and Load", "Save Configuration"])
def test_uploaded_draft_requires_confirmation_before_replacement(editor_controller, choice):
    content = editor_controller.configuration.model_dump_json().encode()

    async def action(user, _mark_unsaved):
        user.find("Load configuration").click()
        await user.should_see("Load Configuration")
        await upload_config(user, "draft.json", content)
        await user.should_see("Editing: draft")
        draft = editor_controller.configuration
        user.find("Load configuration").click()
        await user.should_see("Unsaved changes")
        assert not find_dialog_with_label(user, "Load Configuration").value
        assert editor_controller.configuration is draft
        click_open_dialog_button(user, choice)
        if choice == "Cancel":
            assert not find_dialog_with_label(user, "Load Configuration").value
            assert editor_controller.configuration is draft
            await user.should_see("Editing: draft")
            return
        if choice == "Save Configuration":
            download = await user.download.next()
            assert json.loads(download.content) == json.loads(content)
        await user.should_see("Load Configuration")
        await upload_config(user, "replacement.json", content)
        await user.should_see("Editing: replacement")
        assert editor_controller.configuration is not draft

    run_editor_simulation(action)


def test_canceling_upload_prevents_late_configuration_replacement(
    editor_controller, monkeypatch
):
    content = editor_controller.configuration.model_dump_json().encode()
    original_config = editor_controller.configuration
    read_upload = editor.read_upload

    async def simulate():
        started = asyncio.Event()
        release = asyncio.Event()

        async def delayed_read(event):
            started.set()
            await release.wait()
            return await read_upload(event)

        monkeypatch.setattr(editor, "read_upload", delayed_read)
        async with user_simulation(root=lambda: editor.configuration_editor(lambda: None)) as user:
            await user.open("/")
            user.find("Load configuration").click()
            await user.should_see("Load Configuration")
            with user.client:
                upload = next(iter(ElementFilter(kind=ui.upload)))
                load_dialog = next(
                    ancestor for ancestor in upload.ancestors()
                    if isinstance(ancestor, ui.dialog)
                )
                event = UploadEventArguments(
                    sender=upload,
                    client=user.client,
                    file=SmallFileUpload("late.json", "application/json", content),
                )
                pending = asyncio.create_task(
                    upload._upload_handlers[0](event)
                )
            try:
                await asyncio.wait_for(started.wait(), timeout=2)
                click_open_dialog_button(user, "Cancel")
                assert not load_dialog.value
                release.set()
                await asyncio.wait_for(pending, timeout=2)
            finally:
                release.set()
                if not pending.done():
                    pending.cancel()
                    await asyncio.gather(pending, return_exceptions=True)

            assert editor_controller.configuration is original_config
            await user.should_not_see("Loaded 'late'.")

    asyncio.run(simulate())
