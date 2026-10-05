from scheduler.config import CombinedConfig
from dataclasses import dataclass
from pydantic import ValidationError

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

@dataclass(frozen=True)
class ValidationProblem:
    area: str          # e.g. "Courses"
    item: str | None   # e.g. "CS 121", or None for the whole area
    message: str


class ConfigValidationError(Exception):
    """Raised when a config can't be saved because it has problems."""

    def __init__(self, problems: list[ValidationProblem]) -> None:
        super().__init__(f"{len(problems)} validation problem(s)")
        self.problems = problems


_AREAS = {
    ("config", "rooms"): "Rooms",
    ("config", "labs"): "Labs",
    ("config", "courses"): "Courses",
    ("config", "faculty"): "Faculty",
    ("time_slot_config", "times"): "Time blocks",
    ("time_slot_config", "classes"): "Class patterns",
}


def _item_label(config: CombinedConfig, loc: tuple) -> str | None:
    """Turn a list position into a readable name, like 'CS 121' or 'Room 101'."""
    if len(loc) < 3:
        return None
    if loc[1] == "times":                      # time blocks are keyed by day
        return str(loc[2])
    if not isinstance(loc[2], int):
        return None
    try:
        item = getattr(getattr(config, loc[0]), loc[1])[loc[2]]
    except (AttributeError, IndexError, TypeError):
        return f"#{loc[2] + 1}"
    if getattr(item, "course_id", None):
        section = getattr(item, "section_id", None)
        return f"{item.course_id} {section}" if section else item.course_id
    if getattr(item, "name", None):
        return item.name
    if getattr(item, "credits", None) is not None:
        return f"{item.credits}-credit pattern"
    return f"#{loc[2] + 1}"


def _describe(config: CombinedConfig, loc: tuple) -> tuple[str, str | None, str]:
    """Map a Pydantic error location to (area, item, field)."""
    if loc[:2] in _AREAS:
        rest = loc[3:] if len(loc) > 2 else ()
        field = ".".join(str(part) for part in rest if not isinstance(part, int))
        return _AREAS[loc[:2]], _item_label(config, loc), field.replace("_", " ")
    if loc and loc[0] in ("limit", "optimizer_flags"):
        return "Global settings", None, str(loc[0]).replace("_", " ")
    if loc and loc[0] == "time_slot_config":
        return "Time slots", None, ""
    if loc and loc[0] == "config":
        return "Configuration data", None, ""
    return "Whole configuration", None, ""


def validate_config(config: CombinedConfig) -> list[ValidationProblem]:
    """Check the whole configuration. Returns an empty list if it's valid.

    Uses the same save -> load round trip the app relies on, so
    "validates" means "will save and load back correctly".
    Never modifies `config`.
    """
    problems: list[ValidationProblem] = []
    try:
        CombinedConfig.model_validate_json(config.model_dump_json())
    except ValidationError as exc:
        for error in exc.errors():
            area, item, field = _describe(config, tuple(error["loc"]))
            if error["type"] == "too_short":
                message = "This can't be empty. Add at least one."
            else:
                message = error["msg"].removeprefix("Value error, ")
            if field:
                message = f"{field}: {message}"
            problems.append(ValidationProblem(area, item, message))
    except Exception as exc:  # anything else the library raises
        problems.append(ValidationProblem("Whole configuration", None, str(exc)))
        return problems

    return problems

class ConfigService:
    def save(self, config: CombinedConfig, config_name: str) -> None:
        save_config(config, clean_config_name(config_name))

    def load(self, config_name: str) -> CombinedConfig:
        return load_config(config_name)

    def exists(self, config_name: str) -> bool:
        return config_exists(config_name)

    def list_names(self) -> list[str]:
        return list_configs()