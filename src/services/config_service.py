from pydantic import ValidationError

from scheduler.config import CombinedConfig, SchedulerConfig, TimeSlotConfig
from services.config_io import (
    write_config_file,
    read_config_file,
    config_file_exists,
    print_config as print_config_io,
)


def create_draft_config() -> CombinedConfig:
    """Build an empty, unvalidated CombinedConfig to be filled in incrementally."""
    scheduler_config = SchedulerConfig.model_construct(
        rooms=[], labs=[], courses=[], faculty=[]
    )
    time_slot_config = TimeSlotConfig.model_construct(
        times={}, classes=[]
    )
    return CombinedConfig.model_construct(
        config=scheduler_config,
        time_slot_config=time_slot_config,
        limit=10,
        optimizer_flags=[],
    )


def save_config(combined_config: CombinedConfig, config_name: str) -> bool:
    """Validate a draft config fully before persisting it. Returns True on success."""
    try:
        validated = CombinedConfig.model_validate(combined_config.model_dump())
    except ValidationError as e:
        print("Cannot save — configuration is incomplete or invalid:")
        for err in e.errors():
            field = ".".join(str(loc) for loc in err["loc"])
            print(f"  - {field}: {err['msg']}")
        return False

    write_config_file(validated, config_name)
    print(f"Configuration '{config_name}' saved successfully.")
    return True


def load_config(config_name: str) -> CombinedConfig:
    """Load a previously saved (and therefore already-valid) config."""
    return read_config_file(config_name)


def config_exists(config_name: str) -> bool:
    """Check whether a saved config with this name exists."""
    return config_file_exists(config_name)


def print_config(combined_config: CombinedConfig) -> None:
    """Print a CombinedConfig object as formatted JSON."""
    print_config_io(combined_config)