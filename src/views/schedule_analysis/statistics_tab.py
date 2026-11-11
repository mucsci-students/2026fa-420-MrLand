
"""Statistics tab for Schedule Analysis.

Contains the visual structure for schedule scoring, workload,
resource utilization, and weekday distribution.
"""

from nicegui import ui

from src.views.schedule_analysis.analysis_components import surface_card


DAYS = ("MON", "TUE", "WED", "THU", "FRI")


def _placeholder_table(columns: list[dict]) -> None:
    """Display a formatted table with headers and no fabricated data."""
    ui.table(
        columns=columns,
        rows=[],
    ).classes("w-full").props("flat bordered")


def _placeholder_weekday_bars() -> None:
    """Display the weekday distribution chart structure without data."""
    with ui.column().classes("w-full gap-3"):
        for day in DAYS:
            with ui.row().classes("w-full items-center gap-3"):
                ui.label(day).classes(
                    "w-12 text-xs font-semibold"
                ).style("color: var(--text-muted)")

                with ui.element("div").classes(
                    "h-3 flex-1 overflow-hidden rounded-full"
                ).style("background: var(--surface-hover)"):
                    pass

                ui.label("—").classes(
                    "w-6 text-right text-xs font-semibold"
                ).style("color: var(--text-primary)")


def _resource_heatmap() -> None:
    """Display a blank, theme-aware Monday-Friday resource heat map."""
    with ui.column().classes("w-full gap-2"):

        # Weekday headings
        with ui.row().classes("w-full items-center gap-2"):
            ui.label("Resource").classes(
                "w-28 shrink-0 text-xs font-semibold"
            ).style("color: var(--text-muted)")

            for day in DAYS:
                ui.label(day).classes(
                    "flex-1 text-center text-[10px] font-semibold"
                ).style("color: var(--text-muted)")

        # Empty heat map row
        with ui.row().classes("w-full items-center gap-2"):
            ui.label("—").classes(
                "w-28 shrink-0 text-xs"
            ).style("color: var(--text-muted)")

            for _ in DAYS:
                with ui.element("div").classes(
                    "flex-1 min-w-0 h-10 rounded"
                ).style(
                    "background: var(--surface-raised); "
                    "border: 1px solid var(--border-color);"
                ):
                    pass

        ui.label("Resource usage will appear here when data is available.").classes(
            "text-xs"
        ).style("color: var(--text-muted)")


def build_statistics_tab():
    """Build the Statistics tab layout."""

    # ---------------------------------------------------------
    # Schedule Quality Score and Top 5 Schedules
    # ---------------------------------------------------------

    with ui.grid(columns=2).classes("w-full gap-4"):

        with surface_card(
            "Schedule Quality Score",
            "Transparent score based on the criteria available for this schedule source.",
        ):
            # Overall score
            with ui.row().classes("items-end gap-3"):
                ui.label("—").classes(
                    "text-5xl font-bold"
                ).style("color: var(--accent-color)")

                ui.label("/ 100").classes(
                    "text-lg pb-1"
                ).style("color: var(--text-muted)")

            # Score breakdown
            ui.label("Score breakdown").classes(
                "font-semibold"
            ).style("color: var(--text-primary)")

            for criterion in (
                "Conflict Avoidance",
                "Faculty Gaps",
                "Room Utilization",
                "Workload Balance",
                "Scheduled Courses",
            ):
                with ui.column().classes("w-full gap-1"):
                    with ui.row().classes(
                        "w-full justify-between items-center"
                    ):
                        ui.label(criterion).classes("text-sm")
                        ui.label("—").classes(
                            "text-sm font-semibold"
                        )

                    with ui.element("div").classes(
                        "h-2 w-full overflow-hidden rounded-full"
                    ).style("background: var(--surface-hover)"):
                        pass

            ui.label(
                "Score details will be populated when schedule analysis is implemented."
            ).classes("text-xs").style("color: var(--text-muted)")

        # Top 5 Schedules
        with surface_card(
            "Top 5 Schedules",
            "Ranked using source-appropriate scoring criteria.",
        ):
            _placeholder_table([
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
            ])

            ui.label(
                "Generated and uploaded schedules will be ranked using their applicable criteria."
            ).classes("text-xs").style("color: var(--text-muted)")

    # ---------------------------------------------------------
    # Faculty Workload
    # ---------------------------------------------------------

    with surface_card(
        "Faculty Workload Analysis",
        "Faculty ranked from highest to lowest scheduled teaching hours.",
    ):
        _placeholder_table([
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
        ])

        ui.label(
            "Faculty workload information will appear here."
        ).classes("text-xs").style("color: var(--text-muted)")

    # ---------------------------------------------------------
    # Room and Lab Utilization
    # ---------------------------------------------------------

    with surface_card(
        "Room / Lab Utilization",
        "Scheduled hours by resource. Utilization percentages require configured availability.",
    ):

        # Room utilization
        ui.label("Rooms").classes(
            "font-semibold"
        ).style("color: var(--text-primary)")

        _placeholder_table([
            {
                "name": "resource",
                "label": "Room",
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
        ])

        ui.label("Room weekly usage heat map").classes(
            "text-sm font-semibold mt-2"
        ).style("color: var(--text-primary)")

        _resource_heatmap()

        ui.separator().style("background: var(--border-color)")

        # Lab utilization
        ui.label("Labs").classes(
            "font-semibold"
        ).style("color: var(--text-primary)")

        _placeholder_table([
            {
                "name": "resource",
                "label": "Lab",
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
        ])

        ui.label("Lab weekly usage heat map").classes(
            "text-sm font-semibold mt-2"
        ).style("color: var(--text-primary)")

        _resource_heatmap()

        ui.label(
            "Uploaded schedules do not include room availability settings, "
            "so absolute utilization percentages may not be available."
        ).classes("text-xs").style("color: var(--text-muted)")

    # ---------------------------------------------------------
    # Class and Faculty Distribution
    # ---------------------------------------------------------

    with ui.grid(columns=2).classes("w-full gap-4"):

        # Class distribution
        with surface_card(
            "Class Distribution",
            "Unique course sections scheduled on each weekday.",
        ):
            _placeholder_weekday_bars()

            ui.label("Busiest day: — · Least busy day: —").classes(
                "text-sm"
            )

            ui.label(
                "Early starts: — · Late starts: —"
            ).classes("text-sm")

        # Faculty distribution
        with surface_card(
            "Faculty Distribution",
            "Number of distinct faculty assigned each weekday.",
        ):
            _placeholder_weekday_bars()

            ui.label("Empty weekdays: —").classes("text-sm")

            ui.label(
                "Available empty blocks (30+ min): —"
            ).classes("text-sm")

    # ---------------------------------------------------------
    # Unscheduled Courses
    # ---------------------------------------------------------

    with surface_card(
        "Unscheduled Courses",
        "Courses in the source configuration that do not appear in this generated result.",
    ) as unscheduled_card:

        _placeholder_table([
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
        ])

        ui.label(
            "Unscheduled course information will appear here for generated schedules."
        ).classes("text-xs").style("color: var(--text-muted)")

    return unscheduled_card
