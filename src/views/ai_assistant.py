"""Floating scheduler AI assistant shared across the GUI screens."""

from __future__ import annotations

import asyncio
import os
from collections.abc import Callable
from typing import Any

from nicegui import ui

from src.ai.api_errors import friendly_error_message
from src.ai.scheduler_agent import invoke_scheduler_agent
from src.controllers.configuration_controller import ConfigurationController


def _create_duck_launcher(
    on_click: Callable[[], None], *, with_hat: bool
) -> tuple[Any, Any]:
    """Create a duck-emoji launcher, optionally adding a hat above it."""
    with ui.button(on_click=on_click).props("unelevated").classes(
        "bg-[#75e6da]"
    ) as launcher:
        ui.label("🦆").classes("text-3xl leading-none")
        hat = ui.label("🎩").style(
            "position: absolute; top: -7px; left: 50%; "
            "transform: translateX(-50%); font-size: 20px; line-height: 1;"
        )
        if not with_hat:
            hat.set_visibility(False)
    launcher.style(
        "position: fixed; right: 20px; bottom: 20px; z-index: 10000; "
        "width: 64px; height: 64px; border-radius: 50%; "
        "display: flex; align-items: center; justify-content: center;"
    )
    return launcher, hat


def give_hat(on_click: Callable[[], None]) -> Any:
    """Create the unlocked, top-hat launcher for the scheduler assistant."""
    launcher, _ = _create_duck_launcher(on_click, with_hat=True)
    return launcher


def give_duck(on_click: Callable[[], None]) -> Any:
    """Create the default duck launcher for the scheduler assistant."""
    launcher, _ = _create_duck_launcher(on_click, with_hat=False)
    return launcher


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
                "Ask scheduler questions. Load a configuration in the "
                "Configuration Editor before asking the assistant to work with it."
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

    async def scroll_transcript_to_latest() -> None:
        await ui.run_javascript(
            """
            const transcript = document.getElementById('scheduler-ai-transcript');
            if (transcript) {
                requestAnimationFrame(() => {
                    transcript.scrollTop = transcript.scrollHeight;
                });
            }
            """
        )

    async def send_prompt() -> None:
        query = (message_input.value or "").strip()
        if not query:
            return

        config = controller.configuration
        if state["config"] is not config:
            state["config"] = config
            state["history"] = []
            state["messages"] = []

        if not os.environ.get("OPENAI_API_KEY"):
            ui.notify(
                "No OpenAI API key found. Add OPENAI_API_KEY to the .env file.",
                type="warning",
            )
            return

        state["messages"].append(("user", query))
        state["messages"].append(("assistant", "Thinking…"))
        message_input.value = ""
        send_button.disable()
        message_input.disable()
        transcript.refresh()
        await scroll_transcript_to_latest()
        accepted_mutations = []

        apply_ai_change = None
        if config is not None:
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
                apply_change=apply_ai_change,
                save_configuration=(
                    controller.save_configuration if config is not None else None
                ),
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
        except Exception as exc:
            message = friendly_error_message(exc)
            state["messages"][-1] = ("assistant", message)
            ui.notify(message, type="negative")
        finally:
            send_button.enable()
            message_input.enable()
            transcript.refresh()
            await scroll_transcript_to_latest()

    def open_assistant() -> None:
        assistant_panel.set_visibility(True)
        if assistant_launcher is not None:
            assistant_launcher.set_visibility(False)

    def close_assistant() -> None:
        assistant_panel.set_visibility(False)
        if assistant_launcher is not None:
            assistant_launcher.set_visibility(True)

    def unlock_assistant() -> None:
        nonlocal assistant_unlocked
        if assistant_unlocked:
            return
        assistant_unlocked = True
        assistant_hat.set_visibility(True)

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

        with ui.column().props("id=scheduler-ai-transcript").classes(
            "mb-3 max-h-80 w-full gap-2 overflow-y-auto rounded border "
            "border-[#29404b] p-3"
        ):
            transcript()


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
    assistant_launcher, assistant_hat = _create_duck_launcher(
        open_assistant, with_hat=False
    )
    return unlock_assistant
