"""Temporary configuration experiments and alternative schedule comparison."""

from collections.abc import Callable
from pathlib import Path

from nicegui import ui
from scheduler.config import CombinedConfig

from src.controllers.configuration_controller import ConfigurationController
from src.controllers.schedule_controller import schedule_controller
from src.controllers.schedule_generator_controller import ScheduleGeneratorController
from src.models.configuration_model import (
    ConfigValidationError,
    validate_config,
)
from src.models.configuration_repository import ConfigLoadError
from src.models.schedule_files import records_from_result
from src.models.what_if_session import WhatIfSession
from src.views.class_patterns_gui import class_patterns_gui
from src.views.courses_gui import courses_gui
from src.views.faculty_gui import faculty_gui
from src.views.global_settings_gui import global_settings_gui
from src.views.labs_gui import labs_gui
from src.views.rooms_gui import rooms_gui
from src.views.schedule_analysis.analysis_components import surface_card
from src.views.time_blocks_gui import time_blocks_gui


async def _read_upload(event) -> tuple[str, bytes]:
    if hasattr(event, "file"):
        return event.file.name, await event.file.read()
    return event.name, event.content.read()


class WhatIfTab:
    """Build an isolated configuration editor and alternative schedule comparison."""

    def __init__(self) -> None:
        self._session: WhatIfSession | None = None
        self._what_if_controller: ConfigurationController | None = None
        self._pending_forms: set[str] = set()
        self._generator = ScheduleGeneratorController()
        self._discard_running_result = False
        current_schedule = schedule_controller.current
        self._original_records = (
            list(current_schedule.records) if current_schedule is not None else []
        )
        self._original_label = (
            current_schedule.label if current_schedule is not None else "No original schedule"
        )

    def has_unsaved_changes(self) -> bool:
        return bool(
            self._pending_forms or (self._session is not None and self._session.has_changes)
        )

    def discard_changes(self) -> None:
        self._discard_running_result = self._generator.state_snapshot().running
        if self._session is not None:
            self._session.discard()
            self._what_if_controller = ConfigurationController(self._session.configuration)
            self._pending_forms.clear()
            self._invalidate_results()
            if hasattr(self, "_configuration_editor"):
                self._configuration_editor.refresh()
            self._refresh_status()

    def refresh_original_schedule(self) -> None:
        if self.has_unsaved_changes():
            return
        current_schedule = schedule_controller.current
        self._original_records = (
            list(current_schedule.records) if current_schedule is not None else []
        )
        self._original_label = (
            current_schedule.label if current_schedule is not None else "No original schedule"
        )
        if hasattr(self, "_comparison_heading"):
            self._comparison_heading.set_text(
                f"Alternative schedules are compared against: {self._original_label}."
            )
        self._render_comparison()

    def build(self) -> None:
        """Render configuration upload and alternative schedule comparison."""
        self._config_loader = ConfigurationController()
        with surface_card(
            "What-If Configuration",
            "Load a configuration and experiment with temporary changes. Your saved configuration is never modified.",
        ):
            self._source_status = ui.label("No configuration loaded.").classes("text-sm")
            self._source_status.style("color: var(--text-muted)")
            ui.button(
                "Load configuration",
                icon="folder_open",
                on_click=self._open_upload_dialog,
            ).props("outline")
            self._draft_status = ui.label("No What-If changes").classes("text-xs")
            self._draft_status.style("color: var(--text-muted)")
            self._configuration_editor()

        with (
            ui.dialog() as self._upload_dialog,
            ui.card().classes("w-[480px] max-w-full gap-3"),
        ):
            ui.label("Load Configuration").classes("text-lg font-semibold")
            ui.label("Select a JSON configuration file from your computer.").classes("text-sm")
            self._config_upload = (
                ui.upload(
                    label="Choose configuration file",
                    auto_upload=True,
                    on_upload=self._load_uploaded_config,
                    max_files=1,
                )
                .props("accept=.json flat bordered")
                .classes("w-full")
            )
            ui.button("Cancel", on_click=self._upload_dialog.close).props("flat")

        with surface_card(
            "Generate and Compare",
        ):
            self._comparison_heading = ui.label(
                f"Alternative schedules are compared against: {self._original_label}."
            ).classes("text-sm")
            self._comparison_heading.style("color: var(--text-muted)")
            self._generation_status = ui.label("").classes("text-sm")
            self._generation_status.style("color: var(--text-muted)")
            ui.button(
                "Generate Alternative Schedule",
                icon="auto_awesome",
                on_click=self._generate,
            ).props("unelevated")
            self._alternative_select = (
                ui.select({}, label="Alternative schedule")
                .classes("w-full max-w-2xl")
                .props("outlined")
            )
            self._alternative_select.disable()
            self._alternative_select.on_value_change(lambda _: self._render_comparison())
            self._result_container = ui.column().classes("w-full")

        self._progress_timer = ui.timer(0.25, self._update_generation)

    def _set_session(
        self,
        config: CombinedConfig,
        name: str,
    ) -> bool:
        if self._generator.state_snapshot().running:
            ui.notify(
                "Wait for schedule generation to finish before changing configurations.",
                type="warning",
            )
            return False
        self._session = WhatIfSession(config, name)
        self._what_if_controller = ConfigurationController(self._session.configuration)
        self._pending_forms.clear()
        self._generator.clear_generated_schedules()
        if hasattr(self, "_result_container"):
            self._result_container.clear()
            self._alternative_select.options = {}
            self._alternative_select.value = None
            self._alternative_select.disable()
            self._alternative_select.update()
        if hasattr(self, "_source_status"):
            self._source_status.set_text(f"Loaded {name}.")
        if hasattr(self, "_generation_status"):
            self._generation_status.set_text("")
        if hasattr(self, "_configuration_editor"):
            self._configuration_editor.refresh()
        self._refresh_status()
        return True

    def _open_upload_dialog(self) -> None:
        if self.has_unsaved_changes():
            ui.notify(
                "Reset temporary edits before loading another configuration.",
                type="warning",
            )
            return
        self._config_upload.reset()
        self._upload_dialog.open()

    async def _load_uploaded_config(self, event) -> None:
        try:
            if self.has_unsaved_changes():
                ui.notify(
                    "Reset temporary edits before loading another configuration.",
                    type="warning",
                )
                return
            file_name, content = await _read_upload(event)
            if Path(file_name).suffix.lower() != ".json":
                raise ValueError("Please select a .json configuration file.")
            config = self._config_loader.load_uploaded_configuration(content)
            if not self._set_session(config, f"uploaded file {file_name}"):
                return
            self._upload_dialog.close()
            ui.notify(f"Loaded {file_name} as a temporary configuration.", type="positive")
        except (OSError, ValueError, ConfigValidationError, ConfigLoadError) as error:
            self._source_status.set_text(f"Unable to load configuration: {error}")
            ui.notify(str(error), type="negative")
        finally:
            self._config_upload.reset()

    @ui.refreshable_method
    def _configuration_editor(self) -> None:
        if self._session is None:
            ui.label("Load a configuration to make temporary changes.").classes(
                "text-sm text-[#9fb2b8]"
            )
            return

        config = self._session.configuration
        with ui.row().classes("w-full flex-wrap items-center gap-2"):
            ui.button(
                "Reset temporary edits",
                icon="restart_alt",
                on_click=self._reset_temporary_edits,
            ).props("outline")
            panel_names = (
                "Courses",
                "Faculty",
                "Rooms",
                "Labs",
                "Time blocks",
                "Class patterns",
                "Global settings",
            )
            panels = {}
            for panel_name in panel_names:
                ui.button(
                    panel_name,
                    on_click=lambda name=panel_name: self._show_panel(panels, name),
                ).props("outline")

        content = config.config
        time_slots = config.time_slot_config
        panel_style = "configuration-panel w-full gap-4 border-t border-[#29404b] pt-6 mt-4"
        with ui.column().classes(panel_style) as courses_panel:
            courses_gui(
                content.courses,
                on_change=self._apply_temporary_change,
                on_pending_change=self._pending_callback("Courses"),
            )
        with ui.column().classes(panel_style) as faculty_panel:
            faculty_gui(
                content.faculty,
                on_change=self._apply_temporary_change,
                on_pending_change=self._pending_callback("Faculty"),
            )
        with ui.column().classes(panel_style) as rooms_panel:
            rooms_gui(
                content.rooms,
                on_change=self._apply_temporary_change,
                on_pending_change=self._pending_callback("Rooms"),
            )
        with ui.column().classes(panel_style) as labs_panel:
            labs_gui(
                content.labs,
                on_change=self._apply_temporary_change,
                on_pending_change=self._pending_callback("Labs"),
            )
        with ui.column().classes(panel_style) as time_blocks_panel:
            time_blocks_gui(
                time_slots.times,
                on_change=self._apply_temporary_change,
                on_pending_change=self._pending_callback("Time blocks"),
            )
        with ui.column().classes(panel_style) as patterns_panel:
            class_patterns_gui(
                time_slots.classes,
                on_change=self._apply_temporary_change,
                on_pending_change=self._pending_callback("Class patterns"),
            )
        with ui.column().classes(panel_style) as settings_panel:
            self._flush_settings = global_settings_gui(
                config,
                on_change=self._apply_temporary_change,
                on_pending_change=self._mark_global_settings_pending,
                on_applied=self._clear_global_settings_pending,
            )

        panels.update(
            {
                "Courses": courses_panel,
                "Faculty": faculty_panel,
                "Rooms": rooms_panel,
                "Labs": labs_panel,
                "Time blocks": time_blocks_panel,
                "Class patterns": patterns_panel,
                "Global settings": settings_panel,
            }
        )
        self._show_panel(panels, "Courses")

    @staticmethod
    def _show_panel(panels, selected: str) -> None:
        for name, panel in panels.items():
            panel.set_visibility(name == selected)

    def _apply_temporary_change(self, mutation: Callable[[], object]) -> bool:
        if self._what_if_controller is None:
            ui.notify("Load a configuration before editing.", type="negative")
            return False
        accepted, problems = self._what_if_controller.apply_change(mutation)
        if not accepted:
            details = "; ".join(
                f"{problem.area}: {problem.item + ': ' if problem.item else ''}{problem.message}"
                for problem in problems
            )
            ui.notify(f"Change rejected: {details}", type="negative")
            return False
        self._invalidate_results()
        self._refresh_status()
        return True

    def _pending_callback(self, name: str):
        def update_pending(pending: bool) -> None:
            if pending:
                self._pending_forms.add(name)
                self._invalidate_results()
            else:
                self._pending_forms.discard(name)
            self._refresh_status()

        return update_pending

    def _mark_global_settings_pending(self) -> None:
        self._pending_forms.add("Global settings")
        self._invalidate_results()
        self._refresh_status()

    def _clear_global_settings_pending(self) -> None:
        self._pending_forms.discard("Global settings")
        self._refresh_status()

    def _reset_temporary_edits(self) -> None:
        if self._generator.state_snapshot().running:
            ui.notify(
                "Wait for schedule generation to finish before resetting edits.", type="warning"
            )
            return
        if self._session is None:
            return
        self._session.discard()
        self._what_if_controller = ConfigurationController(self._session.configuration)
        self._pending_forms.clear()
        self._invalidate_results()
        self._configuration_editor.refresh()
        self._refresh_status()

    def _invalidate_results(self) -> None:
        if self._generator.state_snapshot().running:
            return
        self._generator.clear_generated_schedules()
        if not hasattr(self, "_result_container"):
            return
        self._result_container.clear()
        self._alternative_select.options = {}
        self._alternative_select.value = None
        self._alternative_select.disable()
        self._alternative_select.update()
        self._generation_status.set_text("")

    def _refresh_status(self) -> None:
        if not hasattr(self, "_draft_status"):
            return
        self._draft_status.set_text(
            "What-If changes will be lost" if self.has_unsaved_changes() else "No What-If changes"
        )

    def _generate(self) -> None:
        if self._session is None:
            ui.notify("Load a configuration first.", type="negative")
            return
        if self._generator.state_snapshot().running:
            ui.notify("Schedule generation is already in progress.", type="warning")
            return
        if "Global settings" in self._pending_forms and not self._flush_settings():
            return
        self._pending_forms.discard("Global settings")
        if self._pending_forms:
            ui.notify(
                "Apply or cancel the open configuration form before generating.",
                type="warning",
            )
            return
        config = self._session.generation_snapshot()
        problems = validate_config(config)
        if problems:
            details = "; ".join(
                f"{problem.area}: {problem.item + ': ' if problem.item else ''}{problem.message}"
                for problem in problems
            )
            self._generation_status.set_text(
                f"Fix configuration issues before generating: {details}"
            )
            ui.notify("The temporary configuration is not valid.", type="negative")
            return

        self._result_container.clear()
        self._alternative_select.options = {}
        self._alternative_select.value = None
        self._alternative_select.disable()
        self._alternative_select.update()
        requested, error = self._generator.start_generation(
            f"What-If: {self._session.name}",
            None,
            None,
            loaded_config=config,
        )
        if error:
            self._generation_status.set_text(error)
            return
        if requested is not None:
            self._generation_status.set_text(
                f"Generating alternative schedules (limit {requested})..."
            )
            self._progress_timer.active = True

    def _update_generation(self) -> None:
        state = self._generator.state_snapshot()
        if not state.finished:
            if state.running and state.message:
                self._generation_status.set_text(state.message)
            return

        self._progress_timer.active = False
        if self._discard_running_result:
            self._discard_running_result = False
            self._generator.clear_generated_schedules()
            self._generation_status.set_text("")
            return
        if state.error:
            self._generation_status.set_text(f"Schedule generation failed: {state.error}")
            return
        results = self._generator.generated_schedules
        if not results:
            self._generation_status.set_text("No valid alternative schedules were generated.")
            return

        self._generation_status.set_text(
            f"Generated {len(results)} alternative schedule(s); {state.valid} passed validation."
        )
        options = {index: f"Alternative schedule {index + 1}" for index in range(len(results))}
        self._alternative_select.options = options
        self._alternative_select.value = 0
        self._alternative_select.enable()
        self._alternative_select.update()
        self._render_comparison()

    def _render_comparison(self) -> None:
        results = self._generator.generated_schedules
        index = self._alternative_select.value
        if not results or index is None or not 0 <= index < len(results):
            return

        alternative_records = records_from_result(results[index])
        original_by_course = {record["course"]: record for record in self._original_records}
        alternative_by_course = {record["course"]: record for record in alternative_records}
        rows = []
        for course in sorted(set(original_by_course) | set(alternative_by_course)):
            original = original_by_course.get(course)
            alternative = alternative_by_course.get(course)
            fields = ("faculty", "room", "lab", "times")
            if not self._original_records:
                change = "Alternative only"
            elif original is None:
                change = "Added"
            elif alternative is None:
                change = "Removed"
            elif any(original.get(field) != alternative.get(field) for field in fields):
                change = "Changed"
            else:
                change = "Unchanged"
            rows.append(
                {
                    "course": course,
                    "change": change,
                    "original_times": original.get("times", "—") if original else "—",
                    "alternative_times": (alternative.get("times", "—") if alternative else "—"),
                    "original_room": original.get("room", "—") if original else "—",
                    "alternative_room": (alternative.get("room", "—") if alternative else "—"),
                    "original_lab": original.get("lab", "—") if original else "—",
                    "alternative_lab": alternative.get("lab", "—") if alternative else "—",
                    "original_faculty": (original.get("faculty", "—") if original else "—"),
                    "alternative_faculty": (
                        alternative.get("faculty", "—") if alternative else "—"
                    ),
                }
            )

        self._result_container.clear()
        with self._result_container:
            if not self._original_records:
                ui.label(
                    "No original schedule is loaded; showing the alternative schedule only."
                ).classes("text-sm").style("color: var(--text-muted)")
            ui.table(
                columns=[
                    {"name": "course", "label": "Course", "field": "course", "align": "left"},
                    {"name": "change", "label": "Change", "field": "change", "align": "left"},
                    {
                        "name": "original_times",
                        "label": "Original time",
                        "field": "original_times",
                        "align": "left",
                    },
                    {
                        "name": "alternative_times",
                        "label": "Alternative time",
                        "field": "alternative_times",
                        "align": "left",
                    },
                    {
                        "name": "original_room",
                        "label": "Original room",
                        "field": "original_room",
                        "align": "left",
                    },
                    {
                        "name": "alternative_room",
                        "label": "Alternative room",
                        "field": "alternative_room",
                        "align": "left",
                    },
                    {
                        "name": "original_lab",
                        "label": "Original lab",
                        "field": "original_lab",
                        "align": "left",
                    },
                    {
                        "name": "alternative_lab",
                        "label": "Alternative lab",
                        "field": "alternative_lab",
                        "align": "left",
                    },
                    {
                        "name": "original_faculty",
                        "label": "Original faculty",
                        "field": "original_faculty",
                        "align": "left",
                    },
                    {
                        "name": "alternative_faculty",
                        "label": "Alternative faculty",
                        "field": "alternative_faculty",
                        "align": "left",
                    },
                ],
                rows=rows,
                row_key="course",
            ).classes("w-full").props("flat bordered dense wrap-cells")


def build_what_if_tab() -> WhatIfTab:
    """Build the What-If Analysis tab."""
    tab = WhatIfTab()
    tab.build()
    return tab
