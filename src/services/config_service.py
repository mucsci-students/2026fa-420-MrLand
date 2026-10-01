from scheduler.config import CombinedConfig
from pydantic import ValidationError
import re

from src.services.config_io import (
    config_exists,
    load_config,
    save_config,
)


class ConfigService:

    def save(
        self,
        config: CombinedConfig,
        config_name: str,
    ) -> None:
        save_config(config, config_name)
_CONFIG_NAME_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 _-]{0,63}$")


def validate_config_name(name: str) -> str:
    """Return a cleaned config name, or raise ValueError explaining what's wrong."""
    name = name.strip()
    if not name:
        raise ValueError("Configuration name cannot be empty.")
    if not _CONFIG_NAME_PATTERN.match(name):
        raise ValueError(
            "Use letters, numbers, spaces, hyphens, or underscores "
            "(start with a letter or number, max 64 characters)."
        )
    if config_exists(name):
        raise ValueError(
            f"A configuration named '{name}' already exists. "
            "Load it instead, or choose a different name."
        )
    return name


    def load(
        self,
        config_name: str,
    ) -> CombinedConfig:
        return load_config(config_name)

    def exists(
        self,
        config_name: str,
    ) -> bool:
        return config_exists(config_name)
