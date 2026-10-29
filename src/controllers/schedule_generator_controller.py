"""Validates and coordinates background schedule generation.

Used by: GUI."""

import copy
import threading

from scheduler.config import CombinedConfig, OptimizerFlags

from src.models.configuration_repository import ConfigLoadError
from src.models.schedule_generator_model import (
    ScheduleGenerationState,
    ScheduleGeneratorModel,
)


class ScheduleGeneratorController:
    """Validate generator requests and coordinate background generation."""

    def __init__(self, model: ScheduleGeneratorModel | None = None) -> None:
        self.model = model or ScheduleGeneratorModel()

    @property
    def generated_schedules(self):
        return self.model.generated_schedules

    def list_config_names(self) -> list[str]:
        return self.model.list_config_names()

    def load_config(self, config_name: str):
        return self.model.load_config(config_name)

    def state_snapshot(self) -> ScheduleGenerationState:
        return self.model.state_snapshot()

    def clear_generated_schedules(self) -> bool:
        return self.model.clear_generated_schedules()

    def schedule_to_json(self, result, schedule_number: int) -> bytes:
        return self.model.schedule_to_json(result, schedule_number)

    def schedule_to_csv(self, result, schedule_number: int) -> bytes:
        return self.model.schedule_to_csv(result, schedule_number)

    def generate_active_configuration(
        self, config, config_name: str = "active configuration"
    ) -> tuple[ScheduleGenerationState | None, str | None]:
        if self.model.state_snapshot().running:
            return None, "Generation is already in progress. Please wait for it to finish."

        if not self.model.begin_generation(config_name, config.limit):
            return None, "Generation is already in progress. Please wait for it to finish."

        self.model.generate_configuration(config_name, config)
        state = self.model.state_snapshot()
        return state, state.error

    def start_generation(
        self,
        config_name: str | None,
        limit_override_value: str | float | None,
        optimizer_override: list[str] | None,
        max_time_gap_override_value: str | float | None = None,
        min_time_overlap_override_value: str | float | None = None,
        loaded_config: CombinedConfig | None = None,
    ) -> tuple[int | None, str | None]:
        if self.model.state_snapshot().running:
            return None, "Generation is already in progress. Please wait for it to finish."
        if not config_name:
            return None, "Please select a configuration."

        limit_override, error = self._parse_positive_integer_override(
            limit_override_value, "generation limit"
        )
        if error:
            return None, error
        max_time_gap_override, error = self._parse_positive_integer_override(
            max_time_gap_override_value, "maximum time gap"
        )
        if error:
            return None, error
        min_time_overlap_override, error = self._parse_positive_integer_override(
            min_time_overlap_override_value, "minimum time overlap"
        )
        if error:
            return None, error

        if loaded_config is None:
            try:
                config = self.model.load_config(config_name)
            except (ConfigLoadError, FileNotFoundError, ValueError) as error:
                return None, f"Could not load configuration: {error}"
        else:
            config = copy.deepcopy(loaded_config)

        requested = limit_override if limit_override is not None else config.limit
        if loaded_config is not None:
            config.limit = requested
            if optimizer_override is not None:
                config.optimizer_flags = [OptimizerFlags(flag) for flag in optimizer_override]
            if max_time_gap_override is not None:
                config.time_slot_config.max_time_gap = max_time_gap_override
            if min_time_overlap_override is not None:
                config.time_slot_config.min_time_overlap = min_time_overlap_override

        if not self.model.begin_generation(config_name, requested):
            return None, None

        if loaded_config is not None:
            worker = threading.Thread(
                target=self.model.generate_configuration,
                args=(config_name, config),
                daemon=True,
            )
            worker.start()
            return requested, None

        generation_args = (
            config_name,
            limit_override,
            optimizer_override,
        )
        if (
            max_time_gap_override is not None
            or min_time_overlap_override is not None
        ):
            generation_args += (
                max_time_gap_override,
                min_time_overlap_override,
            )

        worker = threading.Thread(
            target=self.model.generate,
            args=generation_args,
            daemon=True,
        )
        worker.start()
        return requested, None

    @staticmethod
    def _parse_positive_integer_override(
        value: str | float | None, setting_name: str
    ) -> tuple[int | None, str | None]:
        if value is None or not str(value).strip():
            return None, None

        error_message = (
            f"Temporary {setting_name} must be a positive whole number."
        )
        try:
            parsed_value = int(value)
        except (OverflowError, TypeError, ValueError):
            return None, error_message

        if parsed_value <= 0:
            return None, error_message
        return parsed_value, None


schedule_generator_controller = ScheduleGeneratorController()
