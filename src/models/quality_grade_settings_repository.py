"""Persist per-configuration quality grading constraints."""

import json
import os
import tempfile
from hashlib import sha256
from pathlib import Path

from pydantic import ValidationError

from src.models import configuration_repository
from src.models.quality_grading import QualityGradeSettings, settings_from_document


def _settings_path(config_name: str) -> Path:
    key = sha256(config_name.encode("utf-8")).hexdigest()
    return configuration_repository.CONFIG_DIR / ".quality_grade_settings" / f"{key}.json"


def load_quality_grade_settings(config_name: str | None) -> QualityGradeSettings:
    """Load saved constraints by config name, falling back to embedded settings or defaults."""
    if not config_name:
        return QualityGradeSettings()

    sidecar_path = _settings_path(config_name)
    if sidecar_path.is_file():
        try:
            return QualityGradeSettings.model_validate_json(
                sidecar_path.read_text(encoding="utf-8")
            )
        except ValidationError as exc:
            raise ValueError(f"Invalid quality grade settings for '{config_name}': {exc}") from exc

    try:
        config_path = configuration_repository.CONFIG_DIR / (
            f"{configuration_repository.clean_config_name(config_name)}.json"
        )
    except ValueError:
        return QualityGradeSettings()
    if config_path.is_file():
        try:
            document = json.loads(config_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return QualityGradeSettings()
        return settings_from_document(document)
    return QualityGradeSettings()


def save_quality_grade_settings(
    config_name: str,
    settings: QualityGradeSettings,
) -> None:
    """Atomically save custom constraints in an app-local profile for a config."""
    path = _settings_path(config_name)
    path.parent.mkdir(parents=True, exist_ok=True)
    file_descriptor, temporary_path = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    try:
        with os.fdopen(file_descriptor, "w", encoding="utf-8") as settings_file:
            settings_file.write(settings.model_dump_json(indent=4))
        os.replace(temporary_path, path)
    finally:
        if os.path.exists(temporary_path):
            os.remove(temporary_path)
