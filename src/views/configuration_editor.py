from nicegui import ui

from common import coming_soon, section_header


def configuration_editor() -> None:
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
                on_click=lambda: coming_soon("Load configuration"),
            ).props("outline").classes("border-[#45616b] text-[#d8e7e8]")
            ui.button(
                "Create configuration",
                icon="add",
                on_click=lambda: coming_soon("Create configuration"),
            ).props("unelevated").classes("bg-[#75e6da] text-[#101820]")
            ui.button(
                "Save configuration",
                icon="save",
                on_click=lambda: coming_soon("Save configuration"),
            ).props("outline").classes("border-[#45616b] text-[#d8e7e8]")

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
                        on_click=lambda action=label: coming_soon(action),
                    ).props("outline").classes("border-[#45616b] text-[#d8e7e8]")