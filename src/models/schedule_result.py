# schedule_result.py

from dataclasses import dataclass
from scheduler.models.course import CourseInstance


@dataclass
class ScheduleResult:
    """A single generated schedule, tagged with the config it came from."""
    config_name: str
    schedule: list[CourseInstance]