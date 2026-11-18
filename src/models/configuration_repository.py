"""Reads and writes validated scheduler configuration files.

Used by: GUI."""

import json
import os
import re
import tempfile
from pathlib import Path

from pydantic import ValidationError
from scheduler.config import CombinedConfig

from src.models.quality_grading import (
    QUALITY_GRADE_SETTINGS_KEY,
    QualityGradeSettings,
    settings_from_document,
)

CONFIG_DIR = Path(__file__).resolve().parent.parent / "configs"

_CONFIG_NAME_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 _-]{0,63}$")


class ConfigLoadError(Exception):
    """Raised when a config file exists but can't be parsed or validated."""


def clean_config_name(name: str) -> str:
    """Return a cleaned name, or raise ValueError. Does not check existence."""
    name = name.strip()
    if not name:
        raise ValueError("Configuration name cannot be empty.")
    if not _CONFIG_NAME_PATTERN.match(name):
        raise ValueError(
            "Use letters, numbers, spaces, hyphens, or underscores "
            "(start with a letter or number, max 64 characters)."
        )
    return name


def _config_path(config_name: str) -> Path:
    return CONFIG_DIR / f"{clean_config_name(config_name)}.json"


def save_config(
    combined_config: CombinedConfig,
    config_name: str,
    quality_grade_settings: QualityGradeSettings | None = None,
) -> None:
    path = _config_path(config_name)
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    document = combined_config.model_dump(mode="json")
    if quality_grade_settings is not None:
        document[QUALITY_GRADE_SETTINGS_KEY] = quality_grade_settings.model_dump(mode="json")

    # Write to a temp file in the same directory, then atomically swap it in,
    # so a crash mid-write can't corrupt an existing config.
    fd, tmp_name = tempfile.mkstemp(dir=CONFIG_DIR, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(json.dumps(document, indent=4))
        os.replace(tmp_name, path)
    finally:
        if os.path.exists(tmp_name):
            os.remove(tmp_name)


def load_config(config_name: str) -> CombinedConfig:
    path = _config_path(config_name)
    if not path.is_file():
        raise FileNotFoundError(f"Config '{config_name}' not found at {path}")

    try:
        document = json.loads(path.read_text(encoding="utf-8"))
        settings_from_document(document)
        if isinstance(document, dict):
            document.pop(QUALITY_GRADE_SETTINGS_KEY, None)
        return CombinedConfig.model_validate(document)
    except (json.JSONDecodeError, ValidationError, ValueError) as exc:
        raise ConfigLoadError(f"Config '{config_name}' is invalid: {exc}") from exc


def config_exists(config_name: str) -> bool:
    return _config_path(config_name).is_file()


def list_configs() -> list[str]:
    if not CONFIG_DIR.is_dir():
        return []
    return sorted(p.stem for p in CONFIG_DIR.glob("*.json"))
