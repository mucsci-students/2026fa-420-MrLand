import threading

from models.schedule_generator_model import (
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

    def schedule_to_json(self, result, schedule_number: int) -> bytes:
        return self.model.schedule_to_json(result, schedule_number)

    def schedule_to_csv(self, result, schedule_number: int) -> bytes:
        return self.model.schedule_to_csv(result, schedule_number)

    def start_generation(
        self,
        config_name: str | None,
        limit_override_value: object,
        optimizer_override: list[str] | None,
    ) -> tuple[int | None, str | None]:
        if self.model.state_snapshot().running:
            return None, None
        if not config_name:
            return None, "Please select a configuration."

        limit_override = None
        if limit_override_value is not None and str(limit_override_value).strip():
            try:
                limit_override = int(limit_override_value)
                if limit_override <= 0:
                    raise ValueError
            except (TypeError, ValueError):
                return None, (
                    "Temporary generation limit must be a positive whole number."
                )

        try:
            config = self.model.load_config(config_name)
        except Exception as error:
            return None, f"Could not load configuration: {error}"

        requested = limit_override if limit_override is not None else config.limit
        if not self.model.begin_generation(config_name, requested):
            return None, None

        worker = threading.Thread(
            target=self.model.generate,
            args=(config_name, limit_override, optimizer_override),
            daemon=True,
        )
        worker.start()
        return requested, None


schedule_generator_controller = ScheduleGeneratorController()
