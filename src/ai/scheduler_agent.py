"""LangChain wrapper for the course scheduler configuration.

This module intentionally keeps the scheduler logic in the domain model and
validation layer, while exposing a small set of safe operations as tools that the
LLM can call.
"""

from __future__ import annotations

import os
from collections.abc import Callable
from typing import Any

from pydantic import BaseModel, Field
from scheduler.config import (
    CombinedConfig,
    CourseConfig,
    FacultyConfig,
    LabConfig,
    RoomConfig,
)

from src.models.configuration_model import create_draft_config, validate_config

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


def empty_scheduler_config() -> CombinedConfig:
    """Return a valid draft config object that can be mutated safely."""
    return create_draft_config()


class SchedulerAgentState:
    """Thin bridge between the AI and the scheduler configuration object."""

    def __init__(self, config: CombinedConfig | None = None):
        self.config = config or empty_scheduler_config()

    def _list_items(self, items: list[Any], *, label: str) -> str:
        if not items:
            return f"No {label} found."
        return "\n".join(item.model_dump_json() for item in items)

    def add_room(
        self,
        *,
        name: str,
        capacity: int = 0,
        features: list[str] | None = None,
    ) -> str:
        if any(room.name == name for room in self.config.config.rooms):
            return f"Room {name} already exists."
        self.config.config.rooms.append(
            RoomConfig(
                name=name,
                capacity=capacity,
                features=features or [],
                times=None,
            )
        )
        return f"Room {name} added successfully."

    def add_lab(
        self,
        *,
        name: str,
        capacity: int = 0,
        features: list[str] | None = None,
    ) -> str:
        if any(lab.name == name for lab in self.config.config.labs):
            return f"Lab {name} already exists."
        self.config.config.labs.append(
            LabConfig(
                name=name,
                capacity=capacity,
                features=features or [],
                times=None,
            )
        )
        return f"Lab {name} added successfully."

    def add_faculty(
        self,
        *,
        name: str,
        maximum_credits: int = 12,
        maximum_days: int = 5,
        minimum_credits: int = 0,
        unique_course_limit: int = 3,
    ) -> str:
        if any(faculty.name == name for faculty in self.config.config.faculty):
            return f"Faculty member {name} already exists."
        self.config.config.faculty.append(
            FacultyConfig(
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
        )
        return f"Faculty member {name} added successfully."

    def add_course(
        self,
        *,
        course_id: str,
        section_id: str | None = None,
        credits: int = 3,
        capacity: int = 0,
        room: list[str] | None = None,
        lab: list[str] | None = None,
        conflicts: list[str] | None = None,
        faculty: list[str] | None = None,
        modality: str = "in_person",
        required_room_features: list[str] | None = None,
        required_lab_features: list[str] | None = None,
        reserve_room_during_lab: bool = False,
    ) -> str:
        if any(
            course.course_id == course_id and course.section_id == section_id
            for course in self.config.config.courses
        ):
            return (
                f"Course {course_id} section {section_id or 'default'} already exists."
            )

        self.config.config.courses.append(
            CourseConfig(
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
        )
        return f"Course {course_id} added successfully."

    def get_rooms(self) -> str:
        return self._list_items(self.config.config.rooms, label="rooms")

    def get_labs(self) -> str:
        return self._list_items(self.config.config.labs, label="labs")

    def get_faculty(self) -> str:
        return self._list_items(self.config.config.faculty, label="faculty members")

    def get_courses(self) -> str:
        return self._list_items(self.config.config.courses, label="courses")

    def get_config_summary(self) -> str:
        return (
            f"Rooms: {len(self.config.config.rooms)}\n"
            f"Labs: {len(self.config.config.labs)}\n"
            f"Courses: {len(self.config.config.courses)}\n"
            f"Faculty: {len(self.config.config.faculty)}"
        )

    def validate_current_config(self) -> str:
        problems = validate_config(self.config)
        if not problems:
            return "The current configuration is valid."
        lines = [f"Validation issues ({len(problems)}):"]
        for problem in problems:
            item = problem.item or "overall configuration"
            lines.append(f"- {problem.area}: {item} -> {problem.message}")
        return "\n".join(lines)


class AddRoomArgs(BaseModel):
    name: str = Field(description="Room name, such as 'Room 101'")
    capacity: int = Field(default=0, description="Room seating capacity")
    features: list[str] | None = Field(
        default=None,
        description="Optional room features, such as whiteboard or projector",
    )


class AddLabArgs(BaseModel):
    name: str = Field(description="Lab name, such as 'Lab 1'")
    capacity: int = Field(default=0, description="Lab capacity")
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
    capacity: int = Field(default=0, description="Seat capacity")
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


def get_tool_list(
    state: SchedulerAgentState,
    apply_change: Callable[[Callable[[], str]], tuple[bool, list[Any]]] | None = None,
) -> list[StructuredTool]:
    def mutation_tool(operation: Callable[..., str]) -> Callable[..., str]:
        if apply_change is None:
            return operation

        def guarded_operation(**arguments: Any) -> str:
            result: list[str] = []
            accepted, problems = apply_change(
                lambda: result.append(operation(**arguments))
            )
            if not accepted:
                details = "\n".join(
                    f"- {problem.area}: {problem.item or 'overall'}: {problem.message}"
                    for problem in problems
                )
                return f"Change rejected by scheduler validation:\n{details}"
            message = result[0]
            if problems:
                message += (
                    "\nThe draft still has validation issues; see the editor "
                    "for details."
                )
            return message

        return guarded_operation

    return [
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
            func=state.get_rooms,
            description="List all rooms in the scheduler configuration.",
            args_schema={},
        ),
        StructuredTool.from_function(
            name="get_labs",
            func=state.get_labs,
            description="List all labs in the scheduler configuration.",
            args_schema={},
        ),
        StructuredTool.from_function(
            name="get_faculty",
            func=state.get_faculty,
            description="List all faculty members in the scheduler configuration.",
            args_schema={},
        ),
        StructuredTool.from_function(
            name="get_courses",
            func=state.get_courses,
            description="List all courses in the scheduler configuration.",
            args_schema={},
        ),
        StructuredTool.from_function(
            name="get_config_summary",
            func=state.get_config_summary,
            description="Summarize counts for rooms, labs, courses, and faculty.",
            args_schema={},
        ),
        StructuredTool.from_function(
            name="validate_current_config",
            func=state.validate_current_config,
            description="Validate the current configuration against the scheduler rules.",
            args_schema={},
        ),
    ]


def build_scheduler_agent(
    *,
    config: CombinedConfig | None = None,
    model: Any | None = None,
    api_key: str | None = None,
    apply_change: Callable[[Callable[[], str]], tuple[bool, list[Any]]] | None = None,
) -> Any:
    """Create a LangChain agent configured for the scheduler domain."""
    state = SchedulerAgentState(config=config)
    if model is None:
        resolved_api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not resolved_api_key:
            raise ValueError(
                "Set OPENAI_API_KEY or provide an API key in the AI assistant."
            )
        model = ChatOpenAI(
            model="gpt-6-luna",
            use_responses_api=True,
            reasoning={"effort": "medium"},
            timeout=60,
            max_retries=2,
            api_key=resolved_api_key,
        )
    return create_agent(
        model=model,
        tools=get_tool_list(state, apply_change=apply_change),
        system_prompt=(
            "You are the assistant for the MrLand course scheduler. Use the "
            "provided tools to inspect or edit the active configuration. Never "
            "claim an edit succeeded unless its tool reports success. Ask a "
            "clarifying question when required values are missing; do not invent "
            "availability, assignments, or scheduling constraints. The GUI "
            "validates edits and the user must save changes explicitly."
        ),
    )


def invoke_scheduler_agent(
    *,
    config: CombinedConfig,
    query: str,
    history: list[Any] | None = None,
    api_key: str | None = None,
    apply_change: Callable[[Callable[[], str]], tuple[bool, list[Any]]] | None = None,
) -> dict[str, Any]:
    agent = build_scheduler_agent(
        config=config,
        api_key=api_key,
        apply_change=apply_change,
    )
    result = agent.invoke({"messages": [*(history or []), HumanMessage(content=query)]})
    return result


def run_cli() -> None:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        import getpass

        api_key = getpass.getpass("Enter API key for OpenAI: ")
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
            api_key=api_key,
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
