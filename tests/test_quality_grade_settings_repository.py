from src.models.quality_grade_settings_repository import (
    load_quality_grade_settings,
    save_quality_grade_settings,
)
from src.models.quality_grading import QualityGradeSettings


def test_quality_grade_settings_repository_returns_defaults_and_copies_values():
    assert load_quality_grade_settings(None).model_dump() == QualityGradeSettings().model_dump()
    assert (
        load_quality_grade_settings("missing").model_dump() == QualityGradeSettings().model_dump()
    )

    settings = QualityGradeSettings(max_faculty_gap_minutes=45)
    save_quality_grade_settings("fall", settings)
    settings.max_faculty_gap_minutes = 90

    loaded = load_quality_grade_settings("fall")
    assert loaded.max_faculty_gap_minutes == 45

    loaded.max_faculty_gap_minutes = 10
    assert load_quality_grade_settings("fall").max_faculty_gap_minutes == 45
