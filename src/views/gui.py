"""Builds and launches the NiceGUI scheduling application.

Used by: GUI."""

import os

from nicegui import ui

from src.views.configuration_editor import configuration_editor
from src.views.schedule_generator import schedule_generator
from src.views.schedule_viewer import schedule_viewer

BACKGROUND = "#101820"
ACCENT = "#75e6da"


def build_app() -> None:
    ui.colors(primary=ACCENT, dark=BACKGROUND)
    ui.add_head_html(
        """
        <style>
            body { background: #101820; }
            .q-tab { min-height: 56px; color: #d8e7e8 !important; text-transform: none; }
            .q-tab__label { color: #d8e7e8 !important; font-weight: 600; }
            .q-tab--active, .q-tab--active .q-tab__label { color: #75e6da !important; }
            .q-tab__indicator { background: #75e6da !important; }
            .q-field__label, .q-field__native, .q-field__input, .q-placeholder,
            .q-select__dropdown-icon, .q-table th, .q-table td,
            .q-expansion-item__toggle-icon { color: #d8e7e8 !important; }
            .configuration-panel { color: #d8e7e8; }
            .configuration-panel .q-checkbox__label { color: #d8e7e8 !important; }
            .mandatory-days .q-chip--selected { background: #d8e7e8 !important; }
            .mandatory-days .q-chip--selected .q-chip__content { color: #101820 !important; }
            .mandatory-days .q-menu .q-checkbox__bg { border-color: #45616b !important; }
            .mandatory-days .q-menu .q-checkbox__inner--truthy .q-checkbox__bg { background: #75e6da !important; border-color: #75e6da !important; }
            .mandatory-days .q-menu .q-checkbox__svg { color: #101820 !important; }
            .q-field--outlined .q-field__control:before { border-color: #45616b; }
            .q-field--outlined.q-field--focused .q-field__control:after { border-color: #75e6da; }
        </style>
        """
    )

    with ui.header().classes("border-b border-[#29404b] bg-[#101820] px-6 py-4"):
        with ui.row().classes("w-full items-center justify-between"):
            with ui.row().classes("items-center gap-3"):
                ui.icon("calendar_month", size="32px").classes("text-[#75e6da]")
                with ui.column().classes("gap-0"):
                    ui.label("Scheduler").classes("text-lg font-semibold text-white")

    with ui.column().classes("mx-auto w-full max-w-7xl gap-0 px-6 py-8"):
        tabs = ui.tabs(value="configuration").classes("w-full border-b border-[#29404b]")
        with tabs:
            ui.tab("configuration", label="Configuration Editor", icon="tune")
            ui.tab("generator", label="Schedule Generator", icon="auto_awesome")
            ui.tab("viewer", label="Schedule Viewer", icon="calendar_view_week")

        with ui.tab_panels(tabs, value="configuration").classes("w-full bg-transparent pt-8"):
            with ui.tab_panel("configuration"):
                configuration_editor()
            with ui.tab_panel("generator"):
                schedule_generator()
            with ui.tab_panel("viewer"):
                schedule_viewer()


def main() -> None:
    ui.run(
        root=build_app,
        title="MrLand Scheduler",
        reload=False,
        port=int(os.environ.get("MRLAND_GUI_PORT", "8080")),
    )


if __name__ in {"__main__", "__mp_main__"}:
    main()
