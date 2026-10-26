"""LangChain wrapper for the course scheduler configuration.

This module intentionally keeps the scheduler logic in the domain model and
validation layer, while exposing a small set of safe operations as tools that the
LLM can call.
"""

from __future__ import annotations

import json
import os
from collections.abc import Callable
from typing import Any, Literal

from dotenv import load_dotenv
from pydantic import BaseModel, Field, ValidationError
from scheduler.config import (
    ClassPattern,
    CombinedConfig,
    CourseConfig,
    FacultyConfig,
    LabConfig,
    Meeting,
    RoomConfig,
    TimeBlock,
)
from src.controllers.schedule_generator_controller import (
    schedule_generator_controller,
)
from src.models.configuration_model import (
    ConfigService,
    ConfigValidationError,
    create_draft_config,
    validate_config,
)

try:
    from langchain.agents import create_agent
    from langchain.messages import HumanMessage
    from langchain_core.tools import StructuredTool
    from langchain_openai import ChatOpenAI
except ImportError as exc:  # pragma: no cover - dependency resolution is handled by uv
    raise RuntimeError(
        "LangChain AI dependencies are not installed. Run `uv sync` after adding "
        "the AI packages to pyproject.toml."
    ) from exc

load_dotenv()


# Return a valid draft config object that can be mutated safely.
def empty_scheduler_config() -> CombinedConfig:
    return create_draft_config()


class SchedulerAgentState:
    """Thin bridge between the AI and the scheduler configuration object."""

    def __init__(
        self,
        config: CombinedConfig | None = None,
        save_configuration: Callable[[str], None] | None = None,
        schedule_generator: Any | None = None,
        confirm_action: Callable[[str], bool] | None = None,
        configuration_exists: Callable[[str], bool] | None = None,
    ):
        self.config = config if config is not None else empty_scheduler_config()
        self.has_active_configuration = config is not None
        self._save_configuration = save_configuration
        self._schedule_generator = schedule_generator or schedule_generator_controller
        self._confirm_action = confirm_action
        self._configuration_exists = configuration_exists or ConfigService().exists

    @staticmethod
    def _result(success: bool, message: str, **details: Any) -> dict[str, Any]:
        return {"success": success, "message": message, **details}

    # Return the standard prompt shown when no configuration is active.
    @staticmethod
    def configuration_required_message() -> str:
        return (
            "Please create or load a configuration in the Configuration Editor "
            "before working with scheduler configuration."
        )

    # Report whether the agent can currently access a configuration.
    def get_active_configuration_status(self) -> dict[str, Any]:
        if not self.has_active_configuration:
            return self._result(False, self.configuration_required_message())
        return self._result(True, "A scheduler configuration is active.")

    # Format a configuration collection for the assistant.
    def _list_items(self, items: list[Any], *, label: str) -> dict[str, Any]:
        if not items:
            return self._result(True, f"No {label} found.", items=[])
        return self._result(
            True,
            f"Found {len(items)} {label}.",
            items=[item.model_dump(mode="json") for item in items],
        )

    # Add a room using the assistant's configuration defaults.
    def add_room(
        self,
        *,
        name: str,
        capacity: int = 1,
        features: list[str] | None = None,
    ) -> dict[str, Any]:
        if any(room.name == name for room in self.config.config.rooms):
            return self._result(False, f"Room {name} already exists.")
        try:
            room = RoomConfig(
                name=name,
                capacity=capacity,
                features=features or [],
                times=None,
            )
        except (ValidationError, TypeError, ValueError) as error:
            return self._result(False, f"Could not add room {name}: {error}")
        self.config.config.rooms.append(room)
        return self._result(True, f"Room {name} added successfully.")

    # Add a lab using the assistant's configuration defaults.
    def add_lab(
        self,
        *,
        name: str,
        capacity: int = 1,
        features: list[str] | None = None,
    ) -> dict[str, Any]:
        if any(lab.name == name for lab in self.config.config.labs):
            return self._result(False, f"Lab {name} already exists.")
        try:
            lab = LabConfig(
                name=name,
                capacity=capacity,
                features=features or [],
                times=None,
            )
        except (ValidationError, TypeError, ValueError) as error:
            return self._result(False, f"Could not add lab {name}: {error}")
        self.config.config.labs.append(lab)
        return self._result(True, f"Lab {name} added successfully.")

    # Add a faculty member with empty availability and preferences.
    def add_faculty(
        self,
        *,
        name: str,
        maximum_credits: int = 12,
        maximum_days: int = 5,
        minimum_credits: int = 0,
        unique_course_limit: int = 3,
    ) -> dict[str, Any]:
        if any(faculty.name == name for faculty in self.config.config.faculty):
            return self._result(False, f"Faculty member {name} already exists.")
        try:
            member = FacultyConfig(
                name=name,
                maximum_credits=maximum_credits,
                maximum_days=maximum_days,
                minimum_credits=minimum_credits,
                unique_course_limit=unique_course_limit,
                times={},
                course_preferences={},
                room_preferences={},
                lab_preferences={},
                mandatory_days=[],
            )
        except (ValidationError, TypeError, ValueError) as error:
            return self._result(False, f"Could not add faculty member {name}: {error}")
        self.config.config.faculty.append(member)
        return self._result(True, f"Faculty member {name} added successfully.")

    # Add a course section with the supplied scheduler constraints.
    def add_course(
        self,
        *,
        course_id: str,
        section_id: str | None = None,
        credits: int = 3,
        capacity: int = 1,
        room: list[str] | None = None,
        lab: list[str] | None = None,
        conflicts: list[str] | None = None,
        faculty: list[str] | None = None,
        modality: str = "in_person",
        required_room_features: list[str] | None = None,
        required_lab_features: list[str] | None = None,
        reserve_room_during_lab: bool = False,
    ) -> dict[str, Any]:
        if any(
            course.course_id == course_id and course.section_id == section_id
            for course in self.config.config.courses
        ):
            return self._result(
                False,
                f"Course {course_id} section {section_id or 'default'} already exists.",
            )

        try:
            course = CourseConfig(
                course_id=course_id,
                section_id=section_id,
                credits=credits,
                capacity=capacity,
                room=room or [],
                lab=lab or [],
                conflicts=conflicts or [],
                faculty=faculty or [],
                modality=modality,
                required_room_features=required_room_features or [],
                required_lab_features=required_lab_features or [],
                reserve_room_during_lab=reserve_room_during_lab,
            )
        except (ValidationError, TypeError, ValueError) as error:
            return self._result(False, f"Could not add course {course_id}: {error}")
        self.config.config.courses.append(course)
        return self._result(True, f"Course {course_id} added successfully.")

    # Return all configured rooms in JSON form.
    def get_rooms(self) -> str:
        return self._list_items(self.config.config.rooms, label="rooms")

    # Return all configured labs in JSON form.
    def get_labs(self) -> str:
        return self._list_items(self.config.config.labs, label="labs")

    # Return all configured faculty members in JSON form.
    def get_faculty(self) -> str:
        return self._list_items(self.config.config.faculty, label="faculty members")

    # Return all configured courses in JSON form.
    def get_courses(self) -> str:
        return self._list_items(self.config.config.courses, label="courses")

    # Summarize the counts of configured scheduling resources.
    def get_config_summary(self) -> dict[str, Any]:
        summary = (
            f"Rooms: {len(self.config.config.rooms)}\n"
            f"Labs: {len(self.config.config.labs)}\n"
            f"Courses: {len(self.config.config.courses)}\n"
            f"Faculty: {len(self.config.config.faculty)}"
        )
        return self._result(True, summary)

    # Serialize the full configuration or one supported configuration area.
    def inspect_configuration(self, area: str = "all") -> dict[str, Any]:
        payload = self.config.model_dump(mode="json")
        areas = {
            "rooms": payload["config"]["rooms"],
            "labs": payload["config"]["labs"],
            "courses": payload["config"]["courses"],
            "faculty": payload["config"]["faculty"],
            "class_patterns": payload["time_slot_config"]["classes"],
            "meetings": [
                {
                    "class_pattern_index": pattern_index,
                    "class_pattern_credits": pattern["credits"],
                    **meeting,
                }
                for pattern_index, pattern in enumerate(
                    payload["time_slot_config"]["classes"]
                )
                for meeting in pattern["meetings"]
            ],
            "time_blocks": payload["time_slot_config"]["times"],
            "global_settings": {
                "limit": payload["limit"],
                "optimizer_flags": payload["optimizer_flags"],
                "max_time_gap": payload["time_slot_config"]["max_time_gap"],
                "min_time_overlap": payload["time_slot_config"]["min_time_overlap"],
            },
        }
        if area == "all":
            result = payload
        elif area in areas:
            result = areas[area]
        else:
            return self._result(False, f"Unknown configuration area '{area}'.")
        return self._result(
            True,
            f"Inspected configuration area '{area}'.",
            data=result,
        )

    # Create a typed item or a weekday's time-block set.
    def create_configuration_item(
        self,
        *,
        area: str,
        item: dict[str, Any],
        item_key: str | None = None,
    ) -> dict[str, Any]:
        try:
            if area in {
                "rooms", "labs", "courses", "faculty", "class_patterns"
            }:
                collection = self._item_collection(area)
                parsed = self._parse_item(area, item)
                key = self._item_identity(area, parsed)
                if area != "class_patterns" and any(
                    self._item_identity(area, current) == key for current in collection
                ):
                    return self._result(
                        False,
                        f"A {area.rstrip('s')} item with key '{key}' already exists.",
                    )
                collection.append(parsed)
            elif area == "meetings":
                pattern = self._find_pattern(item_key)
                parsed = Meeting.model_validate(item)
                if any(existing.day == parsed.day for existing in pattern.meetings):
                    return self._result(
                        False,
                        f"Pattern {item_key} already has a meeting on {parsed.day}.",
                    )
                pattern.meetings.append(parsed)
            elif area == "time_blocks":
                if not item_key:
                    return self._result(
                        False, "A weekday item_key is required for time_blocks."
                    )
                day = item_key.upper()
                if day not in {"MON", "TUE", "WED", "THU", "FRI"}:
                    return self._result(False, f"Unknown weekday '{item_key}'.")
                if day in self.config.time_slot_config.times:
                    return self._result(False, f"Time blocks for {day} already exist.")
                blocks = item.get("blocks")
                if not isinstance(blocks, list):
                    return self._result(
                        False, "time_blocks item must include a 'blocks' list."
                    )
                self.config.time_slot_config.times[day] = [
                    TimeBlock.model_validate(block) for block in blocks
                ]
            else:
                return self._result(
                    False, f"Items cannot be created in configuration area '{area}'."
                )
        except (ValidationError, TypeError, ValueError) as error:
            return self._result(False, f"Could not create {area} item: {error}")
        created_key = item_key or (key if "key" in locals() else "")
        return self._result(True, f"Created {area} item '{created_key}'.")

    # Merge changed fields into an existing configuration item.
    def update_configuration_item(
        self,
        *,
        area: str,
        item_key: str | None,
        item: dict[str, Any],
    ) -> dict[str, Any]:
        if not item_key:
            return self._result(
                False, "An item_key is required to update a configuration item."
            )
        try:
            if area == "time_blocks":
                day = item_key.upper()
                if day not in {"MON", "TUE", "WED", "THU", "FRI"}:
                    return self._result(False, f"Unknown weekday '{item_key}'.")
                if day not in self.config.time_slot_config.times:
                    return self._result(False, f"No time blocks found for {day}.")
                blocks = item.get("blocks")
                if not isinstance(blocks, list):
                    return self._result(
                        False, "time_blocks item must include a 'blocks' list."
                    )
                self.config.time_slot_config.times[day] = [
                    TimeBlock.model_validate(block) for block in blocks
                ]
            elif area == "meetings":
                pattern_key, day = self._meeting_key(item_key)
                pattern = self._find_pattern(pattern_key)
                index = next(
                    (i for i, meeting in enumerate(pattern.meetings) if meeting.day == day),
                    None,
                )
                if index is None:
                    return self._result(
                        False, f"No meeting found for pattern {pattern_key} on {day}."
                    )
                values = pattern.meetings[index].model_dump(mode="json")
                values.update(item)
                updated_meeting = Meeting.model_validate(values)
                if any(
                    other_index != index and meeting.day == updated_meeting.day
                    for other_index, meeting in enumerate(pattern.meetings)
                ):
                    return self._result(
                        False,
                        f"Pattern {pattern_key} already has a meeting on "
                        f"{updated_meeting.day}.",
                    )
                pattern.meetings[index] = updated_meeting
            elif area in {"rooms", "labs", "courses", "faculty", "class_patterns"}:
                collection = self._item_collection(area)
                index = self._find_item_index(area, collection, item_key)
                if isinstance(index, str):
                    return self._result(False, index)
                existing = collection[index]
                values = existing.model_dump(mode="json")
                values.update(item)
                collection[index] = self._parse_item(area, values)
                if area != "class_patterns":
                    new_key = self._item_identity(area, collection[index])
                    if any(
                        position != index
                        and self._item_identity(area, current) == new_key
                        for position, current in enumerate(collection)
                    ):
                        collection[index] = existing
                        return self._result(
                            False,
                            f"A {area.rstrip('s')} item with key '{new_key}' already exists.",
                        )
            else:
                return self._result(
                    False, f"Items cannot be updated in configuration area '{area}'."
                )
        except (ValidationError, TypeError, ValueError) as error:
            return self._result(
                False, f"Could not update {area} item '{item_key}': {error}"
            )
        return self._result(True, f"Updated {area} item '{item_key}'.")

    # Delete a keyed configuration item or a weekday's time blocks.
    def delete_configuration_item(self, *, area: str, item_key: str) -> dict[str, Any]:
        if area == "time_blocks":
            day = item_key.upper()
            if day not in {"MON", "TUE", "WED", "THU", "FRI"}:
                return self._result(False, f"Unknown weekday '{item_key}'.")
            if day not in self.config.time_slot_config.times:
                return self._result(False, f"No time blocks found for {day}.")
            del self.config.time_slot_config.times[day]
        elif area == "meetings":
            try:
                pattern_key, day = self._meeting_key(item_key)
                pattern = self._find_pattern(pattern_key)
            except ValueError as error:
                return self._result(False, str(error))
            index = next(
                (i for i, meeting in enumerate(pattern.meetings) if meeting.day == day),
                None,
            )
            if index is None:
                return self._result(
                    False, f"No meeting found for pattern {pattern_key} on {day}."
                )
            if len(pattern.meetings) == 1:
                return self._result(
                    False,
                    "Cannot delete the only meeting in a class pattern; "
                    "delete the class pattern instead.",
                )
            del pattern.meetings[index]
        elif area in {"rooms", "labs", "courses", "faculty", "class_patterns"}:
            collection = self._item_collection(area)
            index = self._find_item_index(area, collection, item_key)
            if isinstance(index, str):
                return self._result(False, index)
            del collection[index]
        else:
            return self._result(
                False, f"Items cannot be deleted from configuration area '{area}'."
            )
        return self._result(True, f"Deleted {area} item '{item_key}'.")

    def _find_pattern(self, pattern_key: str | None) -> ClassPattern:
        if not pattern_key:
            raise ValueError("A class-pattern index is required.")
        try:
            index = int(pattern_key)
        except ValueError as error:
            raise ValueError("Class-pattern key must be its zero-based index.") from error
        if not 0 <= index < len(self.config.time_slot_config.classes):
            raise ValueError(f"No class pattern found at index {index}.")
        return self.config.time_slot_config.classes[index]

    @staticmethod
    def _meeting_key(item_key: str) -> tuple[str, str]:
        if "::" not in item_key:
            raise ValueError("Meeting item_key must be CLASS_PATTERN_INDEX::DAY.")
        pattern_key, day = item_key.rsplit("::", 1)
        return pattern_key, day.upper()

    # Apply provided global and time-slot settings.
    def update_configuration_settings(
        self,
        *,
        limit: int | None = None,
        optimizer_flags: list[str] | None = None,
        max_time_gap: int | None = None,
        min_time_overlap: int | None = None,
    ) -> dict[str, Any]:
        if limit is not None and limit <= 0:
            return self._result(False, "limit must be a positive integer.")
        if max_time_gap is not None and max_time_gap < 0:
            return self._result(False, "max_time_gap cannot be negative.")
        if min_time_overlap is not None and min_time_overlap < 0:
            return self._result(False, "min_time_overlap cannot be negative.")
        changed: list[str] = []
        if limit is not None:
            object.__setattr__(self.config, "limit", limit)
            changed.append("limit")
        if optimizer_flags is not None:
            object.__setattr__(self.config, "optimizer_flags", optimizer_flags)
            changed.append("optimizer_flags")
        if max_time_gap is not None:
            object.__setattr__(
                self.config.time_slot_config, "max_time_gap", max_time_gap
            )
            changed.append("max_time_gap")
        if min_time_overlap is not None:
            object.__setattr__(
                self.config.time_slot_config, "min_time_overlap", min_time_overlap
            )
            changed.append("min_time_overlap")
        if not changed:
            return self._result(False, "No settings were provided to update.")
        return self._result(
            True, f"Updated global settings: {', '.join(changed)}."
        )

    # Format validation problems for the active configuration.
    def validate_current_config(self) -> dict[str, Any]:
        problems = validate_config(self.config)
        if not problems:
            return self._result(True, "The current configuration is valid.")
        lines = [f"Validation issues ({len(problems)}):"]
        for problem in problems:
            item = problem.item or "overall configuration"
            lines.append(f"- {problem.area}: {item} -> {problem.message}")
        return self._result(
            False,
            "\n".join(lines),
            errors=[
                {"area": problem.area, "item": problem.item, "message": problem.message}
                for problem in problems
            ],
        )

    # Validate and save the active configuration through the app callback.
    def save_current_config(self, config_name: str) -> dict[str, Any]:
        problems = validate_config(self.config)
        if problems:
            return self._result(
                False,
                "Configuration was not saved because validation failed.",
                errors=[
                    {"area": problem.area, "item": problem.item, "message": problem.message}
                    for problem in problems
                ],
            )
        try:
            if self._configuration_exists(config_name):
                if self._confirm_action is None or not self._confirm_action(
                    f"Replace the saved configuration '{config_name}.json'?"
                ):
                    return self._result(
                        False, "Save cancelled; the existing file was not changed."
                    )
            if self._save_configuration is not None:
                self._save_configuration(config_name)
            else:
                ConfigService().save(self.config, config_name)
        except (ConfigValidationError, OSError, ValueError) as error:
            if isinstance(error, ConfigValidationError):
                return self._result(
                    False,
                    "Configuration was not saved because validation failed.",
                    errors=[
                        {
                            "area": problem.area,
                            "item": problem.item,
                            "message": problem.message,
                        }
                        for problem in error.problems
                    ],
                )
            return self._result(
                False, f"Could not save configuration '{config_name}': {error}"
            )
        return self._result(
            True,
            f"Configuration saved as '{config_name}.json'.",
            action="saved",
        )

    # Generate from the active config and direct results to the viewer.
    def generate_schedules(self) -> dict[str, Any]:
        problems = validate_config(self.config)
        if problems:
            return self._result(
                False,
                "Cannot generate schedules until the configuration is valid.",
                errors=[
                    {"area": problem.area, "item": problem.item, "message": problem.message}
                    for problem in problems
                ],
            )
        state, error = self._schedule_generator.generate_active_configuration(
            self.config
        )
        if error:
            return self._result(False, f"Schedule generation failed: {error}")

        if state is None or state.generated == 0:
            return self._result(False, "No valid schedules could be generated.")
        return self._result(
            True,
            f"Schedule generation complete. Generated {state.generated} schedule(s), "
            f"{state.valid} valid. View generated schedules in the Schedule Viewer tab.",
            action="generated",
            generated=state.generated,
            valid=state.valid,
        )

    # Resolve a supported area to its mutable configuration collection.
    def _item_collection(self, area: str) -> list[Any]:
        if area in {"rooms", "labs", "courses", "faculty"}:
            return getattr(self.config.config, area)
        if area == "class_patterns":
            return self.config.time_slot_config.classes
        raise ValueError(f"Unknown configuration area '{area}'.")

    # Validate an item dictionary with its scheduler configuration type.
    @staticmethod
    def _parse_item(area: str, item: dict[str, Any]) -> Any:
        model = {
            "rooms": RoomConfig,
            "labs": LabConfig,
            "courses": CourseConfig,
            "faculty": FacultyConfig,
            "class_patterns": ClassPattern,
        }.get(area)
        if model is None:
            raise ValueError(f"Unknown configuration area '{area}'.")
        return model.model_validate(item)

    # Return the stable key used to find or de-duplicate an item.
    @staticmethod
    def _item_identity(area: str, item: Any) -> str:
        if area == "courses":
            return f"{item.course_id}::{item.section_id or 'default'}"
        if area == "class_patterns":
            return str(item.credits)
        return item.name

    # Find an item by key or return a message explaining why it is unresolved.
    def _find_item_index(
        self, area: str, collection: list[Any], item_key: str
    ) -> int | str:
        if area == "class_patterns":
            try:
                index = int(item_key)
            except ValueError:
                return "Class-pattern item_key must be its zero-based index."
            if not 0 <= index < len(collection):
                return f"No class pattern found at index {index}."
            return index
        if area == "courses":
            if "::" in item_key:
                course_id, section = item_key.split("::", 1)
                matches = [
                    index
                    for index, course in enumerate(collection)
                    if course.course_id == course_id
                    and (course.section_id or "default") == section
                ]
            else:
                matches = [
                    index
                    for index, course in enumerate(collection)
                    if course.course_id == item_key
                ]
            if len(matches) > 1:
                keys = [
                    self._item_identity(area, collection[index]) for index in matches
                ]
                return f"'{item_key}' is ambiguous. Use one of: {', '.join(keys)}."
            if not matches:
                return f"No course found with key '{item_key}'."
            return matches[0]
        for index, item in enumerate(collection):
            if self._item_identity(area, item) == item_key:
                return index
        return f"No {area.rstrip('s')} item found with key '{item_key}'."


class AddRoomArgs(BaseModel):
    name: str = Field(description="Room name, such as 'Room 101'")
    capacity: int = Field(default=1, description="Room seating capacity")
    features: list[str] | None = Field(
        default=None,
        description="Optional room features, such as whiteboard or projector",
    )


class AddLabArgs(BaseModel):
    name: str = Field(description="Lab name, such as 'Lab 1'")
    capacity: int = Field(default=1, description="Lab capacity")
    features: list[str] | None = Field(
        default=None, description="Optional lab features"
    )


class AddFacultyArgs(BaseModel):
    name: str = Field(description="Faculty member name")
    maximum_credits: int = Field(
        default=12, description="Maximum credits the faculty member can teach"
    )
    maximum_days: int = Field(default=5, description="Maximum number of teaching days")
    minimum_credits: int = Field(default=0, description="Minimum teaching credits")
    unique_course_limit: int = Field(default=3, description="Maximum unique courses")


class AddCourseArgs(BaseModel):
    course_id: str = Field(description="Course ID, such as 'CS 101'")
    section_id: str | None = Field(default=None, description="Optional section ID")
    credits: int = Field(default=3, description="Course credit count")
    capacity: int = Field(default=1, description="Seat capacity")
    room: list[str] | None = Field(
        default=None, description="List of room names the course can use"
    )
    lab: list[str] | None = Field(
        default=None, description="List of lab names the course can use"
    )
    conflicts: list[str] | None = Field(
        default=None, description="List of conflicting course IDs"
    )
    faculty: list[str] | None = Field(
        default=None, description="List of faculty names assigned to the course"
    )
    modality: str = Field(default="in_person", description="Course delivery modality")
    required_room_features: list[str] | None = Field(
        default=None, description="Required room features"
    )
    required_lab_features: list[str] | None = Field(
        default=None, description="Required lab features"
    )
    reserve_room_during_lab: bool = Field(
        default=False, description="Whether the room should stay reserved during labs"
    )


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
        "rooms", "labs", "courses", "faculty", "class_patterns", "meetings",
        "time_blocks"
    ] = Field(description="Configuration area containing the item")
    item_key: str | None = Field(
        default=None,
        description=(
            "Existing item key for update/delete; weekday for time_blocks; "
            "course keys can use COURSE_ID::SECTION_ID; meetings use "
            "CLASS_PATTERN_INDEX::DAY; create meetings with the class-pattern index"
        ),
    )
    item: dict[str, Any] = Field(
        description="Item fields as a JSON object; time_blocks uses {'blocks': [...]}."
    )


class DeleteConfigurationItemArgs(BaseModel):
    area: Literal[
        "rooms", "labs", "courses", "faculty", "class_patterns", "meetings",
        "time_blocks"
    ] = Field(description="Configuration area containing the item")
    item_key: str = Field(
        description=(
            "Item name, course ID or COURSE_ID::SECTION_ID, zero-based pattern "
            "index, or weekday for time_blocks"
            "; meetings use CLASS_PATTERN_INDEX::DAY"
        )
    )


class ConfigurationSettingsArgs(BaseModel):
    limit: int | None = Field(
        default=None, description="Positive maximum schedules to generate"
    )
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


# Register assistant tools with configuration and change-validation guards.
def get_tool_list(
    state: SchedulerAgentState,
    apply_change: Callable[[Callable[[], Any]], tuple[bool, list[Any]]] | None = None,
    save_configuration: Callable[[str], None] | None = None,
    on_tool_result: Callable[[dict[str, Any]], None] | None = None,
) -> list[StructuredTool]:
    if save_configuration is not None:
        state._save_configuration = save_configuration

    # Apply edits through the configuration controller when available.
    def report(result: dict[str, Any]) -> dict[str, Any]:
        if on_tool_result is not None:
            on_tool_result(result)
        return result

    def mutation_tool(
        operation: Callable[..., dict[str, Any]],
        *,
        needs_confirmation: bool = False,
    ) -> Callable[..., dict[str, Any]]:
        def guarded_operation(**arguments: Any) -> dict[str, Any]:
            if not state.has_active_configuration:
                return report(state._result(False, state.configuration_required_message()))
            if needs_confirmation:
                key = arguments["item_key"]
                if state._confirm_action is None or not state._confirm_action(
                    f"Delete {arguments['area']} item '{key}'?"
                ):
                    return report(
                        state._result(False, "Deletion cancelled; no item was changed.")
                    )
            if apply_change is None:
                return report(operation(**arguments))
            result: list[dict[str, Any]] = []
            accepted, problems = apply_change(
                lambda: result.append(operation(**arguments))
            )
            if not accepted:
                details = "\n".join(
                    f"- {problem.area}: {problem.item or 'overall'}: {problem.message}"
                    for problem in problems
                )
                return report(
                    state._result(
                        False,
                        f"Change rejected by scheduler validation:\n{details}",
                        errors=[
                            {
                                "area": problem.area,
                                "item": problem.item,
                                "message": problem.message,
                            }
                            for problem in problems
                        ],
                    )
                )
            outcome = result[0]
            if not outcome["success"]:
                return report(outcome)
            if problems:
                details = "\n".join(
                    f"- {problem.area}: {problem.item or 'overall'}: "
                    f"{problem.message}"
                    for problem in problems
                )
                outcome = {
                    **outcome,
                    "message": outcome["message"]
                    + f"\nThe draft still has validation issues:\n{details}",
                    "warnings": [
                        {
                            "area": problem.area,
                            "item": problem.item,
                            "message": problem.message,
                        }
                        for problem in problems
                    ],
                }
            return report(outcome)

        return guarded_operation

    # Block configuration operations when no active config is attached.
    def configuration_tool(
        operation: Callable[..., dict[str, Any]]
    ) -> Callable[..., dict[str, Any]]:
        def guarded_operation(**arguments: Any) -> dict[str, Any]:
            if not state.has_active_configuration:
                return report(
                    state._result(False, state.configuration_required_message())
                )
            outcome = operation(**arguments)
            if outcome.get("action") == "saved" and on_tool_result is not None:
                on_tool_result(outcome)
            else:
                report(outcome)
            return outcome

        return guarded_operation

    def validation_error(error: list[Any]) -> str:
        result = report(
            state._result(False, f"Invalid tool arguments: {error}")
        )
        return json.dumps(result, default=str)

    tools = [
        StructuredTool.from_function(
            name="add_room",
            func=mutation_tool(state.add_room),
            description="Add a room to the scheduler configuration.",
            args_schema=AddRoomArgs,
        ),
        StructuredTool.from_function(
            name="add_lab",
            func=mutation_tool(state.add_lab),
            description="Add a lab to the scheduler configuration.",
            args_schema=AddLabArgs,
        ),
        StructuredTool.from_function(
            name="add_faculty",
            func=mutation_tool(state.add_faculty),
            description="Add a faculty member to the scheduler.",
            args_schema=AddFacultyArgs,
        ),
        StructuredTool.from_function(
            name="add_course",
            func=mutation_tool(state.add_course),
            description="Add a course to the scheduler configuration.",
            args_schema=AddCourseArgs,
        ),
        StructuredTool.from_function(
            name="get_rooms",
            func=configuration_tool(state.get_rooms),
            description="List all rooms in the scheduler configuration.",
            args_schema={},
        ),
        StructuredTool.from_function(
            name="get_labs",
            func=configuration_tool(state.get_labs),
            description="List all labs in the scheduler configuration.",
            args_schema={},
        ),
        StructuredTool.from_function(
            name="get_faculty",
            func=configuration_tool(state.get_faculty),
            description="List all faculty members in the scheduler configuration.",
            args_schema={},
        ),
        StructuredTool.from_function(
            name="get_courses",
            func=configuration_tool(state.get_courses),
            description="List all courses in the scheduler configuration.",
            args_schema={},
        ),
        StructuredTool.from_function(
            name="get_config_summary",
            func=configuration_tool(state.get_config_summary),
            description="Summarize counts for rooms, labs, courses, and faculty.",
            args_schema={},
        ),
        StructuredTool.from_function(
            name="validate_current_config",
            func=configuration_tool(state.validate_current_config),
            description="Validate the current configuration against the scheduler rules.",
            args_schema={},
        ),
        StructuredTool.from_function(
            name="inspect_configuration",
            func=configuration_tool(state.inspect_configuration),
            description="Inspect the full configuration or one configuration area.",
            args_schema=InspectConfigurationArgs,
        ),
        StructuredTool.from_function(
            name="create_configuration_item",
            func=mutation_tool(state.create_configuration_item),
            description="Create a room, lab, course, faculty member, class pattern, meeting, or weekday time-block set.",
            args_schema=ConfigurationItemArgs,
        ),
        StructuredTool.from_function(
            name="update_configuration_item",
            func=mutation_tool(state.update_configuration_item),
            description="Update an existing configuration item using its key and changed fields.",
            args_schema=ConfigurationItemArgs,
        ),
        StructuredTool.from_function(
            name="delete_configuration_item",
            func=mutation_tool(state.delete_configuration_item, needs_confirmation=True),
            description="Delete an item from a supported configuration area.",
            args_schema=DeleteConfigurationItemArgs,
        ),
        StructuredTool.from_function(
            name="update_configuration_settings",
            func=mutation_tool(state.update_configuration_settings),
            description="Update global schedule-generation settings.",
            args_schema=ConfigurationSettingsArgs,
        ),
        StructuredTool.from_function(
            name="save_configuration",
            func=configuration_tool(state.save_current_config),
            description="Validate and save the active configuration through the application save workflow as JSON.",
            args_schema=SaveConfigurationArgs,
        ),
        StructuredTool.from_function(
            name="generate_schedules",
            func=configuration_tool(state.generate_schedules),
            description="Generate schedules from the active configuration after validating it.",
            args_schema={},
        ),
        StructuredTool.from_function(
            name="get_active_configuration_status",
            func=state.get_active_configuration_status,
            description="Check whether a configuration is active before working with it.",
            args_schema={},
        ),
    ]
    return [
        tool.model_copy(update={"handle_validation_error": validation_error})
        for tool in tools
    ]


# Build the scheduler agent, model, tools, and behavior instructions.
def build_scheduler_agent(
    *,
    config: CombinedConfig | None = None,
    model: Any | None = None,
    apply_change: Callable[[Callable[[], Any]], tuple[bool, list[Any]]] | None = None,
    save_configuration: Callable[[str], None] | None = None,
    confirm_action: Callable[[str], bool] | None = None,
    on_tool_result: Callable[[dict[str, Any]], None] | None = None,
    configuration_exists: Callable[[str], bool] | None = None,
) -> Any:
    state = SchedulerAgentState(
        config=config,
        confirm_action=confirm_action,
        configuration_exists=configuration_exists,
    )
    if model is None:
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY is not set. Add it to the .env file in the project root."
            )
        model = ChatOpenAI(
            model="gpt-6-luna",
            use_responses_api=True,
            reasoning={"effort": "medium"},
            timeout=60,
            max_retries=2,
            api_key=api_key,
        )

    configuration_context = (
        "An active configuration is available."
        if config is not None
        else (
            "There is no active configuration. Continue helping with general "
            "scheduler questions, but if the user asks to inspect, create, "
            "change, validate, save, or generate from a configuration, tell "
            "them to create or load one in the Configuration Editor first. "
            "Do not imply you can work with a configuration until one is active."
        )
    )
    return create_agent(
        model=model,
        tools=get_tool_list(
            state,
            apply_change=apply_change,
            save_configuration=save_configuration,
            on_tool_result=on_tool_result,
        ),
        system_prompt=(
            "You are the assistant for the MrLand course scheduler. Use the "
            "provided tools to inspect or edit the active configuration. Never "
            "claim an edit succeeded unless its tool reports success. Ask a "
            "clarifying question when required values are missing; do not invent "
            "availability, assignments, or scheduling constraints. Inspect the "
            "relevant configuration area before editing it. Validate edits and "
            "report validation problems. Save only when the user explicitly asks "
            "you to save, and only claim success if the save tool succeeds. "
            "Generate schedules only from a valid active configuration. "
            "Ask for explicit user confirmation before deleting an item or "
            "replacing a saved configuration; the application will show a "
            "confirmation dialog and cancel the operation if it is declined. "
            "Treat each user request as one transaction: if any requested "
            "operation fails, do not claim partial success. "
            "When schedules are generated, do not reproduce schedule rows; "
            "report the count and direct the user to the Schedule Viewer tab. "
            + configuration_context
        ),
    )


# Invoke the agent with the query and prior conversation messages.
def invoke_scheduler_agent(
    *,
    config: CombinedConfig,
    query: str,
    history: list[Any] | None = None,
    apply_change: Callable[[Callable[[], Any]], tuple[bool, list[Any]]] | None = None,
    save_configuration: Callable[[str], None] | None = None,
    confirm_action: Callable[[str], bool] | None = None,
    on_tool_result: Callable[[dict[str, Any]], None] | None = None,
    configuration_exists: Callable[[str], bool] | None = None,
) -> dict[str, Any]:
    agent = build_scheduler_agent(
        config=config,
        apply_change=apply_change,
        save_configuration=save_configuration,
        confirm_action=confirm_action,
        on_tool_result=on_tool_result,
        configuration_exists=configuration_exists,
    )
    result = agent.invoke({"messages": [*(history or []), HumanMessage(content=query)]})
    return result


def run_cli() -> None:
    # Run an interactive terminal conversation with the scheduler assistant.
    config = empty_scheduler_config()
    history: list[Any] = []
    while True:
        try:
            query = input("Enter a scheduler query: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not query or query.casefold() in {"exit", "quit"}:
            break
        result = invoke_scheduler_agent(
            config=config,
            query=query,
            history=history,
        )
        history = result["messages"]
        response = next(
            (
                message.text
                for message in reversed(result["messages"])
                if getattr(message, "type", None) == "ai"
                and getattr(message, "text", None)
            ),
            "",
        )
        if response:
            print(response)


if __name__ == "__main__":
    run_cli()
