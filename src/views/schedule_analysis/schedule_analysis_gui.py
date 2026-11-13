"""Main Schedule Analysis page."""

from nicegui import ui

from src.controllers.schedule_controller import schedule_controller
from src.views.schedule_analysis.comparison_tab import build_comparison_tab
from src.views.schedule_analysis.statistics_tab import build_statistics_tab
from src.views.schedule_analysis.what_if_tab import build_what_if_tab


class ScheduleAnalysisRefresh:
    """Refresh analysis data and expose the What-If navigation guard."""

    def __init__(self, refresh, what_if_tab) -> None:
        self._refresh = refresh
        self.what_if_tab = what_if_tab

    def __call__(self) -> None:
        self._refresh()

    def has_unsaved_what_if_changes(self) -> bool:
        return self.what_if_tab.has_unsaved_changes()

    def discard_what_if_changes(self) -> None:
        self.what_if_tab.discard_changes()


async def read_upload(event) -> tuple[str, bytes]:
    """Read an uploaded schedule file (NiceGUI 2.x and 3.x)."""
    if hasattr(event, "file"):
        return event.file.name, await event.file.read()

    return event.name, event.content.read()


def schedule_analysis() -> ScheduleAnalysisRefresh:
    """Build the main Schedule Analysis page."""

    schedule_controller.sync_generated()

    # ---------------------------------------------------------
    # Custom styling
    # ---------------------------------------------------------

    ui.add_head_html("""
        <style>
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

            .analysis-tabs {
                background: transparent;
                color: var(--text-muted);
            }

            .analysis-tabs .q-tab {
                color: var(--text-muted);
                font-weight: 500;
                min-height: 42px;
            }

            .analysis-tabs .q-tab--active {
                color: var(--text-primary);
            }

            .analysis-tabs .q-tab__indicator {
                background: var(--accent-color);
                height: 2px;
            }
        </style>
    """)

    load_generation = 0
    load_target = None

    # ---------------------------------------------------------
    # Page behaviors
    # ---------------------------------------------------------

    def refresh() -> None:
        """Refresh the shared schedule list and update every selector."""
        schedule_controller.sync_generated()

        refresh_statistics()
        refresh_comparison()
        what_if_tab.refresh_sources()
        what_if_tab.refresh_original_schedule()

        current = schedule_controller.current

        unscheduled_card.set_visibility(bool(current and current.source == "generated"))

    def open_load_dialog(target_select=None) -> None:
        """Open the shared upload dialog for the requested selector."""
        nonlocal load_generation, load_target

        load_generation += 1
        load_target = target_select

        load_status.text = ""
        upload.reset()
        load_dialog.open()

    def cancel_load() -> None:
        """Cancel an upload and invalidate any pending upload callback."""
        nonlocal load_generation, load_target

        load_generation += 1
        load_target = None

        upload.reset()
        load_dialog.close()

    def on_schedule_loaded(entry, error) -> None:
        """Handle the result of an uploaded schedule."""
        if error:
            load_status.text = error
            return

        refresh()

        # If the upload came from a Comparison selector, select the
        # newly loaded schedule in that selector.
        if load_target is not None:
            options = schedule_controller.schedule_options()
            if options:
                load_target.options = options
                load_target.value = max(options)
                load_target.update()

        load_dialog.close()

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

        on_schedule_loaded(*schedule_controller.load_uploaded_file(file_name, content))

    # ---------------------------------------------------------
    # Page layout
    # ---------------------------------------------------------

    with ui.column().classes("schedule-analysis w-full min-h-screen gap-5"):
        # Page heading
        with ui.column().classes("w-full gap-1"):
            ui.label("Schedule Analysis").classes("text-2xl font-semibold").style(
                "color: var(--text-primary)"
            )

            ui.label("Analyze, compare, and evaluate generated schedules.").classes(
                "text-sm"
            ).style("color: var(--text-muted)")

        # -----------------------------------------------------
        # Load Schedule dialog
        # -----------------------------------------------------

        with (
            ui.dialog() as load_dialog,
            ui.card()
            .classes("w-[480px] max-w-full gap-3 schedule-analysis-dialog")
            .style(
                "background: var(--surface); "
                "color: var(--app-foreground); "
                "border: 1px solid var(--border-color); "
                "border-radius: 14px; "
                "box-shadow: 0 12px 32px rgba(0, 0, 0, 0.2);"
            ),
        ):
            ui.label("Load Schedule").classes("text-lg font-semibold").style(
                "color: var(--text-primary)"
            )

            ui.label("Upload a CSV or JSON schedule from your computer.").classes("text-sm").style(
                "color: var(--text-muted)"
            )

            load_status = ui.label("").classes("text-sm")

            upload = (
                ui.upload(
                    label="Choose schedule file",
                    auto_upload=True,
                    max_files=1,
                )
                .props("accept=.csv,.json flat bordered")
                .classes("w-full")
            )

            with ui.row().classes("w-full justify-end"):
                ui.button(
                    "Cancel",
                    on_click=lambda: cancel_load(),
                ).props("flat")

        # -----------------------------------------------------
        # Analysis tabs and global refresh button
        # -----------------------------------------------------

        with ui.row().classes("w-full items-center justify-between"):
            # Analysis tabs
            with ui.tabs().props("dense no-caps").classes("analysis-tabs") as analysis_tabs:
                ui.tab("statistics", label="Statistics")
                ui.tab("comparison", label="Schedule Comparison")
                ui.tab("what-if", label="What-If Analysis")

            # Refresh button
            refresh_button = (
                ui.button(
                    "Refresh",
                    icon="refresh",
                    on_click=refresh,
                )
                .props("outline")
                .style("color: var(--text-muted)")
            )

        # -----------------------------------------------------
        # Tab panels
        # -----------------------------------------------------

        with ui.tab_panels(
            analysis_tabs,
            value="statistics",
        ).classes("w-full"):
            with ui.tab_panel("statistics"):
                unscheduled_card, refresh_statistics = build_statistics_tab(
                    on_load_schedule=open_load_dialog
                )

            with ui.tab_panel("comparison"):
                refresh_comparison = build_comparison_tab(on_load_schedule=open_load_dialog)

            with ui.tab_panel("what-if"):
                what_if_tab = build_what_if_tab()

        active_analysis_tab = {"value": "statistics"}
        pending_analysis_tab = {"value": None}

        with (
            ui.dialog() as what_if_leave_dialog,
            ui.card().classes("border border-[#29404b] bg-[#182630]"),
        ):
            ui.label("Unsaved What-If Changes").classes("text-lg font-semibold text-white")
            ui.label("What-If changes will be lost if you leave. Continue?").classes(
                "text-sm text-[#9fb2b8]"
            )
            with ui.row().classes("mt-4 w-full justify-end gap-2"):
                ui.button(
                    "Stay",
                    on_click=lambda: stay_in_what_if(),
                ).props("flat")
                ui.button(
                    "Leave and discard",
                    on_click=lambda: leave_what_if(),
                ).props("unelevated color=negative")

        def stay_in_what_if() -> None:
            pending_analysis_tab["value"] = None
            what_if_leave_dialog.close()
            analysis_tabs.value = "what-if"
            active_analysis_tab["value"] = "what-if"

        def leave_what_if() -> None:
            next_tab = pending_analysis_tab["value"]
            pending_analysis_tab["value"] = None
            what_if_leave_dialog.close()
            what_if_tab.discard_changes()
            if next_tab is not None:
                active_analysis_tab["value"] = next_tab
                analysis_tabs.value = next_tab

        def on_analysis_tab_change(event) -> None:
            next_tab = event.value
            if next_tab == active_analysis_tab["value"]:
                return
            if active_analysis_tab["value"] == "what-if" and what_if_tab.has_unsaved_changes():
                pending_analysis_tab["value"] = next_tab
                analysis_tabs.value = "what-if"
                what_if_leave_dialog.open()
                return
            active_analysis_tab["value"] = next_tab

        analysis_tabs.on_value_change(on_analysis_tab_change)

    refresh_button.on_click(refresh)
    upload.on_upload(on_upload)

    refresh()

    return ScheduleAnalysisRefresh(refresh, what_if_tab)
