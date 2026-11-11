
"""Main Schedule Analysis page."""

from collections.abc import Callable

from nicegui import ui

from src.controllers.schedule_controller import schedule_controller
from src.views.schedule_analysis.statistics_tab import build_statistics_tab
from src.views.schedule_analysis.comparison_tab import build_comparison_tab
from src.views.schedule_analysis.what_if_tab import build_what_if_tab


async def read_upload(event) -> tuple[str, bytes]:
    """Read an uploaded schedule file (NiceGUI 2.x and 3.x)."""
    if hasattr(event, "file"):
        return event.file.name, await event.file.read()

    return event.name, event.content.read()


def schedule_analysis() -> Callable[[], None]:
    """Build the main Schedule Analysis page."""

    schedule_controller.sync_generated()

    # ---------------------------------------------------------
    # Theme-aware styling
    # ---------------------------------------------------------

    ui.add_head_html("""
        <style>
            /* Analysis tabs */
            .schedule-analysis .q-tabs {
                background: var(--surface) !important;
                color: var(--text-muted) !important;
                border: 1px solid var(--border-color);
                border-radius: 12px;
                padding: 4px;
            }

            .schedule-analysis .q-tab {
                color: var(--text-muted) !important;
                border-radius: 9px;
                transition: background 0.2s ease, color 0.2s ease;
            }

            .schedule-analysis .q-tab--active {
                color: var(--text-primary) !important;
                background: var(--surface-hover) !important;
            }

            .schedule-analysis .q-tab__indicator {
                background: var(--accent-color) !important;
            }

            .schedule-analysis .q-tab-panels {
                background: transparent !important;
                color: var(--app-foreground) !important;
            }

            /* Load dialog */
            .schedule-analysis-dialog .q-uploader {
                background: var(--surface-raised) !important;
                color: var(--text-primary) !important;
                border: 1px solid var(--border-color);
            }

            .schedule-analysis-dialog .q-uploader__header {
                background: var(--surface-hover) !important;
                color: var(--text-primary) !important;
            }

            .schedule-analysis-dialog .q-uploader__list {
                color: var(--text-primary) !important;
            }

            .schedule-analysis-dialog .q-field__control {
                background: var(--surface-raised);
            }
        </style>
    """)

    load_generation = 0

    with ui.column().classes(
        "schedule-analysis w-full min-h-screen gap-5"
    ):

        # ---------------------------------------------------------
        # Page heading
        # ---------------------------------------------------------

        with ui.row().classes("w-full items-center justify-between"):
            with ui.column().classes("gap-1"):
                ui.label("Schedule Analysis").classes(
                    "text-2xl font-semibold"
                ).style("color: var(--text-primary)")

                ui.label(
                    "Analyze, compare, and evaluate generated schedules."
                ).classes("text-sm").style("color: var(--text-muted)")

        # ---------------------------------------------------------
        # Schedule controls
        # ---------------------------------------------------------

        with ui.row().classes("w-full items-center gap-3 flex-wrap"):

            schedule_select = ui.select(
                schedule_controller.schedule_options(),
                value=schedule_controller.selected_index
                if schedule_controller.has_schedules
                else None,
                label="Selected Schedule",
            ).classes("min-w-[250px]")

            load_button = ui.button(
                "Load Schedule",
                icon="upload_file",
            ).props("outline")

            refresh_button = ui.button(
                "Refresh",
                icon="refresh",
            ).props("outline")

        empty_state = ui.label(
            "No schedules available. Generate a schedule or load one."
        ).classes("text-sm").style("color: var(--text-muted)")

        # ---------------------------------------------------------
        # Load Schedule dialog
        # ---------------------------------------------------------

        with (
            ui.dialog() as load_dialog,
            ui.card()
            .classes(
                "w-[480px] max-w-full gap-3 schedule-analysis-dialog"
            )
            .style(
                "background: var(--surface); "
                "color: var(--app-foreground); "
                "border: 1px solid var(--border-color); "
                "border-radius: 14px; "
                "box-shadow: 0 12px 32px rgba(0, 0, 0, 0.2);"
            ),
        ):
            ui.label("Load Schedule").classes(
                "text-lg font-semibold"
            ).style("color: var(--text-primary)")

            ui.label(
                "Upload a CSV or JSON schedule from your computer."
            ).classes("text-sm").style("color: var(--text-muted)")

            load_status = ui.label("").classes("text-sm")

            upload = ui.upload(
                label="Choose schedule file",
                auto_upload=True,
                max_files=1,
            ).props("accept=.csv,.json flat bordered").classes("w-full")

            with ui.row().classes("w-full justify-end"):
                ui.button(
                    "Cancel",
                    on_click=lambda: cancel_load(),
                ).props("flat")

        # ---------------------------------------------------------
        # Analysis tabs
        # ---------------------------------------------------------

        with ui.tabs() as analysis_tabs:
            statistics_tab = ui.tab("Statistics", icon="bar_chart")
            comparison_tab = ui.tab("Schedule Comparison", icon="compare")
            what_if_tab = ui.tab("What-If Analysis", icon="tune")

        with ui.tab_panels(
            analysis_tabs,
            value=statistics_tab,
        ).classes("w-full bg-transparent"):

            with ui.tab_panel(statistics_tab):
                unscheduled_card = build_statistics_tab()

            with ui.tab_panel(comparison_tab):
                build_comparison_tab()

            with ui.tab_panel(what_if_tab):
                build_what_if_tab()

    # ---------------------------------------------------------
    # Page behavior
    # ---------------------------------------------------------

    def refresh() -> None:
        """Refresh the available schedules."""
        schedule_controller.sync_generated()

        options = schedule_controller.schedule_options()
        schedule_select.options = options


        if options:
            schedule_select.value = schedule_controller.selected_index
            empty_state.set_visibility(False)
        else:
            schedule_select.value = None
            empty_state.set_visibility(True)

        current = schedule_controller.current

        unscheduled_card.set_visibility(
            bool(current and current.source == "generated")
        )

        schedule_select.update()

    def on_schedule_change(event) -> None:
        if event.value is None:
            return

        schedule_controller.select(event.value)
        refresh()

    def open_load_dialog() -> None:
        nonlocal load_generation

        load_generation += 1
        load_status.text = ""
        upload.reset()
        load_dialog.open()

    def cancel_load() -> None:
        nonlocal load_generation

        load_generation += 1
        upload.reset()
        load_dialog.close()

    def finish_load(entry, error) -> None:
        if error:
            load_status.text = error
            return

        load_dialog.close()
        refresh()

        ui.notify(
            f"Loaded {entry.file_name} ({len(entry.records)} sections)",
            type="positive",
        )

    async def on_upload(event) -> None:
        generation = load_generation

        if not load_dialog.value:
            return

        file_name, content = await read_upload(event)

        if generation != load_generation or not load_dialog.value:
            return

        upload.reset()

        finish_load(
            *schedule_controller.load_uploaded_file(file_name, content)
        )

    schedule_select.on_value_change(on_schedule_change)
    load_button.on_click(open_load_dialog)
    refresh_button.on_click(refresh)
    upload.on_upload(on_upload)

    refresh()

    return refresh
