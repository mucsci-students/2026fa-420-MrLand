"""Skeleton layout for the Schedule Analysis workspace.

The page intentionally contains presentation placeholders only. Analysis logic,
charts, comparison behavior, and What-If workflows will be added incrementally.

Primary Author: Dylan Groff
Used by: GUI.
"""

from collections.abc import Callable

from nicegui import ui

from src.controllers.schedule_controller import schedule_controller


DAYS = ("MON", "TUE", "WED", "THU", "FRI")


def _surface_card(title: str, subtitle: str | None = None):
    """Create a floating, theme-aware panel used throughout this page."""
    card = ui.card().classes("w-full min-w-0 gap-3 p-5")
    card.style(
        "background: var(--surface); "
        "color: var(--app-foreground); "
        "border: 1px solid var(--border-color); "
        "border-radius: 14px; "
        "box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);"
    )

    with card:
        ui.label(title).classes("text-lg font-semibold").style(
            "color: var(--text-primary)"
        )

        if subtitle:
            ui.label(subtitle).classes("text-sm").style(
                "color: var(--text-muted)"
            )

    return card


def _placeholder(message: str = "Analysis details will appear here.") -> None:
    """Show a consistent placeholder without implying that data is calculated."""
    with ui.column().classes(
        "w-full min-h-24 items-center justify-center gap-2 py-5"
    ):
        ui.icon("insights", size="28px").style(
            "color: var(--accent-color)"
        )
        ui.label(message).classes("text-sm text-center").style(
            "color: var(--text-muted)"
        )


def _placeholder_table(headers: list[str], rows: int = 3) -> None:
    """Draw a lightweight table skeleton for planned analysis data."""
    with ui.column().classes("w-full gap-2"):
        with ui.row().classes(
            "w-full items-center gap-2 rounded-lg px-3 py-2"
        ).style(
            "background: var(--surface-raised); "
            "border: 1px solid var(--border-color)"
        ):
            for header in headers:
                ui.label(header).classes(
                    "flex-1 text-xs font-semibold"
                ).style("color: var(--text-muted)")

        for _ in range(rows):
            with ui.row().classes(
                "w-full items-center gap-2 rounded-lg px-3 py-3"
            ).style(
                "border: 1px solid var(--border-color); "
                "background: var(--surface)"
            ):
                for _header in headers:
                    ui.element("div").classes(
                        "h-2 flex-1 rounded-full"
                    ).style(
                        "background: var(--surface-hover); "
                        "max-width: 100px"
                    )


def schedule_analysis() -> Callable[[], None]:
    """Build the Schedule Analysis page and return its refresh callback.

    Only the page layout and existing schedule selection are wired at this
    stage. Analysis features are deliberately left as placeholders so they
    can be implemented and tested one user story at a time.
    """
    schedule_controller.sync_generated()

    with ui.column().classes("w-full gap-6 schedule-analysis"):
        # Page heading and existing schedule selector.
        with ui.row().classes(
            "w-full items-center justify-between flex-wrap gap-4"
        ):
            with ui.column().classes("gap-1"):
                ui.label("Schedule Analysis").classes(
                    "text-2xl font-semibold"
                ).style("color: var(--text-primary)")

                ui.label(
                    "Explore schedule quality, workload, and resource utilization."
                ).style("color: var(--text-muted)")

            with ui.row().classes("items-center flex-wrap gap-2"):
                schedule_select = ui.select(
                    {}, label="Selected Schedule", value=None
                ).classes("min-w-[260px]").props("outlined")

                refresh_button = ui.button(
                    "Refresh", icon="refresh"
                ).props("outline")

        # Displayed when no generated or uploaded schedules are available.
        empty_state = ui.column().classes(
            "w-full items-center gap-3 py-10"
        )

        with empty_state:
            ui.icon("calendar_month", size="42px").style(
                "color: var(--accent-color)"
            )

            ui.label("No schedules available yet").classes(
                "text-lg font-semibold"
            ).style("color: var(--text-primary)")

            ui.label(
                "Generate a schedule or load a CSV/JSON file in Schedule Viewer."
            ).style("color: var(--text-muted)")

        content = ui.column().classes("w-full gap-5")

        with content:
            # Schedule score and ranked schedule panels.
            with ui.grid(columns=2).classes("w-full gap-4"):
                with _surface_card(
                    "Schedule Quality Score",
                    "A summary score and transparent breakdown of the selected schedule.",
                ):
                    with ui.row().classes("items-end gap-2"):
                        ui.label("—").classes(
                            "text-5xl font-bold"
                        ).style("color: var(--accent-color)")

                        ui.label("/ 100").classes(
                            "text-lg pb-1"
                        ).style("color: var(--text-muted)")

                    _placeholder("Score breakdown will be added here.")

                with _surface_card(
                    "Top 5 Schedules",
                    "Compare the highest-ranked schedules of the selected source type.",
                ):
                    _placeholder_table(
                        ["Rank", "Schedule", "Score"], rows=4
                    )

            # Faculty workload panel.
            with _surface_card(
                "Faculty Workload Analysis",
                "Compare teaching assignments, hours, daily workload, and consecutive periods.",
            ):
                _placeholder_table(
                    [
                        "Faculty",
                        "Courses",
                        "Teaching Hours",
                        "Daily Hours",
                        "Longest Span",
                    ]
                )

            # Room and lab utilization panels.
            with ui.grid(columns=2).classes("w-full gap-4"):
                with _surface_card(
                    "Room Utilization",
                    "View room usage by weekday and identify unused capacity.",
                ):
                    _placeholder(
                        "Room utilization heatmap will be added here."
                    )
                    _placeholder_table(
                        ["Room", "Used Hours", "Utilization"]
                    )

                with _surface_card(
                    "Lab Utilization",
                    "View lab usage separately from regular classroom usage.",
                ):
                    _placeholder(
                        "Lab utilization heatmap will be added here."
                    )
                    _placeholder_table(
                        ["Lab", "Used Hours", "Utilization"]
                    )

            # Distribution panels.
            with ui.grid(columns=2).classes("w-full gap-4"):
                with _surface_card(
                    "Class Distribution",
                    "See how courses are distributed across the weekdays.",
                ):
                    _placeholder(
                        "Courses-per-day chart will be added here."
                    )

                with _surface_card(
                    "Faculty Distribution",
                    "See how faculty assignments are distributed across the week.",
                ):
                    _placeholder(
                        "Faculty-per-day chart will be added here."
                    )

            # This section is only part of the generated-schedule experience.
            unscheduled_card = ui.column().classes("w-full")

            with unscheduled_card:
                with _surface_card(
                    "Unscheduled Courses",
                    "Courses from the source configuration that were not placed in the generated schedule.",
                ):
                    _placeholder(
                        "Unscheduled course list and details will be added here."
                    )

            # Comparison workspace: visual structure only for now.
            with ui.expansion(
                "Compare Schedules", icon="compare_arrows"
            ).classes("w-full"):
                ui.label(
                    "Choose two schedules to compare their calendars and statistics."
                ).classes("text-sm").style("color: var(--text-muted)")

                with ui.row().classes(
                    "w-full items-center flex-wrap gap-3"
                ):
                    ui.select(
                        {}, label="Schedule 1"
                    ).classes("min-w-[230px]").props("outlined")

                    ui.select(
                        {}, label="Schedule 2"
                    ).classes("min-w-[230px]").props("outlined")

                    ui.button(
                        "Upload Schedule", icon="upload_file"
                    ).props("outline disable")

                with ui.tabs().classes("w-full") as compare_tabs:
                    ui.tab(
                        "calendars",
                        label="Side-by-Side Calendars",
                        icon="calendar_month",
                    )
                    ui.tab(
                        "statistics",
                        label="Statistics",
                        icon="bar_chart",
                    )

                with ui.tab_panels(
                    compare_tabs, value="calendars"
                ).classes("w-full"):
                    with ui.tab_panel("calendars"):
                        with ui.row().classes(
                            "w-full flex-wrap gap-3"
                        ):
                            ui.select(
                                ["Course", "Faculty", "Room / Lab"],
                                label="Filter Type",
                            ).classes("min-w-[170px]").props("outlined")

                            ui.select(
                                [], label="Filter Value"
                            ).classes("min-w-[200px]").props(
                                "outlined clearable disable"
                            )

                            ui.select(
                                {
                                    None: "All Days",
                                    **{day: day for day in DAYS},
                                },
                                value=None,
                                label="Day",
                            ).classes("min-w-[150px]").props("outlined")

                        with ui.grid(columns=2).classes("w-full gap-4"):
                            with _surface_card("Schedule 1 Calendar"):
                                _placeholder(
                                    "First schedule calendar will appear here."
                                )

                            with _surface_card("Schedule 2 Calendar"):
                                _placeholder(
                                    "Second schedule calendar will appear here."
                                )

                    with ui.tab_panel("statistics"):
                        with _surface_card(
                            "Schedule Comparison Statistics"
                        ):
                            _placeholder_table(
                                [
                                    "Metric",
                                    "Schedule 1",
                                    "Schedule 2",
                                ],
                                rows=6,
                            )

            # What-If workspace: placeholder only; no temporary config is changed.
            with ui.expansion(
                "What-If Analysis", icon="science"
            ).classes("w-full"):
                ui.label(
                    "Experiment with temporary configuration changes and "
                    "generate alternatives without changing the saved configuration."
                ).classes("text-sm").style("color: var(--text-muted)")

                with _surface_card("Temporary Configuration"):
                    _placeholder(
                        "The reusable Configuration Editor will be placed here."
                    )

                    with ui.row().classes("w-full justify-end"):
                        ui.button(
                            "Generate What-If Schedule",
                            icon="auto_awesome",
                        ).props("outline disable")

    def refresh() -> None:
        """Refresh the selector from the shared schedule controller."""
        schedule_controller.sync_generated()
        options = schedule_controller.schedule_options()

        schedule_select.options = options

        if options:
            selected_index = schedule_controller.selected_index

            schedule_select.value = (
                selected_index
                if selected_index in options
                else next(iter(options))
            )

            empty_state.set_visibility(False)
            content.set_visibility(True)

            current = schedule_controller.current
            unscheduled_card.set_visibility(
                bool(current and current.source == "generated")
            )
        else:
            schedule_select.value = None
            empty_state.set_visibility(True)
            content.set_visibility(False)

        schedule_select.update()

    def on_schedule_change(event) -> None:
        if event.value is not None:
            schedule_controller.select(event.value)
            refresh()

    schedule_select.on_value_change(on_schedule_change)
    refresh_button.on_click(refresh)

    refresh()
    return refresh
