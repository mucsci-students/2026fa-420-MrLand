from nicegui import ui

from common import coming_soon, section_header
from courses_gui import courses_gui
from faculty_gui import faculty_gui
from labs_gui import labs_gui
from rooms_gui import rooms_gui
from time_blocks_gui import time_blocks_gui


def configuration_editor() -> None:
    courses = []
    rooms = []
    faculty_members = []
    labs = []
    time_blocks = {}
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
                        on_click=lambda action=label: show_page(action),
                    ).props("outline").classes("border-[#45616b] text-[#d8e7e8]")

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

    def show_page(action: str) -> None:
        if action == "Courses":
            rooms_panel.set_visibility(False)
            faculty_panel.set_visibility(False)
            courses_panel.set_visibility(True)
            labs_panel.set_visibility(False)
            time_blocks_panel.set_visibility(False)
        elif action == "Rooms":
            rooms_panel.set_visibility(True)
            faculty_panel.set_visibility(False)
            courses_panel.set_visibility(False)
            labs_panel.set_visibility(False)
            time_blocks_panel.set_visibility(False)
        elif action == "Faculty":
            rooms_panel.set_visibility(False)
            faculty_panel.set_visibility(True)
            courses_panel.set_visibility(False)
            labs_panel.set_visibility(False)
            time_blocks_panel.set_visibility(False)
        elif action == "Labs":
            rooms_panel.set_visibility(False)
            faculty_panel.set_visibility(False)
            courses_panel.set_visibility(False)
            labs_panel.set_visibility(True)
            time_blocks_panel.set_visibility(False)
        elif action == "Time blocks":
            rooms_panel.set_visibility(False)
            faculty_panel.set_visibility(False)
            courses_panel.set_visibility(False)
            labs_panel.set_visibility(False)
            time_blocks_panel.set_visibility(True)
        else:
            coming_soon(action)