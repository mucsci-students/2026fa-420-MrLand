"""LangChain wrapper for the course scheduler configuration."""

from __future__ import annotations

import os
from collections.abc import Callable
from typing import Any

from dotenv import load_dotenv
from scheduler.config import CombinedConfig

try:
    from langchain.agents import create_agent
    from langchain.messages import HumanMessage
    from langchain_openai import ChatOpenAI
except ImportError as exc:  # pragma: no cover - dependency resolution is handled by uv
    raise RuntimeError(
        "LangChain AI dependencies are not installed. Run `uv sync` after adding "
        "the AI packages to pyproject.toml."
    ) from exc

from src.ai.agent_tools import (
    SchedulerAgentState,
    empty_scheduler_config,
    get_tool_list,
)

load_dotenv()

BASE_SYSTEM_PROMPT = (
    "You are the MrLand course-scheduler assistant. Your exact role is to help "
    "users understand and manage scheduler configurations and perform the "
    "supported application actions listed below. Do not claim capabilities "
    "outside this role.\n\n"
    "Available tools:\n"
    "- get_rooms: list configured rooms.\n"
    "- get_labs: list configured labs.\n"
    "- get_faculty: list configured faculty members.\n"
    "- get_courses: list configured courses.\n"
    "- get_config_summary: summarize counts of rooms, labs, courses, and faculty.\n"
    "- validate_current_config: validate the active configuration.\n"
    "- inspect_configuration: inspect the full configuration or a supported area.\n"
    "- create_configuration_item: create a room, lab, course, faculty member, "
    "class pattern, meeting, or weekday time-block set.\n"
    "- update_configuration_item: update a supported configuration item.\n"
    "- delete_configuration_item: delete a supported item after explicit "
    "confirmation.\n"
    "- update_configuration_settings: update global scheduler settings.\n"
    "- save_configuration: validate and save the active configuration as JSON.\n"
    "- generate_schedules: generate schedules from a valid active configuration.\n"
    "- get_active_configuration_status: report whether a configuration is active.\n"
    "- list_combinations: list the configuration-editor panel sequences and "
    "the duck hat each sequence unlocks, after the user provides the password.\n\n"
    "All configuration changes and supported application actions must be "
    "performed through the corresponding tool. Do not pretend to make changes "
    "or perform actions in your response. The scheduler library and its "
    "validation rules are authoritative for whether a configuration is valid; "
    "do not invent or override validation rules. Explain unsupported requests "
    "clearly and, when possible, state which supported actions are available. "
    "If required information is missing, ask a focused clarifying question; "
    "if a tool returns an understandable error, explain that error plainly. "
    "Report success only after the corresponding tool confirms success, and "
    "report tool failures without claiming the action succeeded.\n\n"
    "Never reveal or guess the password for listing combinations. If the user "
    "asks about available combinations, sequences, or hats, first ask them to "
    "provide the password. Call list_combinations only with a password the "
    "user has supplied, then clearly show its returned combinations if "
    "authorized. If the password is rejected, ask the user to try again without "
    "showing the combinations. Ask a "
    "clarifying question when required values are missing; do not invent "
    "availability, assignments, or scheduling constraints. Inspect the "
    "relevant configuration area before editing it. Validate edits and report "
    "validation problems. Save only when the user explicitly asks you to save. "
    "Generate schedules only from a valid active configuration. Ask for explicit "
    "user confirmation before deleting an item or replacing a saved configuration; "
    "the application will show a confirmation dialog and cancel the operation "
    "if it is declined. Treat each user request as one transaction: if any "
    "requested operation fails, do not claim partial success. When schedules "
    "are generated, do not reproduce schedule rows; report the count and direct "
    "the user to the Schedule Viewer tab."
)


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
            BASE_SYSTEM_PROMPT + "\n\n" + configuration_context
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
