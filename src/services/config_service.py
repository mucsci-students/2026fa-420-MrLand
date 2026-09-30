from scheduler.config import CombinedConfig

from services.config_io import (
    config_exists,
    load_config,
    save_config,
)


class ConfigService:

    def save(
        self,
        config: CombinedConfig,
        config_name: str,
    ) -> None:
        save_config(config, config_name)

    def load(
        self,
        config_name: str,
    ) -> CombinedConfig:
        return load_config(config_name)

    def exists(
        self,
        config_name: str,
    ) -> bool:
        return config_exists(config_name)
