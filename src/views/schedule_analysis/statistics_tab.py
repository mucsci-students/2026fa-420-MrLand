"""Statistics tab for Schedule Analysis."""

from collections.abc import Callable

from nicegui import ui

from src.controllers.schedule_analysis_controller import schedule_analysis_controller
from src.controllers.schedule_controller import schedule_controller
from src.models.quality_grade_settings_repository import load_quality_grade_settings
from src.models.quality_grading import QualityGradeSettings, grade_schedule_analysis
from src.models.schedule_analysis_model import ResourceUsage, ScheduleAnalysis
from src.models.schedule_viewer_model import ScheduleEntry
from src.views.schedule_analysis.analysis_components import surface_card

DAYS = ("MON", "TUE", "WED", "THU", "FRI")


def _placeholder_table(columns: list[dict]):
    """Display a formatted table without fabricated data."""
    return ui.table(
        columns=columns,
        rows=[],
    ).classes("w-full").props("flat bordered dense")


def _metric_card(title: str, description: str = ""):
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

        value = ui.label("—").classes("text-3xl font-bold").style(
            "color: var(--text-primary)"
        )

        if description:
            ui.label(description).classes("text-xs").style("color: var(--text-muted)")

    return value


def _score_breakdown():
    """Display letter grades for the quality measures."""
    criteria = [
        ("faculty_gaps", "Faculty Gaps"),
        ("resource_utilization", "Room & Lab Utilization"),
        ("faculty_balance", "Faculty Workload Balance"),
        ("weekday_balance", "Weekday Teaching-Hours Balance"),
    ]

    values = {}
    with (
        ui.expansion(
            "View quality grades",
            icon="analytics",
        ).classes("w-full"),
        ui.column().classes("w-full gap-3 pt-2"),
    ):
        ui.label(
            "Faculty gaps use the largest individual weekly total; utilization uses "
            "the geometric mean; balance uses standard deviation."
        ).classes("text-xs").style("color: var(--text-muted)")
        for key, criterion in criteria:
            with ui.row().classes("w-full justify-between items-center"):
                ui.label(criterion).classes("text-sm")
                values[key] = ui.label("—").classes("text-sm font-semibold").style(
                    "color: var(--text-muted)"
                )
    return values


def _weekday_bars():
    """Display weekday bars and return their fill and value elements."""
    bars = {}
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
                    bar = ui.element("div").classes("h-full rounded-full").style(
                        "width: 0%; background: var(--accent-color)"
                    )

                value = ui.label("—").classes("w-6 text-right text-xs font-semibold").style(
                    "color: var(--text-muted)"
                )
                bars[day] = (bar, value)
    return bars


def _resource_heatmap():
    """Create a container for the Monday-Friday resource usage heat map."""
    heatmap = ui.column().classes("w-full gap-2")
    return heatmap


def _resource_section(resource_type: str):
    """Build an expandable room or lab utilization section."""

    with ui.expansion(
        f"{resource_type} Utilization",
        icon="meeting_room" if resource_type == "Room" else "science",
    ).classes("w-full"):
        table = ui.table(
            columns=[
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
                    "label": "Unused Hours",
                    "field": "capacity",
                    "align": "right",
                },
                {
                    "name": "days",
                    "label": "Hours by Day",
                    "field": "days",
                    "align": "left",
                },
            ],
            rows=[],
        ).classes("w-full").props("flat bordered dense")

        ui.label("Weekly Usage Heat Map").classes("text-sm font-semibold mt-4").style(
            "color: var(--text-primary)"
        )

        heatmap = _resource_heatmap()

    return table, heatmap


def _format_hours(hours: float) -> str:
    return f"{hours:.2f}"


def _set_weekday_bars(bars, values: dict[str, int]) -> None:
    maximum = max(values.values(), default=0)
    for day, (bar, label) in bars.items():
        value = values.get(day, 0)
        width = 0 if maximum == 0 else value / maximum * 100
        bar.style(f"width: {width:.1f}%; background: var(--accent-color)")
        label.text = str(value)
        bar.update()
        label.update()


def _resource_rows(resources: list[ResourceUsage]) -> list[dict[str, str]]:
    return [
        {
            "resource": item.resource,
            "used": _format_hours(item.used_hours),
            "util": (
                f"{item.utilization_percent:.1f}%"
                if item.utilization_percent is not None
                else "—"
            ),
            "capacity": (
                _format_hours(item.unused_hours)
                if item.unused_hours is not None
                else "—"
            ),
            "days": " · ".join(
                f"{day} {_format_hours(item.hours_by_day[day])}" for day in DAYS
            ),
        }
        for item in resources
    ]


def _top_schedule_rows(
    config_name: str | None,
    entries: list[ScheduleEntry],
    quality_settings: QualityGradeSettings,
) -> list[dict[str, str | int]]:
    if not config_name:
        return []

    scored_schedules = []
    for entry in entries:
        if entry.config_name != config_name:
            continue
        analysis = schedule_analysis_controller.analyze_schedule(entry)
        if analysis is None:
            continue
        grades = grade_schedule_analysis(analysis, quality_settings)
        score = grades.average_points
        if score is not None:
            scored_schedules.append((score, grades.composite, entry.label))

    scored_schedules.sort(key=lambda result: result[0], reverse=True)
    return [
        {
            "rank": rank,
            "label": label,
            "score": f"{score:.2f} ({composite})",
        }
        for rank, (score, composite, label) in enumerate(scored_schedules[:5], start=1)
    ]


def _update_resource_heatmap(heatmap, resources: list[ResourceUsage]) -> None:
    heatmap.clear()
    with heatmap:
        with ui.row().classes("w-full items-center gap-2"):
            ui.label("Resource").classes("w-28 shrink-0 text-xs font-semibold").style(
                "color: var(--text-muted)"
            )
            for day in DAYS:
                ui.label(day).classes("flex-1 text-center text-[10px] font-semibold").style(
                    "color: var(--text-muted)"
                )

        if not resources:
            ui.label("No resource usage data available.").classes("text-xs").style(
                "color: var(--text-muted)"
            )
            return

        maximum = max(
            (usage.hours_by_day[day] for usage in resources for day in DAYS),
            default=0,
        )
        for usage in resources:
            with ui.row().classes("w-full items-center gap-2"):
                ui.label(usage.resource).classes("w-28 shrink-0 truncate text-xs").style(
                    "color: var(--text-primary)"
                )
                for day in DAYS:
                    hours = usage.hours_by_day[day]
                    opacity = 0 if maximum == 0 else min(hours / maximum, 1)
                    ui.element("div").classes("flex-1 min-w-0 h-10 rounded").style(
                        "background: color-mix(in srgb, var(--accent-color) "
                        f"{opacity * 100:.0f}%, var(--surface-raised)); "
                        "border: 1px solid var(--border-color);"
                    ).tooltip(f"{day}: {_format_hours(hours)} hours")


def _update_analysis(
    analysis: ScheduleAnalysis | None,
    metric_values,
    quality_values,
    quality_settings: QualityGradeSettings,
    workload_table,
    class_bars,
    faculty_bars,
    class_summary,
    faculty_summary,
    empty_blocks_summary,
    start_time_summary,
    room_table,
    room_heatmap,
    lab_table,
    lab_heatmap,
) -> None:
    if analysis is None:
        for value in metric_values.values():
            value.text = "—"
            value.update()
        for value in quality_values.values():
            value.text = "—"
            value.update()
        class_summary["busy"].text = "Busiest Day: —"
        class_summary["quiet"].text = "Least Busy Day: —"
        faculty_summary.text = "Empty Weekdays: —"
        empty_blocks_summary.text = "Available Empty Blocks (30+ min): —"
        start_time_summary.text = "Early Starts (<9:00 AM): — · Late Ends (>5:00 PM): —"
        for label in (
            *class_summary.values(),
            faculty_summary,
            empty_blocks_summary,
            start_time_summary,
        ):
            label.update()
        workload_table.rows = []
        room_table.rows = []
        lab_table.rows = []
        for table in (workload_table, room_table, lab_table):
            table.update()
        _set_weekday_bars(class_bars, {})
        _set_weekday_bars(faculty_bars, {})
        _update_resource_heatmap(room_heatmap, [])
        _update_resource_heatmap(lab_heatmap, [])
        return

    metric_values["scheduled"].text = str(analysis.scheduled_sections)
    metric_values["faculty"].text = str(analysis.faculty_assigned)
    grades = grade_schedule_analysis(analysis, quality_settings)
    metric_values["quality"].text = grades.composite or "—"
    metric_values["scheduled"].update()
    metric_values["faculty"].update()
    metric_values["quality"].update()

    for key, grade in (
        ("faculty_gaps", grades.faculty_gaps),
        (
            "resource_utilization",
            f"Rooms {grades.room_utilization or '—'} · Labs {grades.lab_utilization or '—'}",
        ),
        ("faculty_balance", grades.faculty_workload_balance),
        ("weekday_balance", grades.weekday_teaching_hours_balance),
    ):
        value = quality_values[key]
        value.text = grade or "—"
        value.update()

    workload_table.rows = [
        {
            "faculty": workload.faculty,
            "courses": workload.sections,
            "hours": _format_hours(workload.teaching_hours),
            "daily": " · ".join(
                f"{day} {_format_hours(workload.hours_by_day[day])}" for day in DAYS
            ),
            "longest": _format_hours(workload.longest_daily_span_hours),
        }
        for workload in analysis.faculty_workload
    ]
    workload_table.update()

    class_counts = analysis.weekday_meetings
    _set_weekday_bars(class_bars, class_counts)
    busiest = max(DAYS, key=lambda day: class_counts[day]) if any(class_counts.values()) else None
    least_busy = min(DAYS, key=lambda day: class_counts[day]) if any(class_counts.values()) else None
    class_summary["busy"].text = f"Busiest Day: {busiest or '—'}"
    class_summary["quiet"].text = f"Least Busy Day: {least_busy or '—'}"

    faculty_counts = {
        day: sum(workload.hours_by_day[day] > 0 for workload in analysis.faculty_workload)
        for day in DAYS
    }
    _set_weekday_bars(faculty_bars, faculty_counts)
    empty_days = [day for day in DAYS if faculty_counts[day] == 0]
    faculty_summary.text = f"Empty Weekdays: {', '.join(empty_days) if empty_days else 'None'}"
    faculty_summary.update()
    empty_blocks_summary.text = (
        "Available Empty Blocks (30+ min): "
        f"{analysis.available_empty_blocks if analysis.available_empty_blocks is not None else '—'}"
    )
    empty_blocks_summary.update()
    start_time_summary.text = (
        f"Early Starts (<9:00 AM): {analysis.early_starts} · "
        f"Late Ends (>5:00 PM): {analysis.late_ends}"
    )
    start_time_summary.update()

    for label in (class_summary["busy"], class_summary["quiet"]):
        label.update()

    room_table.rows = _resource_rows(analysis.room_utilization)
    lab_table.rows = _resource_rows(analysis.lab_utilization)
    room_table.update()
    lab_table.update()
    _update_resource_heatmap(room_heatmap, analysis.room_utilization)
    _update_resource_heatmap(lab_heatmap, analysis.lab_utilization)


def build_statistics_tab(on_load_schedule: Callable[[], None]):
    """Build the Statistics tab and return its refresh callback."""

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
            metric_values = {}
            metric_values["quality"] = _metric_card(
                "Composite Grade",
                "Average component points (A=4 through F=0), rounded to the nearest grade.",
            )

            metric_values["scheduled"] = _metric_card(
                "Scheduled Courses",
                "Course sections assigned",
            )

            metric_values["faculty"] = _metric_card(
                "Faculty Assigned",
                "Distinct faculty members",
            )

        quality_values = _score_breakdown()

    # ---------------------------------------------------------
    # Faculty Workload
    # ---------------------------------------------------------

    with surface_card(
        "Faculty Workload",
        "Understand how teaching responsibilities are distributed.",
    ):
        workload_table = _placeholder_table(
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
            "Number of class meetings scheduled each weekday.",
        ):
            class_bars = _weekday_bars()

            ui.separator().style("background: var(--border-color)")

            class_summary = {
                "busy": ui.label("Busiest Day: —").classes("text-sm"),
                "quiet": ui.label("Least Busy Day: —").classes("text-sm"),
            }

            start_time_summary = ui.label(
                "Early Starts (<9:00 AM): — · Late Ends (>5:00 PM): —"
            ).classes("text-sm")

        with surface_card(
            "Faculty Distribution",
            "Number of distinct faculty assigned each weekday.",
        ):
            faculty_bars = _weekday_bars()

            ui.separator().style("background: var(--border-color)")

            faculty_summary = ui.label("Empty Weekdays: —").classes("text-sm")
            empty_blocks_summary = ui.label(
                "Available Empty Blocks (30+ min): —"
            ).classes("text-sm")

    # ---------------------------------------------------------
    # Room and Lab Utilization
    # ---------------------------------------------------------

    with surface_card(
        "Room & Lab Utilization",
        "Explore resource usage and availability throughout the week.",
    ):
        room_table, room_heatmap = _resource_section("Room")

        ui.separator().style("background: var(--border-color)")

        lab_table, lab_heatmap = _resource_section("Lab")

        ui.label(
            "Utilization uses configured resource hours within the schedule's weekly time blocks."
        ).classes("text-xs").style("color: var(--text-muted)")

    # ---------------------------------------------------------
    # Schedule Rankings
    # ---------------------------------------------------------

    with surface_card(
        "Top 5 Schedules",
        "Highest composite quality scores for the selected schedule's configuration.",
    ):
        top_schedules_table = _placeholder_table(
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

    def refresh_statistics() -> None:
        """Refresh the selector and statistics for the currently selected schedule."""
        options = schedule_controller.schedule_options()
        schedule_select.options = options

        if options:
            schedule_select.value = schedule_controller.selected_index
        else:
            schedule_select.value = None

        schedule_select.update()
        analysis = schedule_analysis_controller.analyze_selected_schedule()
        entry = schedule_controller.current
        quality_settings = load_quality_grade_settings(
            entry.config_name if entry is not None else None
        )
        top_schedules_table.rows = _top_schedule_rows(
            entry.config_name if entry is not None else None,
            schedule_controller.generated_entries,
            quality_settings,
        )
        top_schedules_table.update()
        _update_analysis(
            analysis,
            metric_values,
            quality_values,
            quality_settings,
            workload_table,
            class_bars,
            faculty_bars,
            class_summary,
            faculty_summary,
            empty_blocks_summary,
            start_time_summary,
            room_table,
            room_heatmap,
            lab_table,
            lab_heatmap,
        )

    return refresh_statistics
