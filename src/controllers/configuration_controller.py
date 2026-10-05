from scheduler.config import CombinedConfig

from src.services.config_service import ConfigService, ConfigValidationError, ValidationProblem, validate_config
from scheduler.config import CombinedConfig, SchedulerConfig, TimeSlotConfig


class ConfigurationController:

    def __init__(self) -> None:
        self.config_service = ConfigService()
        self.configuration: CombinedConfig | None = None

    def new_configuration(self) -> CombinedConfig:
        # model_construct skips validation: an empty config can't pass the
        # library's rules yet. Validate/Save check it once it's filled in.
        self.configuration = CombinedConfig.model_construct(
            config=SchedulerConfig.model_construct(
                rooms=[], labs=[], courses=[], faculty=[]
            ),
            time_slot_config=TimeSlotConfig.model_construct(times={}, classes=[]),
            limit=10,
            optimizer_flags=[],
        )
        return self.configuration

    def save_configuration(self, config_name: str) -> None:
        if self.configuration is None:
            raise ValueError("No configuration has been created.")
        problems = self.validate_configuration()
        if problems:
            raise ConfigValidationError(problems)
        self.config_service.save(self.configuration, config_name)

    def load_configuration(self, config_name: str) -> CombinedConfig:
        self.configuration = self.config_service.load(config_name)
        return self.configuration

    def list_names(self) -> list[str]:
        return self.config_service.list_names()

    def validate_configuration(self) -> list[ValidationProblem]:
        if self.configuration is None:
            raise ValueError("No configuration has been created or loaded.")
        return validate_config(self.configuration)