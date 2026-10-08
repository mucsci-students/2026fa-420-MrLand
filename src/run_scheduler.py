"""Backward-compatible API for the CLI schedule controller."""

from pathlib import Path
import sys

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.controllers.run_scheduler_controller import (
    confirm_yes_no,
    run_scheduler as _run_scheduler,
)
from src.models.configuration_model import (
    config_exists,
    load_config as config_load,
)
from scheduler.scheduler import Scheduler

if __package__:
    from .models.schedule_result import ScheduleResult
else:
    from models.schedule_result import ScheduleResult


def run_scheduler(schedules):
    return _run_scheduler(
        schedules,
        config_loader=config_load,
        exists_checker=config_exists,
        scheduler_factory=Scheduler,
        result_type=ScheduleResult,
    )