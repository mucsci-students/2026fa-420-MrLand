from nicegui import ui


from src.views.class_patterns_gui import class_patterns_gui
from src.views.common import coming_soon, section_header
from src.views.courses_gui import courses_gui
from src.views.faculty_gui import faculty_gui
from src.views.global_settings_gui import global_settings_gui
from src.views.labs_gui import labs_gui
from src.views.rooms_gui import rooms_gui
from src.views.time_blocks_gui import time_blocks_gui
# from src.services.config_service import ConfigService
from src.controllers.configuration_controller import ConfigurationController

controller = ConfigurationController()

def configuration_editor() -> None:
    # The configuration currently open in the editor. None = nothing created/loaded yet.
    # The Load and Save handlers should read/write this same dict.
    state = {"config": None, "name": None}

    # ------------------------------------------------------------------
    # Editor body: rebuilt whenever a configuration is created or loaded,
    # so every panel is bound to the *current* config's lists.
    # ------------------------------------------------------------------
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

        with ui.column().classes(panel_classes) as rooms_panel:
            rooms_gui(config.config.rooms)
        with ui.column().classes(panel_classes) as faculty_panel:
            faculty_gui(config.config.faculty)
        with ui.column().classes(panel_classes) as courses_panel:
            courses_gui(config.config.courses)
        with ui.column().classes(panel_classes) as labs_panel:
            labs_gui(config.config.labs)
        with ui.column().classes(panel_classes) as time_blocks_panel:
            time_blocks_gui(config.time_slot_config.times)
        with ui.column().classes(panel_classes) as class_patterns_panel:
            class_patterns_gui(config.time_slot_config.classes)
        with ui.column().classes(panel_classes) as global_settings_panel:
            global_settings_gui(config)

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

    # ------------------------------------------------------------------
    # Page layout
    # ------------------------------------------------------------------
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
                on_click=controller.load_configuration,
            ).props("outline").classes("border-[#45616b] text-[#d8e7e8]")
            ui.button(
                "Create configuration",
                icon="add",
                on_click=lambda: start_create(),
            ).props("unelevated").classes("bg-[#75e6da] text-[#101820]")
            ui.button(
                "Save configuration",
                icon="save",
                on_click=controller.save_configuration,
            ).props("outline").classes("border-[#45616b] text-[#d8e7e8]")

        editor_body()

    # ------------------------------------------------------------------
    # Dialogs
    # ------------------------------------------------------------------
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

        with ui.column().classes("w-full gap-4 border-t border-[#29404b] pt-6") as rooms_panel:
            rooms_panel.set_visibility(False)
            rooms_gui(rooms)

        with ui.column().classes("w-full gap-4 border-t border-[#29404b] pt-6") as faculty_panel:
            faculty_panel.set_visibility(False)
            faculty_gui(faculty_members)

        with ui.column().classes("w-full gap-4 border-t border-[#29404b] pt-6") as courses_panel:
            courses_panel.set_visibility(False)
            courses_gui(courses)

        with ui.column().classes("w-full gap-4 border-t border-[#29404b] pt-6") as labs_panel:
            labs_panel.set_visibility(False)
            labs_gui(labs)

        with ui.column().classes("w-full gap-4 border-t border-[#29404b] pt-6") as time_blocks_panel:
            time_blocks_panel.set_visibility(False)
            time_blocks_gui(time_blocks)

        with ui.column().classes("w-full gap-4 border-t border-[#29404b] pt-6") as class_patterns_panel:
            class_patterns_panel.set_visibility(False)
            class_patterns_gui(class_patterns)

        with ui.column().classes("w-full gap-4 border-t border-[#29404b] pt-6") as global_settings_panel:
            global_settings_panel.set_visibility(False)
            # global_settings_gui(settings_config)

    panels = {
        "Courses": courses_panel,
        "Faculty": faculty_panel,
        "Rooms": rooms_panel,
        "Labs": labs_panel,
        "Time blocks": time_blocks_panel,
        "Class patterns": class_patterns_panel,
        "Global settings": global_settings_panel,
    }

    def show_page(action: str) -> None:
        if action not in panels:
            coming_soon(action)
    # ------------------------------------------------------------------
    # Create flow
    # ------------------------------------------------------------------
    def start_create() -> None:
        # Nothing open yet -> go straight to the name prompt.
        # Something open -> confirm first so we never silently discard work.
        if state["config"] is not None:
            discard_dialog.open()
        else:
            open_create_dialog()

    def open_create_dialog() -> None:
        discard_dialog.close()
        name_input.value = ""
        name_input.error = None
        create_dialog.open()

    def confirm_create() -> None:
        try:
            name = validate_config_name(name_input.value or "")
        except ValueError as exc:
            name_input.error = str(exc)  # red message under the field; dialog stays open
            return

        # Only replace the current config once the name is valid,
        # so Cancel at any point leaves the existing config untouched.
        state["config"] = create_draft_config()
        state["name"] = name
        create_dialog.close()
        editor_body.refresh()
        ui.notify(
            f"Configuration '{name}' created. Add items, then validate and save.",
            type="positive",
        )