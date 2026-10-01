import json
from pathlib import Path

from scheduler.config import CombinedConfig
import scheduler.configuration as configuration


CONFIG_DIR = Path(__file__).resolve().parent.parent / "configs"


def _config_path(config_name: str) -> Path:
    return CONFIG_DIR / f"{config_name}.json"


def save_config(
    combined_config: CombinedConfig,
    config_name: str,
) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    path = _config_path(config_name)

    with path.open("w", encoding="utf-8") as config_file:
        config_file.write(
            combined_config.model_dump_json(indent=4)
        )


def load_config(config_name: str) -> CombinedConfig:
    path = _config_path(config_name)

    if not path.is_file():
        raise FileNotFoundError(
            f"Config '{config_name}' not found at {path}"
        )

    return configuration.load_config_from_file(
        CombinedConfig,
        str(path),
    )


def config_exists(config_name: str) -> bool:
    return _config_path(config_name).is_file()
