import asyncio
from unittest.mock import Mock

from nicegui import ElementFilter, ui
from nicegui.testing import user_simulation

from src.models.quality_grading import QualityGradeSettings, ScheduleGrades
from src.models.schedule_analysis_model import (
    FacultyWorkload,
    ResourceUsage,
    ScheduleAnalysis,
)
from src.models.schedule_viewer_model import ScheduleEntry
from src.views.schedule_analysis import statistics_tab
from src.views.schedule_analysis.statistics_tab import build_statistics_tab
from tests.conftest import active_client


def test_analysis_refresh_updates_workload_distribution_and_utilization(monkeypatch):
    days = ("MON", "TUE", "WED", "THU", "FRI")
    analysis = ScheduleAnalysis(
        schedule_label="Selected schedule",
        scheduled_sections=1,
        faculty_assigned=1,
        weekday_meetings={day: int(day == "MON") for day in days},
        faculty_workload=[
            FacultyWorkload(
                faculty="Dr. Smith",
                sections=1,
                teaching_hours=1,
                hours_by_day={day: float(day == "MON") for day in days},
                longest_daily_span_hours=1,
            )
        ],
        room_utilization=[
            ResourceUsage(
                resource="Room 101",
                meetings=1,
                used_hours=1,
                hours_by_day={day: float(day == "MON") for day in days},
                available_hours=2,
            )
        ],
        lab_utilization=[
            ResourceUsage(
                resource="Lab A",
                meetings=1,
                used_hours=1,
                hours_by_day={day: float(day == "MON") for day in days},
                available_hours=2,
            )
        ],
        unscheduled_courses=[],
        available_empty_blocks=0,
        early_starts=0,
        late_ends=0,
    )
    workload_table = Mock()
    room_table = Mock()
    lab_table = Mock()
    class_bars = {day: (Mock(), Mock()) for day in days}
    faculty_bars = {day: (Mock(), Mock()) for day in days}
    quality_values = {
        key: Mock()
        for key in (
            "faculty_gaps",
            "resource_utilization",
            "faculty_balance",
            "weekday_balance",
        )
    }
    heatmap_update = Mock()
    monkeypatch.setattr(statistics_tab, "_update_resource_heatmap", heatmap_update)
    metric_values = {
        "quality": Mock(),
        "scheduled": Mock(),
        "faculty": Mock(),
    }

    statistics_tab._update_analysis(
        analysis,
        metric_values,
        quality_values,
        QualityGradeSettings(),
        workload_table,
        class_bars,
        faculty_bars,
        {"busy": Mock(), "quiet": Mock()},
        Mock(),
        Mock(),
        Mock(),
        room_table,
        Mock(),
        lab_table,
        Mock(),
    )

    assert workload_table.rows[0]["faculty"] == "Dr. Smith"
    assert class_bars["MON"][1].text == "1"
    assert faculty_bars["MON"][1].text == "1"
    assert room_table.rows[0]["util"] == "50.0%"
    assert lab_table.rows[0]["util"] == "50.0%"
    assert quality_values["faculty_gaps"].text == "A"
    assert quality_values["resource_utilization"].text == "Rooms C · Labs A"
    assert quality_values["faculty_balance"].text == "A"
    assert quality_values["weekday_balance"].text == "A"
    assert metric_values["quality"].text == "A"
    assert heatmap_update.call_count == 2


def test_statistics_overview_and_score_breakdown_show_requested_metrics():
    async def simulate():
        async with user_simulation(root=lambda: build_statistics_tab(lambda: None)) as user:
            await user.open("/")

            with active_client(user):
                overview = next(
                    card
                    for card in ElementFilter(kind=ui.card)
                    if next(
                        iter(
                            ElementFilter(
                                kind=ui.label,
                                content="Schedule Overview",
                            ).within(instance=card)
                        ),
                        None,
                    )
                )
                overview_labels = {
                    label.text for label in ElementFilter(kind=ui.label).within(instance=overview)
                }
                assert "Unscheduled Courses" not in overview_labels
                assert "Unscheduled Courses" not in {
                    label.text for label in ElementFilter(kind=ui.label)
                }

                breakdown = next(
                    expansion
                    for expansion in ElementFilter(kind=ui.expansion)
                    if "Faculty Gaps"
                    in {
                        label.text
                        for label in ElementFilter(kind=ui.label).within(instance=expansion)
                    }
                )
                breakdown_labels = {
                    label.text for label in ElementFilter(kind=ui.label).within(instance=breakdown)
                }
                assert "Conflict Avoidance" not in breakdown_labels
                assert "Scheduled Courses" not in breakdown_labels
                assert "Faculty Workload Balance" in breakdown_labels
                assert "Weekday Teaching-Hours Balance" in breakdown_labels

    asyncio.run(simulate())


def test_top_schedules_are_ranked_for_selected_configuration(monkeypatch):
    grades_by_label = {
        "first A": ScheduleGrades("A", "A", "A", "A", "A", "A"),
        "second A": ScheduleGrades("A", "A", "A", "A", "A", "A"),
        "B": ScheduleGrades("B", "B", "B", "B", "B", "B"),
        "C": ScheduleGrades("C", "C", "C", "C", "C", "C"),
        "D": ScheduleGrades("D", "D", "D", "D", "D", "D"),
        "F": ScheduleGrades("F", "F", "F", "F", "F", "F"),
        "other config": ScheduleGrades("A", "A", "A", "A", "A", "A"),
    }
    entries = [
        ScheduleEntry(
            label=label,
            config_name="demo" if label != "other config" else "other",
            source="generated",
            records=[],
        )
        for label in grades_by_label
    ]
    monkeypatch.setattr(
        statistics_tab.schedule_analysis_controller,
        "analyze_schedule",
        lambda entry: entry,
    )
    monkeypatch.setattr(
        statistics_tab,
        "grade_schedule_analysis",
        lambda analysis, _settings: grades_by_label[analysis.label],
    )

    rows = statistics_tab._top_schedule_rows("demo", entries, QualityGradeSettings())

    assert [row["label"] for row in rows] == ["first A", "second A", "B", "C", "D"]
    assert [row["rank"] for row in rows] == [1, 2, 3, 4, 5]
    assert [row["score"] for row in rows] == [
        "4.00 (A)",
        "4.00 (A)",
        "3.00 (B)",
        "2.00 (C)",
        "1.00 (D)",
    ]
