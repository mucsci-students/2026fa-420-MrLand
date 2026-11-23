"""Validate names used for downloaded configuration files."""

import re

_CONFIG_NAME_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 _-]{0,63}$")


def clean_config_name(name: str) -> str:
    """Return a cleaned name, or raise ValueError."""
    name = name.strip()
    if not name:
        raise ValueError("Configuration name cannot be empty.")
    if not _CONFIG_NAME_PATTERN.match(name):
        raise ValueError(
            "Use letters, numbers, spaces, hyphens, or underscores "
            "(start with a letter or number, max 64 characters)."
        )
    return name
