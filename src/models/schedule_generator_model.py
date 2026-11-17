"""Stores generation state, runs scheduling, and prepares schedule exports.

Used by: GUI."""

import json
import threading
from dataclasses import dataclass, replace
from time import sleep
from typing import Any

from scheduler.scheduler import Scheduler

from src.models.configuration_model import load_config
from src.models.configuration_repository import ConfigLoadError, list_configs
from src.models.schedule_files import records_from_result, records_to_csv
from src.models.schedule_result import ScheduleResult


@dataclass
class ScheduleGenerationState:
    running: bool = False
    finished: bool = False
    diagnosing: bool = False
    cancel_requested: bool = False
    diagnosis_cancelled: bool = False
    error: str | None = None
    config_name: str | None = None
    requested: int = 0
    generated: int = 0
    valid: int = 0
    message: str = ""
    diagnosis: Any | None = None
    generation_id: int = 0


class ScheduleGeneratorModel:
    """Own schedule-generation data, status, and serialization."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._state = ScheduleGenerationState()
        self._generated_schedules: list[ScheduleResult] = []
        self._generation_id = 0
        self._active_scheduler: Scheduler | None = None
        self._cancel_diagnosis_requested = False

    @property
    def generated_schedules(self) -> list[ScheduleResult]:
        with self._lock:
            return list(self._generated_schedules)

    def state_snapshot(self) -> ScheduleGenerationState:
        with self._lock:
            return replace(self._state)

    def clear_generated_schedules(self) -> bool:
        """Clear published results unless a generation run is in progress."""
        with self._lock:
            if self._state.running:
                return False
            self._generated_schedules.clear()
            return True

    def list_config_names(self) -> list[str]:
        """List saved configurations from the shared, application-rooted repository."""
        return list_configs()

    @staticmethod
    def load_config(config_name: str) -> Any:
        return load_config(config_name)

    def begin_generation(self, config_name: str, requested: int) -> bool:
        with self._lock:
            if self._state.running:
                return False

            self._generation_id += 1
            self._generated_schedules.clear()
            self._active_scheduler = None
            self._cancel_diagnosis_requested = False
            self._state = ScheduleGenerationState(
                generation_id=self._generation_id,
                running=True,
                config_name=config_name,
                requested=requested,
                message="Starting scheduler...",
            )
            return True

    def cancel_diagnosis(self) -> bool:
        with self._lock:
            if not self._state.diagnosing or self._active_scheduler is None:
                return False
            scheduler = self._active_scheduler
            start_interrupt_worker = not self._cancel_diagnosis_requested
            self._cancel_diagnosis_requested = True
            self._state.cancel_requested = True

        try:
            scheduler._diagnostics._ctx.interrupt()
        except Exception:
            with self._lock:
                if self._active_scheduler is scheduler:
                    self._cancel_diagnosis_requested = False
                    self._state.cancel_requested = False
            raise

        if start_interrupt_worker:
            threading.Thread(
                target=self._interrupt_diagnosis_until_stopped,
                args=(scheduler,),
                daemon=True,
            ).start()
        return True

    def _interrupt_diagnosis_until_stopped(self, scheduler: Scheduler) -> None:
        while True:
            with self._lock:
                if (
                    not self._cancel_diagnosis_requested
                    or self._active_scheduler is not scheduler
                ):
                    return
            scheduler._diagnostics._ctx.interrupt()
            sleep(0.05)

    def _finish_cancelled_diagnosis(self) -> None:
        self._state.diagnosing = False
        self._state.cancel_requested = False
        self._state.diagnosis_cancelled = True
        self._state.diagnosis = None
        self._state.message = "No valid schedules could be generated."
        self._state.finished = True
        self._state.running = False
        self._cancel_diagnosis_requested = False
        self._active_scheduler = None

    def update_state(self, **updates: Any) -> None:
        with self._lock:
            for name, value in updates.items():
                setattr(self._state, name, value)

    def generate(
        self,
        config_name: str,
        limit_override: int | None,
        optimizer_override: list[str] | None,
        max_time_gap_override: int | None = None,
        min_time_overlap_override: int | None = None,
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
            if max_time_gap_override is not None:
                full_config.time_slot_config.max_time_gap = max_time_gap_override
            if min_time_overlap_override is not None:
                full_config.time_slot_config.min_time_overlap = min_time_overlap_override
        except (ConfigLoadError, FileNotFoundError, ValueError) as error:
            self.update_state(
                error=str(error),
                message="Schedule generation failed.",
                finished=True,
                running=False,
            )
            return
        self.generate_configuration(config_name, full_config)

    def generate_configuration(self, config_name: str, config: Any) -> None:
        """Generate from an in-memory config and publish results to viewers."""
        try:
            limit = config.limit
            self.update_state(
                config_name=config_name,
                requested=limit,
                message="Starting Z3 scheduler...",
            )

            scheduler = Scheduler(config)
            with self._lock:
                self._active_scheduler = scheduler
            self.update_state(message="Generating schedules...")
            generated = []

            for schedule in scheduler.get_models():
                generated.append(schedule)
                count = len(generated)
                self.update_state(
                    generated=count,
                    message=(
                        f"Generated {count} of {limit} schedules. Searching for another schedule..."
                    ),
                )
                if count >= limit:
                    break

            if not generated:
                self.update_state(
                    diagnosing=True,
                    message="No schedules found. Analyzing constraints...",
                )
                diagnosis = scheduler.diagnose()
                with self._lock:
                    if self._cancel_diagnosis_requested:
                        self._finish_cancelled_diagnosis()
                    else:
                        self._state.diagnosing = False
                        self._state.message = "No valid schedules could be generated."
                        self._state.diagnosis = diagnosis
                        self._state.finished = True
                        self._state.running = False
                        self._active_scheduler = None
                return

            valid_count = sum(
                1 for schedule in generated if scheduler.audit_schedule(schedule).is_valid
            )

            with self._lock:
                self._generated_schedules.extend(
                    ScheduleResult(
                        config_name=config_name,
                        schedule=schedule,
                        config=config,
                    )
                    for schedule in generated
                )
                self._state.generated = len(generated)
                self._state.valid = valid_count
                self._state.message = f"Generated {len(generated)} of {limit} schedules."
                self._state.finished = True
                self._state.running = False
                self._active_scheduler = None
        except Exception as error:  # noqa: BLE001 - worker boundary must publish scheduler failures
            with self._lock:
                if self._cancel_diagnosis_requested and self._state.diagnosing:
                    self._finish_cancelled_diagnosis()
                else:
                    self._state.diagnosing = False
                    self._state.error = str(error)
                    self._state.message = "Schedule generation failed."
                    self._state.finished = True
                    self._state.running = False
                    self._active_scheduler = None

    @staticmethod
    def schedule_to_json(result: ScheduleResult, schedule_number: int) -> bytes:
        schedule_data = {
            "schedule": schedule_number,
            "config": result.config_name,
            "meetings": records_from_result(result),
        }
        return json.dumps(schedule_data, indent=4).encode("utf-8")

    @staticmethod
    def schedule_to_csv(result: ScheduleResult, schedule_number: int) -> bytes:
        return records_to_csv(
            records_from_result(result),
            extra={"schedule": str(schedule_number), "config": result.config_name},
        )
