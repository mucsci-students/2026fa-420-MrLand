import os

import scheduler.configuration as configuration
from scheduler.config import CombinedConfig

filepath = os.path.join("src", "configs")



def _config_path(config_name: str) -> str:
    return os.path.join(filepath, f"{config_name}.json")


def config_save(combined_config: CombinedConfig, config_name: str) -> None:
    """Save CombinedConfig Object to JSON file"""
    os.makedirs(filepath, exist_ok=True)
    path = _config_path(config_name)

    with open(path, "w", encoding="utf-8") as config_file:
        config_file.write(combined_config.model_dump_json(indent=4))


def config_load(config_name: str) -> CombinedConfig:
    """Load CombinedConfig Object from JSON file"""
    path = _config_path(config_name)

    if not os.path.isfile(path):
        raise FileNotFoundError(f"Config '{config_name}' not found at {path}")

    return configuration.load_config_from_file(CombinedConfig, path)


def config_print(combined_config: CombinedConfig) -> None:
    """Print CombinedConfig Object"""
    print(combined_config.model_dump_json(indent=4))


def config_exists(config_name: str) -> bool:
    """Check if CombinedConfig Object exists in JSON file"""
    return os.path.isfile(_config_path(config_name))