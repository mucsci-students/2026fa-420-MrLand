"""Floating scheduler AI assistant shared across the GUI screens."""

from __future__ import annotations

from collections.abc import Callable
from concurrent.futures import Future
from typing import Any

from nicegui import ui

from src.controllers.configuration_controller import ConfigurationController
from src.views.ai_assistant_conversation import (
    AssistantConversation,
    AssistantConversationView,
)
from src.views.schedule_generation_progress import ScheduleGenerationProgress


def _create_duck_launcher(
    on_click: Callable[[], None], *, with_hat: bool, hat_emoji: str = "🎩"
) -> tuple[Any, Any]:
    """Create a duck-emoji launcher, optionally adding a hat above it."""
    with ui.button(on_click=on_click).props("unelevated").classes("bg-[#75e6da]") as launcher:
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
    download_configuration: Callable[[str], str],
    apply_configuration_change: Callable[[Callable[[], Any]], tuple[bool, list[Any]]] | None = None,
    undo_configuration: Callable[[], Any] | None = None,
    redo_configuration: Callable[[], Any] | None = None,
    create_history_snapshot: Callable[[], Any] | None = None,
    restore_history_snapshot: Callable[[Any], None] | None = None,
) -> Callable[[str, str], None]:
    conversation = AssistantConversation(
        controller,
        refresh_configuration,
        configuration_is_saved,
        download_configuration,
        apply_configuration_change,
        undo_configuration,
        redo_configuration,
        create_history_snapshot,
        restore_history_snapshot,
    )
    assistant_view: AssistantConversationView
    assistant_launcher: Any = None

    @ui.refreshable
    def transcript() -> None:
        if not conversation.messages:
            ui.label(
                "Ask scheduler questions. Load a configuration in the "
                "Configuration Editor before asking the assistant to work with it."
            ).classes("text-sm text-[#9fb2b8]")
            return
        for role, text in conversation.messages:
            is_user = role == "user"
            with ui.card().classes(
                "max-w-[90%] border border-[#29404b] "
                + ("ml-auto bg-[#203b42]" if is_user else "mr-auto bg-[#101820]")
            ):
                ui.label("You" if is_user else "Scheduler AI").classes(
                    "text-xs font-semibold text-[#75e6da]"
                )
                ui.label(text).classes("whitespace-pre-wrap break-words text-sm text-[#d8e7e8]")

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
        await conversation.send_prompt(message_input.value or "", assistant_view)

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

    with ui.card().classes("border border-[#29404b] bg-[#182630] p-3") as assistant_panel:
        assistant_panel.style(
            "position: fixed; right: 20px; bottom: 20px; z-index: 9999; "
            "width: min(440px, calc(100vw - 40px));"
        )
        with ui.row().classes("w-full items-center justify-between"):
            with ui.row().classes("items-center gap-2"):
                ui.icon("auto_awesome").classes("text-[#75e6da]")
                ui.label("Scheduler AI").classes("font-semibold text-white")
            ui.button(icon="close", on_click=close_assistant).props("flat round").classes(
                "text-[#75e6da]"
            )

        progress_display = ScheduleGenerationProgress("w-full gap-2")

        with (
            ui.column()
            .props("id=scheduler-ai-transcript")
            .classes(
                "mb-3 max-h-80 w-full gap-2 overflow-y-auto rounded border border-[#29404b] p-3"
            )
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
            message_input.on("keydown.enter", send_prompt)
            send_button = (
                ui.button(icon="send")
                .props("unelevated round")
                .classes("bg-[#75e6da] text-[#101820]")
            )

        confirmation_state: dict[str, Future[bool] | None] = {"future": None}
        with (
            ui.dialog() as confirmation_dialog,
            ui.card().classes(
                "w-[min(28rem,calc(100vw-2rem))] border border-[#29404b] bg-[#182630]"
            ),
        ):
            confirmation_prompt = ui.label().classes("whitespace-pre-wrap text-[#d8e7e8]")
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

    assistant_view = AssistantConversationView(
        message_input=message_input,
        send_button=send_button,
        refresh_transcript=transcript.refresh,
        scroll_transcript_to_latest=scroll_transcript_to_latest,
        progress_display=progress_display,
        confirmation_state=confirmation_state,
        confirmation_prompt=confirmation_prompt,
        confirmation_dialog=confirmation_dialog,
    )
    send_button.on_click(send_prompt)
    assistant_panel.set_visibility(False)
    assistant_launcher, assistant_hat = _create_duck_launcher(open_assistant, with_hat=False)
    return unlock_assistant
