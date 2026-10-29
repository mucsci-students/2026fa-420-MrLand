"""Shared progress display for schedule generation workflows."""

from nicegui import ui

from src.models.schedule_generator_model import ScheduleGenerationState


class ScheduleGenerationProgress:
    def __init__(self, container_classes: str) -> None:
        with ui.column().classes(container_classes) as self.container:
            self.message = ui.label("Starting scheduler...").classes("text-sm text-gray-300")
            self.bar = ui.linear_progress(value=0).classes("w-full")
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
            self.destination = ui.label("").classes("text-sm text-gray-400")
        self.container.set_visibility(False)
        self.destination.set_visibility(False)

    def reset(self) -> None:
        self.container.set_visibility(False)
        self.message.text = "Starting scheduler..."
        self.bar.value = 0
        self.percentage.text = "0%"
        self.status.text = "Generated 0 of 0 schedules"
        self.spinner.set_visibility(False)
        self.spinner_label.set_visibility(False)
        self.destination.text = ""
        self.destination.set_visibility(False)

    def start(self, requested: int, message: str) -> None:
        self.container.set_visibility(True)
        self.message.text = message
        self.bar.value = 0
        self.percentage.text = "0%"
        self.status.text = f"Generated 0 of {requested} schedules"
        self.spinner.set_visibility(True)
        self.spinner_label.set_visibility(True)
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
        self.spinner.set_visibility(state.running)
        self.spinner_label.set_visibility(state.running)

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
