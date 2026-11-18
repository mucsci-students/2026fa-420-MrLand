"""Pydantic argument schemas for scheduler assistant tools."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from src.ai.agent_tool_types import JsonObject


class InspectConfigurationArgs(BaseModel):
    area: Literal[
        "all",
        "rooms",
        "labs",
        "courses",
        "faculty",
        "class_patterns",
        "meetings",
        "time_blocks",
        "global_settings",
    ] = Field(default="all", description="Configuration area to inspect")


class ConfigurationItemArgs(BaseModel):
    area: Literal[
        "rooms", "labs", "courses", "faculty", "class_patterns", "meetings", "time_blocks"
    ] = Field(description="Configuration area containing the item")
    item_key: str | None = Field(
        default=None,
        description=(
            "Existing item key for update/delete; weekday for time_blocks; "
            "course keys can use COURSE_ID::SECTION_ID; meetings use "
            "CLASS_PATTERN_INDEX::DAY; create meetings with the class-pattern index"
        ),
    )
    item: JsonObject = Field(
        description="Item fields as a JSON object; time_blocks uses {'blocks': [...]}."
    )


class DeleteConfigurationItemArgs(BaseModel):
    area: Literal[
        "rooms", "labs", "courses", "faculty", "class_patterns", "meetings", "time_blocks"
    ] = Field(description="Configuration area containing the item")
    item_key: str = Field(
        description=(
            "Item name, course ID or COURSE_ID::SECTION_ID, zero-based pattern "
            "index, or weekday for time_blocks"
            "; meetings use CLASS_PATTERN_INDEX::DAY"
        )
    )


class ConfigurationSettingsArgs(BaseModel):
    limit: int | None = Field(default=None, description="Positive maximum schedules to generate")
    optimizer_flags: list[str] | None = Field(
        default=None, description="Scheduler optimization flags"
    )
    max_time_gap: int | None = Field(
        default=None, description="Maximum adjacent-meeting gap in minutes"
    )
    min_time_overlap: int | None = Field(
        default=None, description="Minimum overlap between class patterns in minutes"
    )


class SaveConfigurationArgs(BaseModel):
    config_name: str = Field(description="Name for the saved JSON configuration")


class CombinationPasswordArgs(BaseModel):
    password: str = Field(
        description="Password provided by the user to authorize listing combinations"
    )
