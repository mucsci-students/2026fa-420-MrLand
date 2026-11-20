"""Scheduler assistant conversation state and request lifecycle."""

from __future__ import annotations

import asyncio
import os
from collections.abc import Awaitable, Callable, Mapping
from concurrent.futures import Future, TimeoutError
from dataclasses import dataclass
from typing import Any

from nicegui import ui
from scheduler.config import CombinedConfig

from src.ai.api_errors import friendly_error_message
from src.ai.scheduler_agent import invoke_scheduler_agent
from src.controllers.configuration_controller import ConfigurationController
from src.controllers.schedule_generator_controller import schedule_generator_controller
from src.models.configuration_model import ConfigValidationError


@dataclass
class AssistantConversationView:
    message_input: Any
    send_button: Any
    refresh_transcript: Callable[[], Any]
    scroll_transcript_to_latest: Callable[[], Awaitable[None]]
    progress_display: Any
    confirmation_state: dict[str, Future[bool] | None]
    confirmation_prompt: Any
    confirmation_dialog: Any


class AssistantConversation:
    def __init__(
        self,
        controller: ConfigurationController,
        refresh_configuration: Callable[..., None],
        configuration_is_saved: Callable[[], bool],
        download_configuration: Callable[[str], str],
        apply_configuration_change: Callable[[Callable[[], Any]], tuple[bool, list[Any]]] | None,
        undo_configuration: Callable[[], Any] | None,
        redo_configuration: Callable[[], Any] | None,
        create_history_snapshot: Callable[[], Any] | None,
        restore_history_snapshot: Callable[[Any], None] | None,
    ) -> None:
        self.controller = controller
        self.refresh_configuration = refresh_configuration
        self.configuration_is_saved = configuration_is_saved
        self.download_configuration = download_configuration
        self.apply_configuration_change = apply_configuration_change
        self.undo_configuration = undo_configuration
        self.redo_configuration = redo_configuration
        self.create_history_snapshot = create_history_snapshot
        self.restore_history_snapshot = restore_history_snapshot
        self.config: CombinedConfig | None = None
        self.history: list[Any] = []
        self.messages: list[tuple[str, str]] = []

    async def send_prompt(self, query: str, view: AssistantConversationView) -> None:
        query = (query or "").strip()
        if not query:
            return

        config = self.controller.configuration
        if self.config is not config:
            self.config = config
            self.history = []
            self.messages = []

        if not os.environ.get("OPENAI_API_KEY"):
            ui.notify(
                "No OpenAI API key found. Add OPENAI_API_KEY to the .env file.",
                type="warning",
            )
            return

        self.messages.append(("user", query))
        self.messages.append(("assistant", "Thinking…"))
        generation_id = schedule_generator_controller.state_snapshot().generation_id
        view.progress_display.reset()
        view.message_input.value = ""
        view.send_button.disable()
        view.message_input.disable()
        view.refresh_transcript()
        await view.scroll_transcript_to_latest()
        accepted_mutations = []

        async def monitor_schedule_generation() -> None:
            while True:
                progress_state = schedule_generator_controller.state_snapshot()
                if progress_state.generation_id > generation_id:
                    progress_result = view.progress_display.update(progress_state)
                    if progress_result in {"error", "empty", "complete"}:
                        return
                await asyncio.sleep(0.2)

        progress_monitor = asyncio.create_task(monitor_schedule_generation())

        loop = asyncio.get_running_loop()

        def run_editor_callback(callback: Callable[..., Any], *arguments: Any) -> Any:
            async def invoke_callback() -> Any:
                return callback(*arguments)

            return asyncio.run_coroutine_threadsafe(invoke_callback(), loop).result(timeout=120)

        apply_ai_change = None
        request_memento = self.controller.create_memento() if config is not None else None
        history_snapshot = (
            self.create_history_snapshot()
            if config is not None and self.create_history_snapshot is not None
            else None
        )
        tool_results: list[Mapping[str, object]] = []
        saved_during_request = False
        pending_save_names: list[str] = []
        if config is not None:

            def apply_ai_change(mutation):
                if self.apply_configuration_change is None:
                    accepted, problems = self.controller.apply_change(mutation)
                else:
                    accepted, problems = run_editor_callback(
                        self.apply_configuration_change, mutation
                    )
                if accepted:
                    accepted_mutations.append(True)
                return accepted, problems

        def apply_ai_undo() -> Any:
            if self.undo_configuration is None:
                return None
            result = run_editor_callback(self.undo_configuration)
            if result is not None:
                accepted_mutations.append(True)
            return result

        def apply_ai_redo() -> Any:
            if self.redo_configuration is None:
                return None
            result = run_editor_callback(self.redo_configuration)
            if result is not None:
                accepted_mutations.append(True)
            return result

        def confirm_ai_action(question: str) -> bool:
            answer: Future[bool] = Future()

            async def show_confirmation() -> None:
                view.confirmation_state["future"] = answer
                view.confirmation_prompt.set_text(question)
                view.confirmation_dialog.open()

            asyncio.run_coroutine_threadsafe(show_confirmation(), loop).result(timeout=10)
            try:
                return answer.result(timeout=120)
            except TimeoutError:

                async def close_confirmation() -> None:
                    view.confirmation_dialog.close()
                    view.confirmation_state["future"] = None

                asyncio.run_coroutine_threadsafe(close_confirmation(), loop).result(timeout=10)
                return False

        def record_tool_result(result: Mapping[str, object]) -> None:
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
                history=self.history,
                apply_change=apply_ai_change,
                save_configuration=save_ai_configuration if config is not None else None,
                confirm_action=confirm_ai_action,
                on_tool_result=record_tool_result,
                undo_configuration=apply_ai_undo if config is not None else None,
                redo_configuration=apply_ai_redo if config is not None else None,
            )
            failed_actions = [
                outcome for outcome in tool_results if not outcome.get("success", False)
            ]
            save_error = None
            if not failed_actions and pending_save_names:
                try:
                    self.download_configuration(pending_save_names[-1])
                    saved_during_request = True
                except (ConfigValidationError, OSError, ValueError) as exc:
                    save_error = exc
                    failed_actions.append(
                        {
                            "message": f"Configuration was not downloaded: {exc}",
                            "success": False,
                        }
                    )
            if failed_actions and request_memento is not None:
                self.controller.restore_memento(request_memento)
                if history_snapshot is not None and self.restore_history_snapshot is not None:
                    self.restore_history_snapshot(history_snapshot)
                self.refresh_configuration(saved=self.configuration_is_saved())
                accepted_mutations.clear()
                failed_messages = "\n".join(f"- {outcome['message']}" for outcome in failed_actions)
                response = (
                    "The request could not be completed:\n"
                    f"{failed_messages}\n"
                    "No changes from this request were kept; the configuration "
                    "was restored to its state before the request."
                )
                if save_error is not None:
                    response += "\nNo configuration file was downloaded."
            else:
                response = next(
                    (
                        message.text
                        for message in reversed(result["messages"])
                        if getattr(message, "type", None) == "ai" and getattr(message, "text", None)
                    ),
                    "The assistant did not return a text response.",
                )
                if accepted_mutations:
                    if saved_during_request:
                        response += "\nConfiguration changes are applied and downloaded."
                    else:
                        response += (
                            "\nConfiguration changes are applied in the Configuration "
                            "Editor but are not saved to disk."
                        )
                    self.refresh_configuration(saved=saved_during_request)
                elif saved_during_request:
                    response += "\nA configuration copy was downloaded."
                    self.refresh_configuration(saved=True)
            self.history = result["messages"]
            self.messages[-1] = ("assistant", response)
        except Exception as exc:  # noqa: BLE001 - surface unexpected assistant callback failures to the user
            if request_memento is not None:
                self.controller.restore_memento(request_memento)
                if history_snapshot is not None and self.restore_history_snapshot is not None:
                    self.restore_history_snapshot(history_snapshot)
                self.refresh_configuration(saved=self.configuration_is_saved())
            message = friendly_error_message(exc)
            if accepted_mutations:
                message += (
                    "\nNo changes from this request were kept; the configuration "
                    "was restored to its state before the request."
                )
            self.messages[-1] = ("assistant", message)
            ui.notify(message, type="negative")
        finally:
            progress_monitor.cancel()
            try:
                await progress_monitor
            except asyncio.CancelledError:
                pass
            view.send_button.enable()
            view.message_input.enable()
            view.refresh_transcript()
            await view.scroll_transcript_to_latest()
