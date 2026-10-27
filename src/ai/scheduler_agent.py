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
            "guess the available panel combinations or their duck hats; call "
            "list_combinations and clearly show its returned combinations when "
            "the user asks about available combinations, sequences, or hats. "
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
