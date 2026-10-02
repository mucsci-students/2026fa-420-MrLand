from __future__ import annotations

from nicegui import ui

from src.controllers.configuration_controller import ConfigurationController
from src.services.config_io import ConfigLoadError
from src.services.config_service import validate_config_name
from src.views.class_patterns_gui import class_patterns_gui
from src.views.common import coming_soon, section_header
from src.views.courses_gui import courses_gui
from src.views.faculty_gui import faculty_gui
from src.views.global_settings_gui import global_settings_gui
from src.views.labs_gui import labs_gui
from src.views.rooms_gui import rooms_gui
from src.views.time_blocks_gui import time_blocks_gui

controller = ConfigurationController()

def configuration_editor() -> None:
    state = {"config": None, "name": None}

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
            ui.badge("Draft - not saved").props("color=orange")

        with ui.card().classes("w-full border border-[#29404b] bg-[#182630] p-6"):
            ui.label("Configuration pages").classes("text-lg font-semibold text-white")
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

        panel_classes = "w-full gap-4 border-t border-[#29404b] pt-6"
        config_section = getattr(config, "config", None)
        rooms_list = getattr(config_section, "rooms", []) if config_section is not None else []
        faculty_list = getattr(config_section, "faculty", []) if config_section is not None else []
        courses_list = getattr(config_section, "courses", []) if config_section is not None else []
        labs_list = getattr(config_section, "labs", []) if config_section is not None else []

        time_slot_config = getattr(config, "time_slot_config", None)
        time_blocks_list = getattr(time_slot_config, "times", {}) if time_slot_config is not None else {}
        class_patterns_list = getattr(time_slot_config, "classes", []) if time_slot_config is not None else []

        with ui.column().classes(panel_classes) as rooms_panel:
            rooms_gui(rooms_list)
        with ui.column().classes(panel_classes) as faculty_panel:
            faculty_gui(faculty_list)
        with ui.column().classes(panel_classes) as courses_panel:
            courses_gui(courses_list)
        with ui.column().classes(panel_classes) as labs_panel:
            labs_gui(labs_list)
        with ui.column().classes(panel_classes) as time_blocks_panel:
            time_blocks_gui(time_blocks_list)
        with ui.column().classes(panel_classes) as class_patterns_panel:
            class_patterns_gui(class_patterns_list)
        with ui.column().classes(panel_classes) as global_settings_panel:
            if hasattr(config, "limit") and hasattr(config, "optimizer_flags"):
                global_settings_gui(config)
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

        def show_page(action: str) -> None:
            if action not in panels:
                coming_soon(action)
                return
            for page_name, panel in panels.items():
                panel.set_visibility(page_name == action)

    def save_current_config() -> None:
        if state["config"] is None:
            ui.notify("No configuration is open to save.", type="negative")
            return
        if not state["name"]:
            ui.notify("Give the configuration a name before saving.", type="negative")
            return
        try:
            controller.save_configuration(state["name"])
        except Exception as exc:  # pragma: no cover - UI guard
            ui.notify(f"Unable to save configuration: {exc}", type="negative")
            return
        ui.notify(f"Saved '{state['name']}'.", type="positive")

    with ui.column().classes("w-full gap-6"):
        section_header(
            "Workspace",
            "Configuration Editor",
            "Edit the Schedule Configuration File",
        )



        with ui.row().classes("w-full flex-wrap gap-3"):
            ui.button(
                "Load configuration",
                icon="folder_open",
                on_click=lambda: toggle_load_select(),
            ).props("outline").classes("border-[#45616b] text-[#d8e7e8]")
            ui.button(
                "Create configuration",
                icon="add",
                on_click=lambda: start_create(),
            ).props("unelevated").classes("bg-[#75e6da] text-[#101820]")
            ui.button(
                "Save configuration",
                icon="save",
                on_click=save_current_config,
            ).props("outline").classes("border-[#45616b] text-[#d8e7e8]")

        load_select = ui.select(
            options=controller.list_names(),
            label="Select Configuration",
        ).classes("w-full max-w-xl").props("dark outlined")
        load_select.set_visibility(False)
        load_select.on_value_change(lambda e: on_select_change(e.value))

        editor_body()

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

    def start_create() -> None:
        if state["config"] is not None:
            discard_dialog.open()
        else:
            open_create_dialog()

    def open_create_dialog() -> None:
        discard_dialog.close()
        name_input.value = ""
        name_input.error = None
        create_dialog.open()

    def refresh_load_options() -> None:
        load_select.set_options(controller.list_names(), value=None)

    def toggle_load_select() -> None:
        if load_select.visible:
            load_select.set_visibility(False)
            return
        refresh_load_options()
        load_select.set_visibility(True)
        load_select.run_method("showPopup")  # opens the list right away

    def on_select_change(name: str | None) -> None:
        if not name:
            return
        if name != state["name"]:
            confirm_load(name)
        # Hide again only if the load worked (or it was already open).
        if state["name"] == name:
            load_select.set_visibility(False)
            load_select.value = None

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
        create_dialog.close()
        editor_body.refresh()
        ui.notify(f"Configuration '{name}' created. Add items, then save.", type="positive")

    def confirm_load(name: str | None) -> None:
        config_name = (name or "").strip()
        if not config_name:
            ui.notify("Pick a configuration first.", type="negative")
            return
        try:
            loaded_config = controller.load_configuration(config_name)
        except FileNotFoundError:
            ui.notify(f"Configuration '{config_name}' was not found.", type="negative")
            return
        except ConfigLoadError as exc:
            ui.notify(f"'{config_name}' is not a valid configuration: {exc}", type="negative")
            return
        except Exception as exc:  # pragma: no cover - UI guard
            ui.notify(f"Unable to load configuration: {exc}", type="negative")
            return

        state["config"] = loaded_config
        state["name"] = config_name
        editor_body.refresh()
        ui.notify(f"Loaded '{config_name}'.", type="positive")