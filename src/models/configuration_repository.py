import json
import os
import re
import tempfile
from pathlib import Path

from pydantic import ValidationError

from scheduler.config import CombinedConfig
import scheduler.configuration as configuration


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


def save_config(combined_config: CombinedConfig, config_name: str) -> None:
    path = _config_path(config_name)
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    # Write to a temp file in the same directory, then atomically swap it in,
    # so a crash mid-write can't corrupt an existing config.
    fd, tmp_name = tempfile.mkstemp(dir=CONFIG_DIR, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(combined_config.model_dump_json(indent=4))
        os.replace(tmp_name, path)
    except BaseException:
        if os.path.exists(tmp_name):
            os.remove(tmp_name)
        raise


def load_config(config_name: str) -> CombinedConfig:
    path = _config_path(config_name)
    if not path.is_file():
        raise FileNotFoundError(f"Config '{config_name}' not found at {path}")

    try:
        return configuration.load_config_from_file(CombinedConfig, str(path))
    except (json.JSONDecodeError, ValidationError) as exc:
        raise ConfigLoadError(
            f"Config '{config_name}' is invalid: {exc}"
        ) from exc


def config_exists(config_name: str) -> bool:
    return _config_path(config_name).is_file()


def list_configs() -> list[str]:
    if not CONFIG_DIR.is_dir():
        return []
    return sorted(p.stem for p in CONFIG_DIR.glob("*.json"))