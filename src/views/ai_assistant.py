"""Floating scheduler AI assistant shared across the GUI screens."""

from __future__ import annotations

import asyncio
import os
from collections.abc import Callable
from typing import Any

from langchain_core.exceptions import LangChainException
from nicegui import ui
from openai import OpenAIError

from src.ai.scheduler_agent import invoke_scheduler_agent
from src.controllers.configuration_controller import ConfigurationController


def _create_duck_launcher(on_click: Callable[[], None], *, with_hat: bool) -> Any:
    """Create a duck-emoji launcher, optionally adding a hat above it."""
    with ui.button(on_click=on_click).props("unelevated").classes(
        "bg-[#75e6da]"
    ) as launcher:
        ui.label("🦆").classes("text-3xl leading-none")
        if with_hat:
            ui.label("🎩").style(
                "position: absolute; top: -7px; left: 50%; "
                "transform: translateX(-50%); font-size: 20px; line-height: 1;"
            )
    launcher.style(
        "position: fixed; right: 20px; bottom: 20px; z-index: 10000; "
        "width: 64px; height: 64px; border-radius: 50%; "
        "display: flex; align-items: center; justify-content: center;"
    )
    return launcher


def give_hat(on_click: Callable[[], None]) -> Any:
    """Create the unlocked, top-hat launcher for the scheduler assistant."""
    return _create_duck_launcher(on_click, with_hat=True)


def give_duck(on_click: Callable[[], None]) -> Any:
    """Create the default duck launcher for the scheduler assistant."""
    return _create_duck_launcher(on_click, with_hat=False)


def scheduler_ai_assistant(
    controller: ConfigurationController,
    refresh_configuration: Callable[[], None],
) -> Callable[[], None]:
    state: dict[str, Any] = {
        "config": None,
        "history": [],
        "messages": [],
    }
    assistant_launcher: Any = None
    assistant_unlocked = False

    @ui.refreshable
    def transcript() -> None:
        if not state["messages"]:
            ui.label(
                "Ask about or make changes to the active scheduler configuration."
            ).classes("text-sm text-[#9fb2b8]")
            return
        for role, text in state["messages"]:
            is_user = role == "user"
            with ui.card().classes(
                "max-w-[90%] border border-[#29404b] "
                + ("ml-auto bg-[#203b42]" if is_user else "mr-auto bg-[#101820]")
            ):
                ui.label("You" if is_user else "Scheduler AI").classes(
                    "text-xs font-semibold text-[#75e6da]"
                )
                ui.label(text).classes(
                    "whitespace-pre-wrap break-words text-sm text-[#d8e7e8]"
                )

    async def send_prompt() -> None:
        query = (message_input.value or "").strip()
        if not query:
            return

        config = controller.configuration
        if config is None:
            ui.notify(
                "Create or load a configuration in the Configuration Editor first.",
                type="warning",
            )
            return
        if state["config"] is not config:
            state["config"] = config
            state["history"] = []
            state["messages"] = []

        api_key = (api_key_input.value or "").strip() or None
        if not api_key and not os.environ.get("OPENAI_API_KEY"):
            ui.notify("Enter an OpenAI API key to use the assistant.", type="warning")
            return

        state["messages"].append(("user", query))
        state["messages"].append(("assistant", "Thinking…"))
        message_input.value = ""
        send_button.disable()
        message_input.disable()
        transcript.refresh()
        accepted_mutations = []

        def apply_ai_change(mutation):
            before = config.model_dump(mode="json")
            accepted, problems = controller.apply_change(mutation)
            if accepted and config.model_dump(mode="json") != before:
                accepted_mutations.append(True)
            return accepted, problems

        try:
            result = await asyncio.to_thread(
                invoke_scheduler_agent,
                config=config,
                query=query,
                history=state["history"],
                api_key=api_key,
                apply_change=apply_ai_change,
            )
            state["history"] = result["messages"]
            response = next(
                (
                    message.text
                    for message in reversed(result["messages"])
                    if getattr(message, "type", None) == "ai"
                    and getattr(message, "text", None)
                ),
                "The assistant did not return a text response.",
            )
            state["messages"][-1] = ("assistant", response)
            if accepted_mutations:
                refresh_configuration()
        except (LangChainException, OpenAIError, TypeError, ValueError) as exc:
            state["messages"][-1] = ("assistant", f"AI request failed: {exc}")
        finally:
            send_button.enable()
            message_input.enable()
            transcript.refresh()

    def open_assistant() -> None:
        assistant_panel.set_visibility(True)
        if assistant_launcher is not None:
            assistant_launcher.set_visibility(False)

    def close_assistant() -> None:
        assistant_panel.set_visibility(False)
        if assistant_launcher is not None:
            assistant_launcher.set_visibility(True)

    def unlock_assistant() -> None:
        nonlocal assistant_launcher, assistant_unlocked
        if assistant_unlocked:
            return
        assistant_unlocked = True
        if assistant_launcher is not None:
            assistant_launcher.set_visibility(False)
        assistant_launcher = give_hat(open_assistant)

    with ui.card().classes(
        "border border-[#29404b] bg-[#182630] p-3"
    ) as assistant_panel:
        assistant_panel.style(
            "position: fixed; right: 20px; bottom: 20px; z-index: 9999; "
            "width: min(440px, calc(100vw - 40px));"
        )
        with ui.row().classes("w-full items-center justify-between"):
            with ui.row().classes("items-center gap-2"):
                ui.icon("auto_awesome").classes("text-[#75e6da]")
                ui.label("Scheduler AI").classes("font-semibold text-white")
            ui.button(icon="close", on_click=close_assistant).props(
                "flat round"
            ).classes("text-[#75e6da]")

        with ui.column().classes(
            "mb-3 max-h-80 w-full gap-2 overflow-y-auto rounded border "
            "border-[#29404b] p-3"
        ):
            transcript()

        if not os.environ.get("OPENAI_API_KEY"):
            api_key_input = (
                ui.input(
                    "OpenAI API key",
                    password=True,
                    password_toggle_button=True,
                )
                .props("autocomplete=off dense")
                .classes("mb-2 w-full")
            )
        else:
            api_key_input = (
                ui.input(
                    "OpenAI API key (optional override)",
                    password=True,
                    password_toggle_button=True,
                )
                .props("autocomplete=off dense")
                .classes("mb-2 w-full")
            )

        with ui.row().classes("w-full items-center gap-2"):
            message_input = (
                ui.input(
                    placeholder="Ask the scheduler assistant...",
                )
                .props("outlined dense")
                .classes("flex-1")
            )
            message_input.on("keydown.enter", lambda: send_prompt())
            send_button = (
                ui.button(icon="send", on_click=send_prompt)
                .props("unelevated round")
                .classes("bg-[#75e6da] text-[#101820]")
            )

    assistant_panel.set_visibility(False)
    assistant_launcher = give_duck(open_assistant)
    return unlock_assistant
