"""Build scheduler-agent tools grouped by the operation they expose."""

from __future__ import annotations

from langchain_core.tools import StructuredTool

from src.ai.agent_tool_guards import AgentToolGuards
from src.ai.agent_tool_schemas import (
    CombinationPasswordArgs,
    ConfigurationItemArgs,
    ConfigurationSettingsArgs,
    DeleteConfigurationItemArgs,
    InspectConfigurationArgs,
    SaveConfigurationArgs,
)
from src.ai.scheduler_agent_state import SchedulerAgentState


def configuration_tools(
    state: SchedulerAgentState, guards: AgentToolGuards
) -> list[StructuredTool]:
    return [
        StructuredTool.from_function(
            name="get_config_summary",
            func=guards.configuration(state.get_config_summary),
            description="Summarize counts for rooms, labs, courses, and faculty.",
            args_schema={},
        ),
        StructuredTool.from_function(
            name="validate_current_config",
            func=guards.configuration(state.validate_current_config),
            description="Validate the current configuration against the scheduler rules.",
            args_schema={},
        ),
        StructuredTool.from_function(
            name="inspect_configuration",
            func=guards.configuration(state.inspect_configuration),
            description="Inspect the full configuration or one configuration area.",
            args_schema=InspectConfigurationArgs,
        ),
        StructuredTool.from_function(
            name="save_configuration",
            func=guards.configuration(state.save_current_config),
            description="Validate and save the active configuration through the application save workflow as JSON.",
            args_schema=SaveConfigurationArgs,
        ),
        StructuredTool.from_function(
            name="generate_schedules",
            func=guards.configuration(state.generate_schedules),
            description="Generate schedules from the active configuration after validating it.",
            args_schema={},
        ),
    ]


def mutation_tools(state: SchedulerAgentState, guards: AgentToolGuards) -> list[StructuredTool]:
    return [
        StructuredTool.from_function(
            name="create_configuration_item",
            func=guards.mutation(state.create_configuration_item),
            description=(
                "Create one room, lab, course, faculty member, class pattern, "
                "meeting, or weekday time-block set. Supply the exact fields "
                "required by that scheduler model in item."
            ),
            args_schema=ConfigurationItemArgs,
        ),
        StructuredTool.from_function(
            name="update_configuration_item",
            func=guards.mutation(state.update_configuration_item),
            description="Update an existing configuration item using its key and changed fields.",
            args_schema=ConfigurationItemArgs,
        ),
        StructuredTool.from_function(
            name="delete_configuration_item",
            func=guards.mutation(state.delete_configuration_item, needs_confirmation=True),
            description="Delete an item from a supported configuration area.",
            args_schema=DeleteConfigurationItemArgs,
        ),
        StructuredTool.from_function(
            name="update_configuration_settings",
            func=guards.mutation(state.update_configuration_settings),
            description="Update global schedule-generation settings.",
            args_schema=ConfigurationSettingsArgs,
        ),
    ]


def history_tools(
    undo_configuration,
    redo_configuration,
    guards: AgentToolGuards,
) -> list[StructuredTool]:
    return [
        StructuredTool.from_function(
            name="undo_configuration_change",
            func=guards.history(undo_configuration, "undo"),
            description="Undo the most recent configuration change using the editor's undo history.",
            args_schema={},
        ),
        StructuredTool.from_function(
            name="redo_configuration_change",
            func=guards.history(redo_configuration, "redo"),
            description="Redo the most recently undone configuration change using the editor's redo history.",
            args_schema={},
        ),
    ]


def informational_tools(
    state: SchedulerAgentState, guards: AgentToolGuards
) -> list[StructuredTool]:
    return [
        StructuredTool.from_function(
            name="get_active_configuration_status",
            func=state.get_active_configuration_status,
            description="Check whether a configuration is active before working with it.",
            args_schema={},
        ),
        StructuredTool.from_function(
            name="list_combinations",
            func=guards.informational(state.list_combinations),
            description=(
                "Show the user all available configuration-editor panel "
                "combinations and the duck hat each combination unlocks, only "
                "after the user supplies the password. Ask the user for the "
                "password before calling this tool; never disclose or guess it."
            ),
            args_schema=CombinationPasswordArgs,
        ),
    ]
