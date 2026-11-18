from src.models.quality_grading import QualityGradeSettings, grade_schedule_analysis
from src.models.schedule_analysis_model import (
    DAYS,
    FacultyWorkload,
    ResourceUsage,
    ScheduleAnalysis,
)


def _analysis(
    *,
    faculty_workload: list[FacultyWorkload],
    room_utilization: list[ResourceUsage],
    lab_utilization: list[ResourceUsage],
    weekday_teaching_hours: dict[str, float],
    scheduled_sections: int = 1,
) -> ScheduleAnalysis:
    return ScheduleAnalysis(
        schedule_label="Test schedule",
        scheduled_sections=scheduled_sections,
        faculty_assigned=len(faculty_workload),
        weekday_meetings={day: 0 for day in DAYS},
        faculty_workload=faculty_workload,
        room_utilization=room_utilization,
        lab_utilization=lab_utilization,
        unscheduled_courses=None,
        available_empty_blocks=None,
        early_starts=0,
        late_ends=0,
        weekday_teaching_hours=weekday_teaching_hours,
    )


def _workload(faculty: str, teaching_hours: float, gap_minutes: int) -> FacultyWorkload:
    return FacultyWorkload(
        faculty=faculty,
        sections=1,
        teaching_hours=teaching_hours,
        hours_by_day={day: 0 for day in DAYS},
        longest_daily_span_hours=0,
        gap_minutes=gap_minutes,
    )


def _resource(name: str, used_hours: float, available_hours: float) -> ResourceUsage:
    return ResourceUsage(
        resource=name,
        meetings=1,
        used_hours=used_hours,
        hours_by_day={day: 0 for day in DAYS},
        available_hours=available_hours,
    )


def test_grade_schedule_analysis_uses_default_targets():
    analysis = _analysis(
        faculty_workload=[_workload("A", 3, 100), _workload("B", 3, 200)],
        room_utilization=[_resource("Room", 60, 100)],
        lab_utilization=[_resource("Lab", 50, 100)],
        weekday_teaching_hours={day: 2 for day in DAYS},
    )

    grades = grade_schedule_analysis(analysis, QualityGradeSettings())

    assert grades.faculty_gaps == "A"
    assert grades.room_utilization == "A"
    assert grades.lab_utilization == "A"
    assert grades.faculty_workload_balance == "A"
    assert grades.weekday_teaching_hours_balance == "A"
    assert grades.composite == "A"


def test_grade_schedule_analysis_grades_metrics_and_averages_composite():
    analysis = _analysis(
        faculty_workload=[_workload("A", 0, 600), _workload("B", 6, 300)],
        room_utilization=[
            _resource("Room A", 52, 100),
            _resource("Room B", 50, 100),
        ],
        lab_utilization=[_resource("Lab", 35, 100)],
        weekday_teaching_hours={"MON": 7.75},
    )

    grades = grade_schedule_analysis(analysis, QualityGradeSettings())

    assert grades.faculty_gaps == "D"
    assert grades.room_utilization == "B"
    assert grades.lab_utilization == "C"
    assert grades.faculty_workload_balance == "C"
    assert grades.weekday_teaching_hours_balance == "D"
    assert grades.composite == "C"


def test_grade_schedule_analysis_excludes_unavailable_metrics():
    analysis = _analysis(
        faculty_workload=[],
        room_utilization=[],
        lab_utilization=[],
        weekday_teaching_hours={},
        scheduled_sections=0,
    )

    grades = grade_schedule_analysis(analysis, QualityGradeSettings())

    assert grades.faculty_gaps is None
    assert grades.room_utilization is None
    assert grades.lab_utilization is None
    assert grades.faculty_workload_balance is None
    assert grades.weekday_teaching_hours_balance is None
    assert grades.composite is None
