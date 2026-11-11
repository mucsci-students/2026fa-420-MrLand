"""Statistics tab for Schedule Analysis."""

from collections.abc import Callable

from nicegui import ui

from src.controllers.schedule_controller import schedule_controller
from src.views.schedule_analysis.analysis_components import surface_card

DAYS = ("MON", "TUE", "WED", "THU", "FRI")


def _placeholder_table(columns: list[dict]) -> None:
    """Display a formatted table without fabricated data."""
    ui.table(
        columns=columns,
        rows=[],
    ).classes("w-full").props("flat bordered dense")


def _metric_card(title: str, description: str = "") -> None:
    """Display a compact overview metric."""
    with (
        ui.card()
        .classes("grow min-w-[150px] gap-1 p-4")
        .style(
            "background: var(--surface-raised); "
            "border: 1px solid var(--border-color); "
            "border-radius: 12px;"
        )
    ):
        ui.label(title).classes("text-sm").style("color: var(--text-muted)")

        ui.label("—").classes("text-3xl font-bold").style("color: var(--text-primary)")

        if description:
            ui.label(description).classes("text-xs").style("color: var(--text-muted)")


def _score_breakdown() -> None:
    """Display the expandable quality-score breakdown."""
    criteria = [
        "Conflict Avoidance",
        "Faculty Gaps",
        "Room Utilization",
        "Workload Balance",
        "Scheduled Courses",
    ]

    with (
        ui.expansion(
            "View score breakdown",
            icon="analytics",
        ).classes("w-full"),
        ui.column().classes("w-full gap-3 pt-2"),
    ):
        for criterion in criteria:
            with ui.column().classes("w-full gap-1"):
                with ui.row().classes("w-full justify-between items-center"):
                    ui.label(criterion).classes("text-sm")
                    ui.label("—").classes("text-sm font-semibold").style("color: var(--text-muted)")

                with (
                    ui.element("div")
                    .classes("h-2 w-full overflow-hidden rounded-full")
                    .style("background: var(--surface-hover)")
                ):
                    pass


def _weekday_bars() -> None:
    """Display weekday distribution bars without sample values."""
    with ui.column().classes("w-full gap-3"):
        for day in DAYS:
            with ui.row().classes("w-full items-center gap-3"):
                ui.label(day).classes("w-12 text-xs font-semibold").style(
                    "color: var(--text-muted)"
                )

                with (
                    ui.element("div")
                    .classes("h-3 flex-1 overflow-hidden rounded-full")
                    .style("background: var(--surface-hover)")
                ):
                    pass

                ui.label("—").classes("w-6 text-right text-xs font-semibold").style(
                    "color: var(--text-muted)"
                )


def _resource_heatmap() -> None:
    """Display a blank Monday-Friday resource usage heat map."""
    with ui.column().classes("w-full gap-2"):
        # Weekday headings
        with ui.row().classes("w-full items-center gap-2"):
            ui.label("Resource").classes("w-28 shrink-0 text-xs font-semibold").style(
                "color: var(--text-muted)"
            )

            for day in DAYS:
                ui.label(day).classes("flex-1 text-center text-[10px] font-semibold").style(
                    "color: var(--text-muted)"
                )

        # Empty resource row
        with ui.row().classes("w-full items-center gap-2"):
            ui.label("—").classes("w-28 shrink-0 text-xs").style("color: var(--text-muted)")

            for _ in DAYS:
                with (
                    ui.element("div")
                    .classes("flex-1 min-w-0 h-10 rounded")
                    .style(
                        "background: var(--surface-raised); border: 1px solid var(--border-color);"
                    )
                ):
                    pass

        ui.label("Resource usage will appear here when data is available.").classes(
            "text-xs"
        ).style("color: var(--text-muted)")


def _resource_section(resource_type: str) -> None:
    """Build an expandable room or lab utilization section."""

    with ui.expansion(
        f"{resource_type} Utilization",
        icon="meeting_room" if resource_type == "Room" else "science",
    ).classes("w-full"):
        _placeholder_table(
            [
                {
                    "name": "resource",
                    "label": resource_type,
                    "field": "resource",
                    "align": "left",
                },
                {
                    "name": "used",
                    "label": "Used Hours",
                    "field": "used",
                    "align": "right",
                },
                {
                    "name": "util",
                    "label": "Utilization",
                    "field": "util",
                    "align": "right",
                },
                {
                    "name": "capacity",
                    "label": "Unused Capacity",
                    "field": "capacity",
                    "align": "right",
                },
                {
                    "name": "days",
                    "label": "Hours by Day",
                    "field": "days",
                    "align": "left",
                },
            ]
        )

        ui.label("Weekly Usage Heat Map").classes("text-sm font-semibold mt-4").style(
            "color: var(--text-primary)"
        )

        _resource_heatmap()


def build_statistics_tab(on_load_schedule: Callable[[], None]):
    """Build the Statistics tab and return the unscheduled courses container."""

    # ---------------------------------------------------------
    # Schedule controls
    # ---------------------------------------------------------

    with (
        surface_card(
            "Schedule",
            "Choose which schedule you want to analyze.",
        ),
        ui.row().classes("w-full items-center gap-3"),
    ):
        schedule_options = schedule_controller.schedule_options()

        schedule_select = (
            ui.select(
                options=schedule_options,
                label="Selected Schedule",
                value=(
                    schedule_controller.selected_index
                    if schedule_controller.selected_index in schedule_options
                    else None
                ),
            )
            .classes("flex-grow")
            .props("outlined")
        )

        ui.button(
            "Load Schedule",
            icon="upload_file",
            on_click=on_load_schedule,
        ).props("outline").classes("h-14 px-5")

    def on_schedule_change(event) -> None:
        if event.value is None:
            return

        schedule_controller.select(event.value)
        refresh_statistics()

    schedule_select.on_value_change(on_schedule_change)

    # ---------------------------------------------------------
    # Schedule Overview
    # ---------------------------------------------------------

    with surface_card(
        "Schedule Overview",
        "A quick summary of the selected schedule.",
    ):
        with ui.row().classes("w-full flex-wrap gap-3"):
            _metric_card(
                "Quality Score",
                "Overall schedule rating",
            )

            _metric_card(
                "Scheduled Courses",
                "Course sections assigned",
            )

            _metric_card(
                "Faculty Assigned",
                "Distinct faculty members",
            )

            _metric_card(
                "Unscheduled Courses",
                "Courses not assigned",
            )

        _score_breakdown()

    # ---------------------------------------------------------
    # Faculty Workload
    # ---------------------------------------------------------

    with surface_card(
        "Faculty Workload",
        "Understand how teaching responsibilities are distributed.",
    ):
        _placeholder_table(
            [
                {
                    "name": "faculty",
                    "label": "Faculty",
                    "field": "faculty",
                    "align": "left",
                },
                {
                    "name": "courses",
                    "label": "Courses",
                    "field": "courses",
                    "align": "right",
                },
                {
                    "name": "hours",
                    "label": "Teaching Hours",
                    "field": "hours",
                    "align": "right",
                },
                {
                    "name": "daily",
                    "label": "Daily Hours (M–F)",
                    "field": "daily",
                    "align": "left",
                },
                {
                    "name": "longest",
                    "label": "Longest Daily Span",
                    "field": "longest",
                    "align": "right",
                },
            ]
        )

        ui.label("Faculty workload information will appear here.").classes("text-xs").style(
            "color: var(--text-muted)"
        )

    # ---------------------------------------------------------
    # Course and Faculty Distribution
    # ---------------------------------------------------------

    with ui.grid(columns=2).classes("w-full gap-4"):
        with surface_card(
            "Class Distribution",
            "Number of course sections scheduled each weekday.",
        ):
            _weekday_bars()

            ui.separator().style("background: var(--border-color)")

            ui.label("Busiest Day: —").classes("text-sm")

            ui.label("Least Busy Day: —").classes("text-sm")

            ui.label("Early Starts: — · Late Starts: —").classes("text-sm")

        with surface_card(
            "Faculty Distribution",
            "Number of distinct faculty assigned each weekday.",
        ):
            _weekday_bars()

            ui.separator().style("background: var(--border-color)")

            ui.label("Empty Weekdays: —").classes("text-sm")

            ui.label("Available Empty Blocks (30+ min): —").classes("text-sm")

    # ---------------------------------------------------------
    # Room and Lab Utilization
    # ---------------------------------------------------------

    with surface_card(
        "Room & Lab Utilization",
        "Explore resource usage and availability throughout the week.",
    ):
        _resource_section("Room")

        ui.separator().style("background: var(--border-color)")

        _resource_section("Lab")

        ui.label(
            "Absolute utilization percentages require configured resource availability."
        ).classes("text-xs").style("color: var(--text-muted)")

    # ---------------------------------------------------------
    # Schedule Rankings
    # ---------------------------------------------------------

    with surface_card(
        "Top 5 Schedules",
        "Compare the highest-ranked generated schedules.",
    ):
        _placeholder_table(
            [
                {
                    "name": "rank",
                    "label": "Rank",
                    "field": "rank",
                    "align": "left",
                },
                {
                    "name": "schedule",
                    "label": "Schedule",
                    "field": "label",
                    "align": "left",
                },
                {
                    "name": "score",
                    "label": "Score",
                    "field": "score",
                    "align": "right",
                },
            ]
        )

        ui.label("Schedule rankings will appear here when available.").classes("text-xs").style(
            "color: var(--text-muted)"
        )

    # ---------------------------------------------------------
    # Unscheduled Courses
    # ---------------------------------------------------------

    with (
        ui.column().classes("w-full") as unscheduled_card,
        surface_card(
            "Unscheduled Courses",
            "Courses from the configuration that were not assigned.",
        ),
    ):
        _placeholder_table(
            [
                {
                    "name": "course",
                    "label": "Course",
                    "field": "course",
                    "align": "left",
                },
                {
                    "name": "section",
                    "label": "Section",
                    "field": "section",
                    "align": "left",
                },
                {
                    "name": "reason",
                    "label": "Reason",
                    "field": "reason",
                    "align": "left",
                },
            ]
        )

        ui.label("Unscheduled course information will appear here.").classes("text-xs").style(
            "color: var(--text-muted)"
        )

    def refresh_statistics() -> None:
        """Update the Statistics schedule selector."""
        options = schedule_controller.schedule_options()
        schedule_select.options = options

        if options:
            schedule_select.value = schedule_controller.selected_index
        else:
            schedule_select.value = None

        schedule_select.update()

    return unscheduled_card, refresh_statistics
