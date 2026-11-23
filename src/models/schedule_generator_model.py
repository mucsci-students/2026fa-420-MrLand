"""Stores generation state, runs scheduling, and prepares schedule exports.

Used by: GUI."""

import json
import threading
from dataclasses import dataclass, replace
from typing import Protocol

from scheduler.config import CombinedConfig
from scheduler.contracts import ScheduleDiagnosis
from scheduler.scheduler import Scheduler

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
    diagnosis: ScheduleDiagnosis | None = None
    generation_id: int = 0


class GenerationPhase(Protocol):
    """State-pattern interface for generation lifecycle phases."""

    def enter(self, state: ScheduleGenerationState) -> None: ...


class IdleGenerationPhase:
    def enter(self, state: ScheduleGenerationState) -> None:
        state.running = False
        state.finished = False
        state.diagnosing = False
        state.cancel_requested = False
        state.diagnosis_cancelled = False
        state.error = None


class RunningGenerationPhase:
    def enter(self, state: ScheduleGenerationState) -> None:
        state.running = True
        state.finished = False
        state.diagnosing = False
        state.cancel_requested = False
        state.diagnosis_cancelled = False
        state.error = None


class DiagnosingGenerationPhase:
    def enter(self, state: ScheduleGenerationState) -> None:
        state.running = True
        state.finished = False
        state.diagnosing = True
        state.cancel_requested = False
        state.diagnosis_cancelled = False
        state.error = None


class FinishedGenerationPhase:
    def enter(self, state: ScheduleGenerationState) -> None:
        state.running = False
        state.finished = True
        state.diagnosing = False
        state.cancel_requested = False
        state.diagnosis_cancelled = False
        state.error = None


class CancelledGenerationPhase:
    def enter(self, state: ScheduleGenerationState) -> None:
        state.running = False
        state.finished = True
        state.diagnosing = False
        state.cancel_requested = False
        state.diagnosis_cancelled = True
        state.error = None


class FailedGenerationPhase:
    def enter(self, state: ScheduleGenerationState) -> None:
        state.running = False
        state.finished = True
        state.diagnosing = False
        state.cancel_requested = False
        state.diagnosis_cancelled = False


class ScheduleGeneratorModel:
    """Own schedule-generation data, status, and serialization."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._state = ScheduleGenerationState()
        self._phase: GenerationPhase = IdleGenerationPhase()
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

    def update_state(
        self,
        *,
        running: bool | None = None,
        finished: bool | None = None,
        diagnosing: bool | None = None,
        cancel_requested: bool | None = None,
        diagnosis_cancelled: bool | None = None,
        error: str | None = None,
        config_name: str | None = None,
        requested: int | None = None,
        generated: int | None = None,
        valid: int | None = None,
        message: str | None = None,
        diagnosis: ScheduleDiagnosis | None = None,
        generation_id: int | None = None,
    ) -> None:
        with self._lock:
            if running is not None:
                self._state.running = running
            if finished is not None:
                self._state.finished = finished
            if diagnosing is not None:
                self._state.diagnosing = diagnosing
            if cancel_requested is not None:
                self._state.cancel_requested = cancel_requested
            if diagnosis_cancelled is not None:
                self._state.diagnosis_cancelled = diagnosis_cancelled
            if error is not None:
                self._state.error = error
            if config_name is not None:
                self._state.config_name = config_name
            if requested is not None:
                self._state.requested = requested
            if generated is not None:
                self._state.generated = generated
            if valid is not None:
                self._state.valid = valid
            if message is not None:
                self._state.message = message
            if diagnosis is not None:
                self._state.diagnosis = diagnosis
            if generation_id is not None:
                self._state.generation_id = generation_id
            self._reconcile_phase_locked()

    def _transition_phase_locked(self, phase: GenerationPhase) -> None:
        self._phase = phase
        phase.enter(self._state)

    def _reconcile_phase_locked(self) -> None:
        if self._state.diagnosis_cancelled:
            self._phase = CancelledGenerationPhase()
        elif self._state.error is not None:
            self._phase = FailedGenerationPhase()
        elif self._state.finished:
            self._phase = FinishedGenerationPhase()
        elif self._state.diagnosing:
            self._phase = DiagnosingGenerationPhase()
        elif self._state.running:
            self._phase = RunningGenerationPhase()
        else:
            self._phase = IdleGenerationPhase()

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
            self._transition_phase_locked(RunningGenerationPhase())
            return True

    def cancel_diagnosis(self) -> bool:
        with self._lock:
            if not self._state.running or not self._state.diagnosing:
                return False

            self._cancel_diagnosis_requested = True
            self._state.cancel_requested = True
            self._state.message = "Stopping diagnosis..."
            if self._active_scheduler is not None:
                diagnostics = getattr(self._active_scheduler, "_diagnostics", None)
                context = getattr(diagnostics, "_ctx", None)
                interrupt = getattr(context, "interrupt", None)
                if callable(interrupt):
                    interrupt()
            return True

    def _finish_cancelled_diagnosis(self) -> None:
        self._cancel_diagnosis_requested = False
        self._transition_phase_locked(CancelledGenerationPhase())
        self._state.generated = 0
        self._state.valid = 0
        self._state.message = "No valid schedules could be generated."
        self._state.diagnosis = None
        self._active_scheduler = None

    def generate_configuration(self, config_name: str, config: CombinedConfig) -> None:
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
                        self._transition_phase_locked(FinishedGenerationPhase())
                        self._state.message = "No valid schedules could be generated."
                        self._state.diagnosis = diagnosis
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
                self._transition_phase_locked(FinishedGenerationPhase())
                self._state.generated = len(generated)
                self._state.valid = valid_count
                self._state.message = f"Generated {len(generated)} of {limit} schedules."
                self._active_scheduler = None
        except Exception as error:  # noqa: BLE001 - worker boundary must publish scheduler failures
            with self._lock:
                if self._cancel_diagnosis_requested and self._state.diagnosing:
                    self._finish_cancelled_diagnosis()
                else:
                    self._transition_phase_locked(FailedGenerationPhase())
                    self._state.error = str(error)
                    self._state.message = "Schedule generation failed."
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
