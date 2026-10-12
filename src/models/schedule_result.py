"""Data model associating a generated schedule with its source configuration.

Used by: GUI and CLI."""

# schedule_result.py

from dataclasses import dataclass
from scheduler.config import CombinedConfig
from scheduler.models.course import CourseInstance


@dataclass
class ScheduleResult:
    """A single generated schedule, tagged with the config it came from."""
    config_name: str
    schedule: list[CourseInstance]
    config: CombinedConfig | None = None
