from dataclasses import dataclass
import copy
import json
from pathlib import Path
from typing import Callable, TypeVar

from jsonschema import Draft202012Validator, FormatChecker
from pydantic import ValidationError

from scheduler.config import CombinedConfig

from src.models.configuration_repository import (
    clean_config_name,
    config_exists,
    list_configs,
    load_config,
    save_config,
)

T = TypeVar("T")
_CONFIG_SCHEMA_PATH = (
    Path(__file__).resolve().parents[1]
    / "schemas"
    / "combined-config.schema.json"
)
with _CONFIG_SCHEMA_PATH.open(encoding="utf-8") as schema_file:
    _CONFIG_SCHEMA = json.load(schema_file)
Draft202012Validator.check_schema(_CONFIG_SCHEMA)
_CONFIG_SCHEMA_VALIDATOR = Draft202012Validator(
    _CONFIG_SCHEMA,
    format_checker=FormatChecker(),
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

    Checks the published JSON Schema first, then applies the scheduler model's
    cross-field and cross-reference validation. Never modifies `config`.
    """
    problems: list[ValidationProblem] = []
    payload = config.model_dump(mode="json", warnings=False)
    schema_errors = sorted(
        _CONFIG_SCHEMA_VALIDATOR.iter_errors(payload),
        key=lambda error: tuple(str(part) for part in error.absolute_path),
    )
    for error in schema_errors:
        area, item, field = _describe(config, tuple(error.absolute_path))
        message = error.message
        if field:
            message = f"{field}: {message}"
        problems.append(ValidationProblem(area, item, message))

    try:
        CombinedConfig.model_validate_json(config.model_dump_json(warnings=False))
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


def apply_configuration_change(
    config: CombinedConfig,
    mutation: Callable[[], T],
    *,
    has_valid_baseline: bool,
) -> tuple[bool, list[ValidationProblem], T | None]:
    """Apply one edit and restore it when it invalidates a valid configuration.

    Incomplete new drafts may be edited until their first valid state. Every
    mutation is validated against the whole configuration before it is accepted.
    """
    previous_config = copy.deepcopy(config)
    try:
        result = mutation()
        problems = validate_config(config)
    except Exception:
        _restore_config(config, previous_config)
        raise

    if problems and has_valid_baseline:
        _restore_config(config, previous_config)
        return False, problems, None
    return True, problems, result


def _restore_config(config: CombinedConfig, snapshot: CombinedConfig) -> None:
    object.__setattr__(config, "__dict__", snapshot.__dict__)
    object.__setattr__(
        config, "__pydantic_fields_set__", snapshot.__pydantic_fields_set__
    )
    object.__setattr__(
        config, "__pydantic_extra__", snapshot.__pydantic_extra__
    )
    object.__setattr__(
        config, "__pydantic_private__", snapshot.__pydantic_private__
    )


class ConfigService:
    def save(self, config: CombinedConfig, config_name: str) -> None:
        save_config(config, clean_config_name(config_name))

    def load(self, config_name: str) -> CombinedConfig:
        return load_config(config_name)

    def exists(self, config_name: str) -> bool:
        return config_exists(config_name)

    def list_names(self) -> list[str]:
        return list_configs()