"""Assemble the scheduler assistant's LangChain tools."""

from __future__ import annotations

from collections.abc import Callable

from scheduler.config import CombinedConfig

try:
    from langchain_core.tools import StructuredTool
except ImportError as exc:  # pragma: no cover - dependency resolution is handled by uv
    raise RuntimeError(
        "LangChain AI dependencies are not installed. Run `uv sync` after adding "
        "the AI packages to pyproject.toml."
    ) from exc

from src.ai.agent_tool_definitions import (
    configuration_tools,
    history_tools,
    informational_tools,
    mutation_tools,
)
from src.ai.agent_tool_guards import AgentToolGuards
from src.ai.agent_tool_types import ToolResult
from src.ai.scheduler_agent_state import SchedulerAgentState, empty_scheduler_config
from src.controllers.configuration_controller import ConfigurationController
from src.models.configuration_model import ValidationProblem


def get_tool_list(
    state: SchedulerAgentState,
    apply_change: Callable[[Callable[[], None]], tuple[bool, list[ValidationProblem]]]
    | None = None,
    save_configuration: Callable[[str], None] | None = None,
    on_tool_result: Callable[[ToolResult], None] | None = None,
    undo_configuration: Callable[[], CombinedConfig | None] | None = None,
    redo_configuration: Callable[[], CombinedConfig | None] | None = None,
) -> list[StructuredTool]:
    if save_configuration is not None:
        state._save_configuration = save_configuration
    if apply_change is None:
        apply_change = ConfigurationController(state.config).apply_change

    guards = AgentToolGuards(state, apply_change, on_tool_result)
    tools = [
        *configuration_tools(state, guards),
        *mutation_tools(state, guards),
        *history_tools(undo_configuration, redo_configuration, guards),
        *informational_tools(state, guards),
    ]
    return [
        tool.model_copy(update={"handle_validation_error": guards.validation_error})
        for tool in tools
    ]


__all__ = ["SchedulerAgentState", "empty_scheduler_config", "get_tool_list"]
