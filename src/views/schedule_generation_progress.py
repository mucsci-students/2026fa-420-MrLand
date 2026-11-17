"""Shared progress display for schedule generation workflows."""

from collections.abc import Callable
from time import monotonic

from nicegui import ui

from src.models.schedule_generator_model import ScheduleGenerationState

DIAGNOSIS_CANCEL_DELAY_SECONDS = 60


class ScheduleGenerationProgress:
    def __init__(
        self,
        container_classes: str,
        on_cancel: Callable[[], None] | None = None,
    ) -> None:
        self._diagnosing_since: float | None = None
        with ui.column().classes(container_classes) as self.container:
            self.message = ui.label("Starting scheduler...").classes("text-sm text-gray-300")
            self.bar = ui.linear_progress(value=0, show_value=False).classes("w-full")
            with ui.row().classes("w-full items-center justify-between"):
                self.percentage = ui.label("0%").classes("text-sm text-gray-300")
                self.status = ui.label("Generated 0 of 0 schedules").classes(
                    "text-sm text-gray-400"
                )
            with ui.row().classes("items-center gap-2"):
                self.spinner = ui.spinner(size="24px")
                self.spinner_label = ui.label("Z3 is searching for schedules...").classes(
                    "text-sm text-gray-400"
                )
            self.cancel_button = None
            if on_cancel is not None:
                self.cancel_button = ui.button(
                    "Stop analysis and show no-solution result",
                    on_click=on_cancel,
                ).props("outline").classes("border-[#45616b] text-[#d8e7e8]")
            self.destination = ui.label("").classes("text-sm text-gray-400")
        self.container.set_visibility(False)
        if self.cancel_button is not None:
            self.cancel_button.set_visibility(False)
        self.destination.set_visibility(False)

    def reset(self) -> None:
        self.container.set_visibility(False)
        self._diagnosing_since = None
        self.message.text = "Starting scheduler..."
        self.bar.value = 0
        self.percentage.text = "0%"
        self.status.text = "Generated 0 of 0 schedules"
        self.spinner_label.text = "Z3 is searching for schedules..."
        self.spinner.set_visibility(False)
        self.spinner_label.set_visibility(False)
        if self.cancel_button is not None:
            self.cancel_button.set_visibility(False)
            self.cancel_button.set_enabled(True)
            self.cancel_button.set_text("Stop analysis and show no-solution result")
        self.destination.text = ""
        self.destination.set_visibility(False)

    def start(self, requested: int, message: str) -> None:
        self.container.set_visibility(True)
        self._diagnosing_since = None
        self.message.text = message
        self.bar.value = 0
        self.percentage.text = "0%"
        self.status.text = f"Generated 0 of {requested} schedules"
        self.spinner_label.text = "Z3 is searching for schedules..."
        self.spinner.set_visibility(True)
        self.spinner_label.set_visibility(True)
        if self.cancel_button is not None:
            self.cancel_button.set_visibility(False)
            self.cancel_button.set_enabled(True)
            self.cancel_button.set_text("Stop analysis and show no-solution result")
        self.destination.set_visibility(False)

    def update(self, state: ScheduleGenerationState) -> str | None:
        if not state.running and not state.finished:
            return None

        percentage = 0
        if state.requested > 0:
            percentage = min(state.generated / state.requested, 1)
        self.container.set_visibility(True)
        self.bar.value = percentage
        self.percentage.text = f"{percentage * 100:.0f}%"
        self.message.text = state.message
        if state.requested > 0:
            self.status.text = f"Generated {state.generated} of {state.requested} schedules"
        self.spinner_label.text = (
            "Stopping diagnosis..."
            if state.cancel_requested
            else (
                "Analyzing schedule constraints..."
                if state.diagnosing
                else "Z3 is searching for schedules..."
            )
        )
        self.spinner.set_visibility(state.running)
        self.spinner_label.set_visibility(state.running)

        if state.diagnosing:
            if self._diagnosing_since is None:
                self._diagnosing_since = monotonic()
            if self.cancel_button is not None:
                show_cancel = (
                    state.cancel_requested
                    or monotonic() - self._diagnosing_since >= DIAGNOSIS_CANCEL_DELAY_SECONDS
                )
                self.cancel_button.set_visibility(show_cancel)
                self.cancel_button.set_enabled(not state.cancel_requested)
                if state.cancel_requested:
                    self.cancel_button.set_text("Stopping diagnosis...")
        else:
            self._diagnosing_since = None
            if self.cancel_button is not None:
                self.cancel_button.set_visibility(False)
                self.cancel_button.set_enabled(True)
                self.cancel_button.set_text("Stop analysis and show no-solution result")

        if state.running or not state.finished:
            return "running"
        if state.error:
            self.message.text = "Schedule generation failed."
            return "error"
        if state.generated == 0:
            self.bar.value = 0
            self.percentage.text = "0%"
            self.message.text = "No valid schedules could be generated."
            return "empty"

        self.bar.value = 1
        self.percentage.text = "100%"
        self.message.text = "Schedule generation complete."
        self.status.text = f"Generated {state.generated} of {state.requested} requested schedules"
        self.destination.text = "View the generated schedules in the Schedule Viewer tab."
        self.destination.set_visibility(True)
        return "complete"
