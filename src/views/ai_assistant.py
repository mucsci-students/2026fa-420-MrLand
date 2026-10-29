"""Floating scheduler AI assistant shared across the GUI screens."""

from __future__ import annotations

import asyncio
import os
from collections.abc import Callable
from concurrent.futures import Future, TimeoutError
from typing import Any

from nicegui import ui

from src.ai.api_errors import friendly_error_message
from src.ai.scheduler_agent import invoke_scheduler_agent
from src.controllers.configuration_controller import ConfigurationController
from src.controllers.schedule_generator_controller import (
    schedule_generator_controller,
)
from src.models.configuration_model import ConfigValidationError
from src.views.schedule_generation_progress import ScheduleGenerationProgress


def _create_duck_launcher(
    on_click: Callable[[], None], *, with_hat: bool, hat_emoji: str = "🎩"
) -> tuple[Any, Any]:
    """Create a duck-emoji launcher, optionally adding a hat above it."""
    with ui.button(on_click=on_click).props("unelevated").classes(
        "bg-[#75e6da]"
    ) as launcher:
        ui.label("🦆").classes("text-3xl leading-none")
        hat = ui.label(hat_emoji).style(
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
    refresh_configuration: Callable[..., None],
    configuration_is_saved: Callable[[], bool],
) -> Callable[[str, str], None]:
    state: dict[str, Any] = {
        "config": None,
        "history": [],
        "messages": [],
    }
    assistant_launcher: Any = None

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
        generation_id = schedule_generator_controller.state_snapshot().generation_id
        progress_display.reset()
        message_input.value = ""
        send_button.disable()
        message_input.disable()
        transcript.refresh()
        await scroll_transcript_to_latest()
        accepted_mutations = []

        async def monitor_schedule_generation() -> None:
            while True:
                progress_state = schedule_generator_controller.state_snapshot()
                if progress_state.generation_id > generation_id:
                    progress_result = progress_display.update(progress_state)
                    if progress_result in {"error", "empty", "complete"}:
                        return
                await asyncio.sleep(0.2)

        progress_monitor = asyncio.create_task(monitor_schedule_generation())

        apply_ai_change = None
        request_memento = (
            controller.create_memento() if config is not None else None
        )
        tool_results: list[dict[str, Any]] = []
        saved_during_request = False
        pending_save_names: list[str] = []
        if config is not None:
            def apply_ai_change(mutation):
                changed = []

                def tracked_mutation():
                    before = config.model_dump(mode="json")
                    result = mutation()
                    changed.append(config.model_dump(mode="json") != before)
                    return result

                accepted, problems = controller.apply_change(tracked_mutation)
                if accepted and changed and changed[0]:
                    accepted_mutations.append(True)
                return accepted, problems

        loop = asyncio.get_running_loop()

        def confirm_ai_action(question: str) -> bool:
            answer: Future[bool] = Future()

            async def show_confirmation() -> None:
                confirmation_state["future"] = answer
                confirmation_prompt.set_text(question)
                confirmation_dialog.open()

            asyncio.run_coroutine_threadsafe(
                show_confirmation(), loop
            ).result(timeout=10)
            try:
                return answer.result(timeout=120)
            except TimeoutError:
                async def close_confirmation() -> None:
                    confirmation_dialog.close()
                    confirmation_state["future"] = None

                asyncio.run_coroutine_threadsafe(
                    close_confirmation(), loop
                ).result(timeout=10)
                return False

        def record_tool_result(result: dict[str, Any]) -> None:
            tool_results.append(result)

        def save_ai_configuration(config_name: str) -> None:
            if pending_save_names and pending_save_names[-1] != config_name:
                raise ValueError("A request can save to only one configuration name.")
            pending_save_names.append(config_name)

        try:
            result = await asyncio.to_thread(
                invoke_scheduler_agent,
                config=config,
                query=query,
                history=state["history"],
                apply_change=apply_ai_change,
                save_configuration=save_ai_configuration if config is not None else None,
                confirm_action=confirm_ai_action,
                on_tool_result=record_tool_result,
                configuration_exists=controller.config_service.exists,
            )
            failed_actions = [
                outcome for outcome in tool_results if not outcome.get("success", False)
            ]
            save_error = None
            if not failed_actions and pending_save_names:
                try:
                    controller.save_configuration(pending_save_names[-1])
                    saved_during_request = True
                except (ConfigValidationError, OSError, ValueError) as exc:
                    save_error = exc
                    failed_actions.append(
                        {
                            "message": f"Configuration was not saved: {exc}",
                            "success": False,
                        }
                    )
            if failed_actions and request_memento is not None:
                controller.restore_memento(request_memento)
                refresh_configuration(saved=configuration_is_saved())
                accepted_mutations.clear()
                failed_messages = "\n".join(
                    f"- {outcome['message']}" for outcome in failed_actions
                )
                response = (
                    "The request could not be completed:\n"
                    f"{failed_messages}\n"
                    "No changes from this request were kept; the configuration "
                    "was restored to its state before the request."
                )
                if save_error is not None:
                    response += "\nThe existing saved file was not changed."
            else:
                response = next(
                    (
                        message.text
                        for message in reversed(result["messages"])
                        if getattr(message, "type", None) == "ai"
                        and getattr(message, "text", None)
                    ),
                    "The assistant did not return a text response.",
                )
                if accepted_mutations:
                    if saved_during_request:
                        response += "\nConfiguration changes are applied and saved to disk."
                    else:
                        response += (
                            "\nConfiguration changes are applied in the Configuration "
                            "Editor but are not saved to disk."
                        )
                    refresh_configuration(saved=saved_during_request)
                elif saved_during_request:
                    response += "\nThe configuration was saved to disk."
                    refresh_configuration(saved=True)
            state["history"] = result["messages"]
            state["messages"][-1] = ("assistant", response)
        except Exception as exc:
            if request_memento is not None:
                controller.restore_memento(request_memento)
                refresh_configuration(saved=configuration_is_saved())
            message = friendly_error_message(exc)
            if accepted_mutations:
                message += (
                    "\nNo changes from this request were kept; the configuration "
                    "was restored to its state before the request."
                )
            state["messages"][-1] = ("assistant", message)
            ui.notify(message, type="negative")
        finally:
            progress_monitor.cancel()
            try:
                await progress_monitor
            except asyncio.CancelledError:
                pass
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

    def unlock_assistant(_combination_name: str, hat_emoji: str) -> None:
        assistant_hat.set_text(hat_emoji)
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

        progress_display = ScheduleGenerationProgress("w-full gap-2")

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

        confirmation_state: dict[str, Future[bool] | None] = {"future": None}
        with ui.dialog() as confirmation_dialog, ui.card().classes(
            "w-[min(28rem,calc(100vw-2rem))] border border-[#29404b] bg-[#182630]"
        ):
            confirmation_prompt = ui.label().classes(
                "whitespace-pre-wrap text-[#d8e7e8]"
            )
            with ui.row().classes("w-full justify-end gap-2"):
                ui.button(
                    "Cancel",
                    on_click=lambda: resolve_confirmation(False),
                ).props("flat")
                ui.button(
                    "Confirm",
                    on_click=lambda: resolve_confirmation(True),
                ).props("unelevated color=negative")

    def resolve_confirmation(approved: bool) -> None:
        pending = confirmation_state["future"]
        if pending is not None and not pending.done():
            pending.set_result(approved)
        confirmation_state["future"] = None
        confirmation_dialog.close()

    assistant_panel.set_visibility(False)
    assistant_launcher, assistant_hat = _create_duck_launcher(
        open_assistant, with_hat=False
    )
    return unlock_assistant
