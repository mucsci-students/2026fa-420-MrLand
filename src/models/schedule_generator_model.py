import json
import os
import threading
from dataclasses import dataclass, replace
from typing import Any

from scheduler.scheduler import Scheduler
from schedule_result import ScheduleResult
from services.config_service import config_exists, load_config


@dataclass
class ScheduleGenerationState:
    running: bool = False
    finished: bool = False
    error: str | None = None
    config_name: str | None = None
    requested: int = 0
    generated: int = 0
    valid: int = 0
    message: str = ""
    diagnosis: Any | None = None


class ScheduleGeneratorModel:
    """Own schedule-generation data, status, and serialization."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._state = ScheduleGenerationState()
        self._generated_schedules: list[ScheduleResult] = []

    @property
    def generated_schedules(self) -> list[ScheduleResult]:
        with self._lock:
            return list(self._generated_schedules)

    def state_snapshot(self) -> ScheduleGenerationState:
        with self._lock:
            return replace(self._state)

    def list_config_names(self) -> list[str]:
        config_directory = os.path.join("src", "configs")
        try:
            return sorted(
                filename[:-5]
                for filename in os.listdir(config_directory)
                if filename.endswith(".json")
                and config_exists(filename[:-5])
            )
        except OSError:
            return []

    @staticmethod
    def load_config(config_name: str) -> Any:
        return load_config(config_name)

    def begin_generation(self, config_name: str, requested: int) -> bool:
        with self._lock:
            if self._state.running:
                return False

            self._generated_schedules.clear()
            self._state = ScheduleGenerationState(
                running=True,
                config_name=config_name,
                requested=requested,
                message="Starting scheduler...",
            )
            return True

    def update_state(self, **updates: Any) -> None:
        with self._lock:
            for name, value in updates.items():
                setattr(self._state, name, value)

    def generate(
        self,
        config_name: str,
        limit_override: int | None,
        optimizer_override: list[str] | None,
    ) -> None:
        """Generate schedules and publish progress without touching the UI."""
        try:
            self.update_state(
                config_name=config_name,
                message=f"Loading configuration '{config_name}'...",
            )
            full_config = self.load_config(config_name)

            if limit_override is not None:
                full_config.limit = limit_override
            if optimizer_override is not None:
                full_config.optimizer_flags = optimizer_override

            limit = full_config.limit
            self.update_state(
                requested=limit,
                message="Starting Z3 scheduler...",
            )

            scheduler = Scheduler(full_config)
            self.update_state(message="Generating schedules...")
            generated = []

            for schedule in scheduler.get_models():
                generated.append(schedule)
                count = len(generated)
                self.update_state(
                    generated=count,
                    message=(
                        f"Generated {count} of {limit} schedules. "
                        "Searching for another schedule..."
                    ),
                )
                if count >= limit:
                    break

            if not generated:
                diagnosis = scheduler.diagnose()
                self.update_state(
                    message="No valid schedules could be generated.",
                    diagnosis=diagnosis,
                    finished=True,
                    running=False,
                )
                return

            valid_count = sum(
                1
                for schedule in generated
                if scheduler.audit_schedule(schedule).is_valid
            )

            with self._lock:
                self._generated_schedules.extend(
                    ScheduleResult(config_name, schedule)
                    for schedule in generated
                )
                self._state.generated = len(generated)
                self._state.valid = valid_count
                self._state.message = (
                    f"Generated {len(generated)} of {limit} schedules."
                )
                self._state.finished = True
                self._state.running = False
        except Exception as error:
            self.update_state(
                error=str(error),
                message="Schedule generation failed.",
                finished=True,
                running=False,
            )

    @staticmethod
    def schedule_to_json(result: ScheduleResult, schedule_number: int) -> bytes:
        schedule_data = {
            "schedule": schedule_number,
            "config": result.config_name,
            "meetings": [
                {
                    "course": str(instance.course),
                    "faculty": str(instance.faculty),
                    "room": str(instance.room),
                    "lab": str(instance.lab),
                    "times": str(instance.times),
                }
                for instance in result.schedule
            ],
        }
        return json.dumps(schedule_data, indent=4).encode("utf-8")

    @staticmethod
    def schedule_to_csv(result: ScheduleResult, schedule_number: int) -> bytes:
        lines = ["schedule,config,course,faculty,room,lab,times"]
        for instance in result.schedule:
            row = [
                str(schedule_number),
                result.config_name,
                str(instance.course),
                str(instance.faculty),
                str(instance.room),
                str(instance.lab),
                str(instance.times),
            ]
            escaped_row = []
            for value in row:
                value = value.replace('"', '""')
                if any(character in value for character in [",", '"', "\n"]):
                    value = f'"{value}"'
                escaped_row.append(value)
            lines.append(",".join(escaped_row))
        return "\n".join(lines).encode("utf-8")
