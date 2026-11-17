"""Default quality-grade constraints and schedule grade calculation."""

from dataclasses import dataclass

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from src.models.schedule_analysis_model import ScheduleAnalysis

QUALITY_GRADE_SETTINGS_KEY = "quality_grade_settings"
_GRADE_POINTS = {"A": 4, "B": 3, "C": 2, "D": 1, "F": 0}


class QualityGradeSettings(BaseModel):
    """Per-configuration A-grade targets for schedule quality measures."""

    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    max_faculty_gap_minutes: int = Field(default=300, ge=0)
    min_room_utilization_percent: float = Field(default=60, ge=0, le=100)
    min_lab_utilization_percent: float = Field(default=50, ge=0, le=100)
    max_faculty_workload_stddev_hours: float = Field(default=2, ge=0)
    max_weekday_teaching_hours_stddev: float = Field(default=2, ge=0)


def settings_from_document(document: object) -> QualityGradeSettings:
    """Read the optional application metadata from a configuration document."""
    if not isinstance(document, dict):
        return QualityGradeSettings()
    values = document.get(QUALITY_GRADE_SETTINGS_KEY)
    if values is None:
        return QualityGradeSettings()
    try:
        return QualityGradeSettings.model_validate(values)
    except ValidationError as exc:
        raise ValueError(f"Invalid quality grade settings: {exc}") from exc


@dataclass(frozen=True)
class ScheduleGrades:
    """Letter grades for the five component measures and their composite."""

    faculty_gaps: str | None
    room_utilization: str | None
    lab_utilization: str | None
    faculty_workload_balance: str | None
    weekday_teaching_hours_balance: str | None
    composite: str | None

    @property
    def average_points(self) -> float | None:
        return _average_grade_points(
            [
                self.faculty_gaps,
                self.room_utilization,
                self.lab_utilization,
                self.faculty_workload_balance,
                self.weekday_teaching_hours_balance,
            ]
        )


def _average_grade_points(grades: list[str | None]) -> float | None:
    points = [_GRADE_POINTS[grade] for grade in grades if grade is not None]
    return sum(points) / len(points) if points else None


def _grade_lower_is_better(value: float | None, target: float) -> str | None:
    if value is None:
        return None
    if value <= target:
        return "A"
    if value <= target * 1.25:
        return "B"
    if value <= target * 1.5:
        return "C"
    if value <= target * 2:
        return "D"
    return "F"


def _grade_higher_is_better(value: float | None, target: float) -> str | None:
    if value is None:
        return None
    if value >= target:
        return "A"
    if value >= target * 0.85:
        return "B"
    if value >= target * 0.7:
        return "C"
    if value >= target * 0.5:
        return "D"
    return "F"


def _composite_grade(grades: list[str | None]) -> str | None:
    average = _average_grade_points(grades)
    if average is None:
        return None
    if average >= 3.5:
        return "A"
    if average >= 2.5:
        return "B"
    if average >= 1.5:
        return "C"
    if average >= 0.5:
        return "D"
    return "F"


def grade_schedule_analysis(
    analysis: ScheduleAnalysis,
    settings: QualityGradeSettings,
) -> ScheduleGrades:
    """Grade available measures against A-grade targets and average their points."""
    faculty_gap_minutes = max(
        (workload.gap_minutes for workload in analysis.faculty_workload),
        default=None,
    )
    grades = (
        _grade_lower_is_better(faculty_gap_minutes, settings.max_faculty_gap_minutes),
        _grade_higher_is_better(
            analysis.room_utilization_geomean_percent,
            settings.min_room_utilization_percent,
        ),
        _grade_higher_is_better(
            analysis.lab_utilization_geomean_percent,
            settings.min_lab_utilization_percent,
        ),
        _grade_lower_is_better(
            analysis.faculty_workload_stddev_hours,
            settings.max_faculty_workload_stddev_hours,
        ),
        _grade_lower_is_better(
            analysis.weekday_teaching_hours_stddev,
            settings.max_weekday_teaching_hours_stddev,
        ),
    )
    return ScheduleGrades(*grades, composite=_composite_grade(list(grades)))
