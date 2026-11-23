"""Shared types used by scheduler assistant tools."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Literal, Protocol, TypedDict, TypeVar

from scheduler.config import (
    ClassPattern,
    CombinedConfig,
    CourseConfig,
    FacultyConfig,
    LabConfig,
    RoomConfig,
)

from src.models.schedule_generator_model import ScheduleGenerationState

type JsonValue = str | int | float | bool | None | Sequence[JsonValue] | Mapping[str, JsonValue]
type JsonObject = dict[str, JsonValue]
type ConfigurationItem = RoomConfig | LabConfig | CourseConfig | FacultyConfig | ClassPattern
type ConfigurationItemCollection = (
    list[RoomConfig]
    | list[LabConfig]
    | list[CourseConfig]
    | list[FacultyConfig]
    | list[ClassPattern]
)
ConfigurationItemType = TypeVar("ConfigurationItemType", bound=ConfigurationItem)


class ToolResultDetails(TypedDict, total=False):
    action: str
    combinations: object
    data: object
    save_destination: Literal["download"]
    errors: object
    generated: int
    valid: int
    warnings: object


class ToolResult(ToolResultDetails):
    success: bool
    message: str


class ScheduleGenerator(Protocol):
    def generate_active_configuration(
        self, config: CombinedConfig
    ) -> tuple[ScheduleGenerationState | None, str | None]: ...
