"""NiceGUI configuration editor for creating, loading, and editing configurations.

Used by: GUI."""

from __future__ import annotations

from collections.abc import Callable

from nicegui import ui

from src.controllers.configuration_controller import (
    ConfigurationController,
    ConfigurationMemento,
)
from src.models.configuration_repository import ConfigLoadError
from src.controllers.configuration_controller import ConfigurationController
from src.models.configuration_model import ConfigValidationError, validate_config_name
from src.models.configuration_repository import ConfigLoadError
from src.views.class_patterns_gui import class_patterns_gui
from src.views.common import coming_soon, section_header
from src.views.courses_gui import courses_gui
from src.views.faculty_gui import faculty_gui
from src.views.global_settings_gui import global_settings_gui
from src.views.labs_gui import labs_gui
from src.views.rooms_gui import rooms_gui
from src.views.time_blocks_gui import time_blocks_gui


controller = ConfigurationController()
PANEL_COMBINATION = ("Rooms", "Time blocks", "Faculty", "Faculty")


class ConfigurationEditorRefresh:
    """Refresh the editor while exposing whether its current draft is saved."""

    def __init__(
        self,
        refresh: Callable[..., None],
        is_saved: Callable[[], bool],
    ) -> None:
        self._refresh = refresh
        self.is_saved = is_saved

    def __call__(self, *, saved: bool = False) -> None:
        self._refresh(saved=saved)


# Return the uploaded file name and contents.
async def read_upload(event) -> tuple[str, bytes]:
    if hasattr(event, "file"):  # NiceGUI 3.x
        return event.file.name, await event.file.read()
    return event.name, event.content.read()  # NiceGUI 2.x


def configuration_editor(
    on_unlock: Callable[[], None],
) -> ConfigurationEditorRefresh:
    """Build the editor workspace and coordinate configuration lifecycle actions."""
    # Keep the selected draft and save state shared by the editor callbacks.
    state = {
        "config": None,
        "name": None,
        "saved": False,
        "status_badge": None,
        "undo_button": None,
        "redo_button": None,
        "combination_progress": 0,
        "combination_unlocked": False,
        "flush_pending_settings": lambda: True,
    }
    load_generation = 0
    undo_history: list[ConfigurationMemento] = []
    redo_history: list[ConfigurationMemento] = []
    
    # Update the saved indicator after a draft change or successful save.
    def set_saved_status(saved: bool) -> None:
        state["saved"] = saved
        badge = state["status_badge"]
        if badge is not None:
            badge.set_text("Draft saved" if saved else "Draft - not saved")
            badge.props(f"color={'green' if saved else 'orange'}")

    def update_history_buttons() -> None:
        undo_button = state["undo_button"]
        if undo_button is not None:
            undo_enabled = bool(undo_history) and state["config"] is not None
            undo_button.set_enabled(undo_enabled)
            if undo_enabled:
                undo_button.classes(
                    add="border-[#45616b] text-[#d8e7e8]",
                    remove="border-gray-700 text-gray-500 bg-gray-800",
                )
            else:
                undo_button.classes(
                    add="border-gray-700 text-gray-500 bg-gray-800",
                    remove="border-[#45616b] text-[#d8e7e8]",
                )
                undo_button.style("opacity: 0.3 !important; filter: grayscale(1);")
            if undo_enabled:
                undo_button.style(remove="opacity: 0.3 !important; filter: grayscale(1);")
        redo_button = state["redo_button"]
        if redo_button is not None:
            redo_enabled = bool(redo_history) and state["config"] is not None
            redo_button.set_enabled(redo_enabled)
            if redo_enabled:
                redo_button.classes(
                    add="border-[#45616b] text-[#d8e7e8]",
                    remove="border-gray-700 text-gray-500 bg-gray-800",
                )
            else:
                redo_button.classes(
                    add="border-gray-700 text-gray-500 bg-gray-800",
                    remove="border-[#45616b] text-[#d8e7e8]",
                )
                redo_button.style("opacity: 0.3 !important; filter: grayscale(1);")
            if redo_enabled:
                redo_button.style(remove="opacity: 0.3 !important; filter: grayscale(1);")

    def clear_history() -> None:
        undo_history.clear()
        redo_history.clear()
        update_history_buttons()

    # Apply edits through model validation and restore rejected changes.
    def apply_config_change(mutation) -> bool:
        try:
            previous_state = controller.create_memento()
            accepted, problems = controller.apply_change(mutation)
        except Exception as exc:
            state["config"] = controller.configuration
            editor_body.refresh()
            ui.notify(f"Change was not applied: {exc}", type="negative")
            return False

        if not accepted:
            state["config"] = controller.configuration
            editor_body.refresh()
            show_problems("Change rejected", problems, restored=True)
            return False
        undo_history.append(previous_state)
        redo_history.clear()
        update_history_buttons()
        set_saved_status(False)
        if problems:
            show_problems("Draft validation", problems)
        return True

    def undo_last_change() -> None:
        if not undo_history or state["config"] is None:
            return
        try:
            current_state = controller.create_memento()
            controller.restore_memento(undo_history[-1])
        except Exception as exc:
            ui.notify(f"Unable to undo change: {exc}", type="negative")
            return
        undo_history.pop()
        redo_history.append(current_state)
        state["config"] = controller.configuration
        set_saved_status(False)
        update_history_buttons()
        editor_body.refresh()

    def redo_last_change() -> None:
        if not redo_history or state["config"] is None:
            return
        try:
            current_state = controller.create_memento()
            controller.restore_memento(redo_history[-1])
        except Exception as exc:
            ui.notify(f"Unable to redo change: {exc}", type="negative")
            return
        redo_history.pop()
        undo_history.append(current_state)
        state["config"] = controller.configuration
        set_saved_status(False)
        update_history_buttons()
        editor_body.refresh()

    # Render the current configuration and its category-specific editors.
    @ui.refreshable
    def editor_body() -> None:
        config = state["config"]

        if config is None:
            with ui.card().classes(
                "w-full items-center border border-dashed border-[#45616b] bg-[#182630] p-10"
            ):
                ui.icon("note_add", size="48px").classes("text-[#75e6da]")
                ui.label("No configuration loaded").classes("text-lg font-semibold text-white")
                ui.label(
                    "Create a new configuration or load an existing one to get started."
                ).classes("text-sm text-[#9fb2b8]")
            return

        with ui.row().classes("items-center gap-3"):
            ui.label(f"Editing: {state['name']}").classes("text-xl font-semibold text-white")
            state["status_badge"] = ui.badge(
                "Draft saved" if state["saved"] else "Draft - not saved"
            ).props(
                f"color={'green' if state['saved'] else 'orange'} "
                "id=configuration-draft-status"
            )

        current_problems = controller.validate_configuration()
        with ui.card().classes("w-full border border-[#29404b] bg-[#182630] p-4"):
            if not current_problems:
                ui.label("Configuration is valid.").classes("text-green-400")
            else:
                ui.label(
                    f"Draft has {len(current_problems)} validation problem(s). "
                    "Edits are checked against the complete configuration."
                ).classes("font-semibold text-amber-300")
                for problem in current_problems:
                    prefix = f"{problem.item}: " if problem.item else ""
                    ui.label(
                        f"{problem.area} — {prefix}{problem.message}"
                    ).classes("break-words text-sm text-[#d8e7e8]")

        with ui.card().classes("w-full border border-[#29404b] bg-[#182630] p-6"):
            with ui.row().classes("w-full items-center justify-between gap-3"):
                ui.label("Configuration pages").classes(
                    "text-lg font-semibold text-white"
                )
                with ui.row().classes("items-center gap-2"):
                    state["undo_button"] = ui.button(
                        "Undo",
                        icon="undo",
                        on_click=undo_last_change,
                    ).props("outline").classes("border-[#45616b] text-[#d8e7e8]")
                    state["redo_button"] = ui.button(
                        "Redo",
                        icon="redo",
                        on_click=redo_last_change,
                    ).props("outline").classes("border-[#45616b] text-[#d8e7e8]")
                    update_history_buttons()
            ui.label("Select an item to add/modify/delete objects to/from configuration.").classes(
                "text-sm text-[#9fb2b8]"
            )

            with ui.row().classes("mt-6 w-full flex-wrap gap-3"):
                for label, icon in (
                    ("Courses", "menu_book"),
                    ("Faculty", "person"),
                    ("Rooms", "meeting_room"),
                    ("Labs", "science"),
                    ("Time blocks", "schedule"),
                    ("Class patterns", "view_timeline"),
                    ("Global settings", "tune"),
                ):
                    ui.button(
                        label,
                        icon=icon,
                        on_click=lambda action=label: show_page(action),
                    ).props("outline").classes("border-[#45616b] text-[#d8e7e8]")

        panel_classes = "configuration-panel w-full gap-4 border-t border-[#29404b] pt-6"
        config_section = getattr(config, "config", None)
        rooms_list = getattr(config_section, "rooms", []) if config_section is not None else []
        faculty_list = getattr(config_section, "faculty", []) if config_section is not None else []
        courses_list = getattr(config_section, "courses", []) if config_section is not None else []
        labs_list = getattr(config_section, "labs", []) if config_section is not None else []

        time_slot_config = getattr(config, "time_slot_config", None)
        time_blocks_list = getattr(time_slot_config, "times", {}) if time_slot_config is not None else {}
        class_patterns_list = getattr(time_slot_config, "classes", []) if time_slot_config is not None else []

        with ui.column().classes(panel_classes) as rooms_panel:
            rooms_gui(rooms_list, on_change=apply_config_change)
        with ui.column().classes(panel_classes) as faculty_panel:
            faculty_gui(faculty_list, on_change=apply_config_change)
        with ui.column().classes(panel_classes) as courses_panel:
            courses_gui(courses_list, on_change=apply_config_change)
        with ui.column().classes(panel_classes) as labs_panel:
            labs_gui(labs_list, on_change=apply_config_change)
        with ui.column().classes(panel_classes) as time_blocks_panel:
            time_blocks_gui(time_blocks_list, on_change=apply_config_change)
        with ui.column().classes(panel_classes) as class_patterns_panel:
            class_patterns_gui(class_patterns_list, on_change=apply_config_change)
        with ui.column().classes(panel_classes) as global_settings_panel:
            if hasattr(config, "limit") and hasattr(config, "optimizer_flags"):
                state["flush_pending_settings"] = global_settings_gui(
                    config,
                    on_change=apply_config_change,
                    on_pending_change=lambda: set_saved_status(False),
                )
            else:
                ui.label("Global settings are unavailable for this draft.").classes(
                    "text-sm text-[#9fb2b8]"
                )

        panels = {
            "Courses": courses_panel,
            "Faculty": faculty_panel,
            "Rooms": rooms_panel,
            "Labs": labs_panel,
            "Time blocks": time_blocks_panel,
            "Class patterns": class_patterns_panel,
            "Global settings": global_settings_panel,
        }
        for panel in panels.values():
            panel.set_visibility(False)

        # Display the selected category panel or announce unavailable actions.
        def show_page(action: str) -> None:
            if action not in panels:
                coming_soon(action)
                return
            for page_name, panel in panels.items():
                panel.set_visibility(page_name == action)

    # Download the active draft through the browser.
            if state["combination_unlocked"]:
                return
            if action == PANEL_COMBINATION[state["combination_progress"]]:
                state["combination_progress"] += 1
            else:
                state["combination_progress"] = int(action == PANEL_COMBINATION[0])

            if state["combination_progress"] == len(PANEL_COMBINATION):
                state["combination_unlocked"] = True
                on_unlock()

    # Download the active draft and report validation or browser errors.
    def download_configuration(file_name: str) -> str:
        content, file_name, media_type = controller.export_configuration(file_name)
        ui.download(content, filename=file_name, media_type=media_type)
        set_saved_status(True)
        return file_name

    def save_current_config() -> None:
        if state["config"] is None:
            ui.notify("No configuration is open to save.", type="negative")
            return
        if not state["name"]:
            ui.notify("Give the configuration a name before saving.", type="negative")
            return
        if not state["flush_pending_settings"]():
            return
        file_name = (save_name.value or "").strip()
        if not file_name:
            save_status.set_text("Enter a file name.")
            return
        if "/" in file_name or "\\" in file_name:
            save_status.set_text("Enter a file name without a folder path.")
            return
        try:
            file_name = download_configuration(file_name)
        except ConfigValidationError as exc:
            show_problems("Can't save yet", exc.problems)
            return
        except ValueError as exc:
            save_status.set_text(str(exc))
            return
        except Exception as exc:  # pragma: no cover - UI guard
            ui.notify(f"Unable to save configuration: {exc}", type="negative")
            return

        save_dialog.close()
        ui.notify(
            f"Downloading '{file_name}'.",
            type="positive",
        )

    with ui.column().classes("w-full gap-6"):
        section_header(
            "Workspace",
            "Configuration Editor",
            "Edit the Schedule Configuration File",
        )

        # dialog for saving a config
        with ui.dialog() as save_dialog:
            with ui.card().classes(
                "border border-[#29404b] bg-[#182630] w-[480px] gap-3"
            ):
                ui.label("Save Configuration").classes(
                    "text-lg font-semibold text-white"
                )
                ui.label(
                    "A copy will be downloaded to your browser's default location. " \
                    "Check your browser settings to manually choose the save location."
                ).classes("text-sm text-[#9fb2b8]")
                save_name = ui.input("File Name").props("outlined dark").classes("w-full")
                save_status = ui.label("").classes("text-sm text-red-400")
                with ui.row().classes("w-full justify-end gap-2"):
                    ui.button("Cancel", on_click=save_dialog.close).props("flat")
                    ui.button(
                        "Save",
                        icon="download",
                        on_click=save_current_config,
                    ).props("unelevated").classes("bg-[#75e6da] text-[#101820]")
        
        # Upload a configuration file from the user's computer.
        async def handle_config_upload(event) -> None:
            generation = load_generation
            if not load_dialog.value:
                return
            try:
                file_name, content = await read_upload(event)
                if generation != load_generation or not load_dialog.value:
                    return

                if not file_name.lower().endswith(".json"):
                    ui.notify("Please select a .json file.", type="negative")
                    return

                loaded_config = controller.load_uploaded_configuration(content)

                state["config"] = loaded_config
                state["name"] = file_name[:-5]
                clear_history()
                set_saved_status(False)
                editor_body.refresh()

                load_dialog.close()
                ui.notify(f"Loaded '{file_name}'.", type="positive")

            except ConfigValidationError as exc:
                show_problems("Invalid configuration file", exc.problems)
            except (ValueError, ConfigLoadError) as exc:
                ui.notify(f"Unable to load configuration: {exc}", type="negative")
            except Exception as exc:
                ui.notify(f"Unable to load configuration: {exc}", type="negative")
            finally:
                if generation == load_generation:
                    config_upload.reset()

        # Dialog for uploading a configuration from the user's computer.
        with ui.dialog() as load_dialog:
            with ui.card().classes(
                "w-[480px] max-w-full border border-[#29404b] bg-[#182630] gap-4"
            ):
                ui.label("Load Configuration").classes(
                    "text-lg font-semibold text-white"
                )
                ui.label(
                    "Select a JSON configuration file from your computer."
                ).classes("text-sm text-[#9fb2b8]")

                config_upload = ui.upload(
                    label="Choose configuration file",
                    auto_upload=True,
                    on_upload=handle_config_upload,
                    max_files=1,
                ).props("accept=.json").classes("w-full")

                with ui.row().classes("w-full justify-end"):
                    ui.button(
                        "Cancel",
                        on_click=lambda: cancel_load(),
                    ).props("flat")

        def open_load_dialog() -> None:
            nonlocal load_generation
            load_generation += 1
            config_upload.reset()
            load_dialog.open()

        def open_save_dialog() -> None:
            if state["config"] is None:
                ui.notify("No configuration is open to save.", type="negative")
                return
            if not state["name"]:
                ui.notify("Give the configuration a name before saving.", type="negative")
                return
            save_name.value = f"{state['name']}.json"
            save_status.set_text("")
            save_dialog.open()

        # Workspace actions for loading, creating, saving, and validating configs.
        with ui.row().classes("w-full flex-wrap gap-3"):
            ui.button(
                "Load configuration",
                icon="folder_open",
                on_click=lambda: request_load_upload(),
            ).props("outline").classes("bg-[#75e6da] text-[#101820]")
            ui.button(
                "Create configuration",
                icon="add",
                on_click=lambda: start_create(),
            ).props("unelevated").classes("bg-[#75e6da] text-[#101820]")
            ui.button(
                "Save configuration",
                icon="save",
                on_click=open_save_dialog,
            ).props("outline").classes("border-[#45616b] text-[#d8e7e8]")
            ui.button(
                "Validate configuration",
                icon="fact_check",
                on_click=lambda: validate_current_config(),
            ).props("outline").classes("border-[#45616b] text-[#d8e7e8]")

        editor_body()

    # Confirm before replacing an open draft with a new configuration.
    with ui.dialog() as discard_dialog, ui.card().classes("border border-[#29404b] bg-[#182630]"):
        ui.label("Start a new configuration?").classes("text-lg font-semibold text-white")
        ui.label(
            "Any unsaved changes to the current configuration will be lost."
        ).classes("text-sm text-[#9fb2b8]")
        with ui.row().classes("mt-4 w-full justify-end gap-2"):
            ui.button("Keep editing", on_click=discard_dialog.close).props("flat")
            ui.button("Continue", on_click=lambda: open_create_dialog()).props(
                "unelevated color=negative"
            )

    with ui.dialog() as unsaved_load_dialog, ui.card().classes(
        "border border-[#29404b] bg-[#182630]"
    ):
        ui.label("Unsaved changes").classes("text-lg font-semibold text-white")
        ui.label(
            "Loading another configuration will overwrite your work unless you save it."
        ).classes("text-sm text-[#9fb2b8]")
        with ui.row().classes("mt-4 w-full justify-end gap-2"):
            ui.button("Cancel", on_click=lambda: cancel_load()).props("flat")
            ui.button("Save Configuration", on_click=lambda: save_and_load()).props(
                "unelevated"
            ).classes("bg-[#75e6da] text-[#101820]")
            ui.button(
                "Discard and Load",
                on_click=lambda: discard_and_load(),
            ).props("unelevated color=negative")

    # Collect and validate the name for a newly created configuration.
    with ui.dialog() as create_dialog, ui.card().classes("border border-[#29404b] bg-[#182630]"):
        ui.label("Create new configuration").classes("text-lg font-semibold text-white")
        name_input = ui.input(
            "Configuration name", placeholder="fall_2026"
        ).props("autofocus").classes("w-80")
        name_input.on("keydown.enter", lambda: confirm_create())
        with ui.row().classes("mt-4 w-full justify-end gap-2"):
            ui.button("Cancel", on_click=create_dialog.close).props("flat")
            ui.button("Create", on_click=lambda: confirm_create()).props("unelevated").classes(
                "bg-[#75e6da] text-[#101820]"
            )

    # Open the create flow, asking before discarding an existing draft.
    def start_create() -> None:
        if state["config"] is not None:
            discard_dialog.open()
        else:
            open_create_dialog()

    # Reset the name input and open the new-configuration dialog.
    def open_create_dialog() -> None:
        discard_dialog.close()
        name_input.value = ""
        name_input.error = None
        create_dialog.open()

    # Protect an edited draft before opening the configuration upload dialog.
    def request_load_upload() -> None:
        if state["config"] is not None and not state["saved"]:
            unsaved_load_dialog.open()
            return
        open_load_dialog()

    def cancel_load() -> None:
        nonlocal load_generation
        load_generation += 1
        config_upload.reset()
        load_dialog.close()
        unsaved_load_dialog.close()

    def discard_and_load() -> None:
        unsaved_load_dialog.close()
        open_load_dialog()

    def save_and_load() -> None:
        config_name = state["name"]
        if state["config"] is None or not config_name:
            ui.notify("No named configuration is open to save.", type="negative")
            return
        if not state["flush_pending_settings"]():
            return
        try:
            file_name = download_configuration(f"{config_name}.json")
        except ConfigValidationError as exc:
            show_problems("Can't save yet", exc.problems)
            return
        except ValueError as exc:
            ui.notify(str(exc), type="negative")
            return
        except Exception as exc:  # pragma: no cover - UI guard
            ui.notify(f"Unable to save configuration: {exc}", type="negative")
            return

        unsaved_load_dialog.close()
        ui.notify(
            f"Downloading '{file_name}'.",
            type="positive",
        )
        discard_and_load()

    # Validate the requested name, create a draft, and refresh the editor.
    def confirm_create() -> None:
        try:
            name = validate_config_name(name_input.value or "")
        except ValueError as exc:
            name_input.error = str(exc)
            return
        try:
            config = controller.new_configuration()
        except Exception as exc:  # pragma: no cover - UI guard
            ui.notify(f"Unable to create configuration: {exc}", type="negative")
            return

        state["config"] = config
        state["name"] = name
        clear_history()
        set_saved_status(False)
        create_dialog.close()
        editor_body.refresh()
        ui.notify(f"Configuration '{name}' created. Add items, then save.", type="positive")

    # Dialog surface used to display validation results and rejected edits.
    with ui.dialog() as validate_dialog, ui.card().classes(
        "min-w-[28rem] max-w-2xl border border-[#29404b] bg-[#182630]"
    ):
        validate_title = ui.label().classes("text-lg font-semibold text-white")
        validate_results = ui.column().classes("w-full gap-3")
        with ui.row().classes("mt-4 w-full justify-end"):
            ui.button("Close", on_click=validate_dialog.close).props("flat")

    # Group configuration problems by area and explain any rollback behavior.
    def show_problems(title: str, problems, *, restored: bool = False) -> None:
        validate_title.set_text(title)
        validate_results.clear()
        with validate_results:
            if not problems:
                with ui.row().classes("items-center gap-2"):
                    ui.icon("check_circle", size="28px").classes("text-green-400")
                    ui.label("Valid configuration. It's ready to save.").classes("text-[#d8e7e8]")
            else:
                ui.label(
                    f"Found {len(problems)} problem(s). "
                    + (
                        "The invalid change was rolled back."
                        if restored
                        else "The incomplete draft is retained; fix these issues before saving."
                    )
                ).classes("text-sm text-[#9fb2b8]")
                by_area: dict[str, list] = {}
                for problem in problems:
                    by_area.setdefault(problem.area, []).append(problem)
                for area, area_problems in by_area.items():
                    ui.label(area).classes("mt-2 font-semibold text-[#75e6da]")
                    for problem in area_problems:
                        prefix = f"{problem.item}: " if problem.item else ""
                        ui.label(f"• {prefix}{problem.message}").classes(
                            "break-words text-sm text-[#d8e7e8]"
                        )
        validate_dialog.open()

    # Validate the active draft and display its current problems.
    def validate_current_config() -> None:
        if state["config"] is None:
            ui.notify("Create or load a configuration first.", type="warning")
            return
        try:
            problems = controller.validate_configuration()
        except Exception as exc:  # pragma: no cover - UI guard
            ui.notify(f"Unable to validate configuration: {exc}", type="negative")
            return
        show_problems("Validate configuration", problems)

    def refresh_after_ai_change(*, saved: bool = False) -> None:
        state["config"] = controller.configuration
        set_saved_status(saved)
        editor_body.refresh()

    return ConfigurationEditorRefresh(
        refresh_after_ai_change,
        lambda: state["config"] is None or bool(state["saved"]),
    )
