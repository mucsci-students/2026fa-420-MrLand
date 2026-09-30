from scheduler.config import CombinedConfig

from src.services.config_service import ConfigService


class ConfigurationController:

    def __init__(self) -> None:
        self.config_service = ConfigService()
        self.configuration: CombinedConfig | None = None

    def create_configuration(
        self,
        configuration: CombinedConfig,
    ) -> None:
        self.configuration = configuration

    def save_configuration(
        self,
        config_name: str,
    ) -> None:
        if self.configuration is None:
            raise ValueError("No configuration has been created.")

        self.config_service.save(
            self.configuration,
            config_name,
        )

    def load_configuration(
        self,
        config_name: str,
    ) -> CombinedConfig:
        self.configuration = self.config_service.load(
            config_name
        )

        return self.configuration
