"""Keep uploaded configurations' quality grading settings for this app session."""

from src.models.quality_grading import QualityGradeSettings

_settings_by_config: dict[str, QualityGradeSettings] = {}


def load_quality_grade_settings(config_name: str | None) -> QualityGradeSettings:
    """Return settings retained from a loaded configuration, or the defaults."""
    if not config_name:
        return QualityGradeSettings()

    settings = _settings_by_config.get(config_name)
    return settings.model_copy(deep=True) if settings is not None else QualityGradeSettings()


def save_quality_grade_settings(
    config_name: str,
    settings: QualityGradeSettings,
) -> None:
    """Retain settings in memory; downloaded JSON carries them between sessions."""
    _settings_by_config[config_name] = settings.model_copy(deep=True)
