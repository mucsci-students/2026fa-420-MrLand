from dataclasses import dataclass, field
from typing import Optional

from scheduler.config import CombinedConfig
from scheduler.models import CourseInstance  # adjust import path once confirmed


@dataclass
class ConfigState:
    """Holds the in-progress configuration draft and any generated schedules
    for the current session."""

    draft_config: Optional[CombinedConfig] = None
    config_name: Optional[str] = None
    schedules: list[list[CourseInstance]] = field(default_factory=list)


state = ConfigState()