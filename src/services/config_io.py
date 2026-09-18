import os

import scheduler.configuration as configuration
from scheduler.config import CombinedConfig

filepath = os.path.join("src", "configs")


def _config_path(config_name: str) -> str:
    return os.path.join(filepath, f"{config_name}.json")


def write_config_file(combined_config: CombinedConfig, config_name: str) -> None:
    """Write a CombinedConfig object to a JSON file."""
    os.makedirs(filepath, exist_ok=True)
    path = _config_path(config_name)

    with open(path, "w", encoding="utf-8") as config_file:
        config_file.write(combined_config.model_dump_json(indent=4))


def read_config_file(config_name: str) -> CombinedConfig:
    """Read a CombinedConfig object from a JSON file."""
    path = _config_path(config_name)

    if not os.path.isfile(path):
        raise FileNotFoundError(f"Config '{config_name}' not found at {path}")

    return configuration.load_config_from_file(CombinedConfig, path)


def print_config(combined_config: CombinedConfig) -> None:
    """Print a CombinedConfig object as formatted JSON."""
    print(combined_config.model_dump_json(indent=4))


def config_file_exists(config_name: str) -> bool:
    """Check whether a config JSON file exists on disk."""
    return os.path.isfile(_config_path(config_name))