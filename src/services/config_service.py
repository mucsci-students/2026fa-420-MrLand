from scheduler.config import CombinedConfig

from src.services.config_io import (
    clean_config_name,
    config_exists,
    list_configs,
    load_config,
    save_config,
)


def validate_config_name(name: str) -> str:
    """For creating a NEW config: a valid name that isn't already taken."""
    name = clean_config_name(name)
    if config_exists(name):
        raise ValueError(
            f"A configuration named '{name}' already exists. "
            "Load it instead, or choose a different name."
        )
    return name


class ConfigService:
    def save(self, config: CombinedConfig, config_name: str) -> None:
        save_config(config, clean_config_name(config_name))

    def load(self, config_name: str) -> CombinedConfig:
        return load_config(config_name)

    def exists(self, config_name: str) -> bool:
        return config_exists(config_name)

    def list_names(self) -> list[str]:
        return list_configs()