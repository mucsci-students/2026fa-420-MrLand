"""NiceGUI page for generating and downloading schedules.

Used by: GUI."""

from pathlib import Path

from nicegui import ui

from src.controllers.configuration_controller import ConfigurationController
from src.controllers.schedule_generator_controller import (
    schedule_generator_controller as controller,
)
from src.models.configuration_model import ConfigValidationError
from src.models.configuration_repository import ConfigLoadError
from src.models.schedule_generator_model import ScheduleGenerationState
from src.views.configuration_editor import controller as editor_controller
from src.views.schedule_generation_progress import ScheduleGenerationProgress


async def read_upload(event) -> tuple[str, bytes]:
    if hasattr(event, "file"):
        return event.file.name, await event.file.read()
    return event.name, event.content.read()


def schedule_generator() -> None:
    """Build the Schedule Generator page."""
    ui.label("Schedule Generator").classes(
        "text-2xl font-semibold text-white"
    )
    ui.label(
        "Generate schedules from a configuration file."
    ).classes("text-gray-400 mb-6")

    ui.label("Configuration").classes(
        "text-lg font-semibold text-white"
    )
    config_load_error = ui.label("").classes("text-red-400")
    config_load_error.visible = False
    config_name_label = ui.label("No configuration loaded.").classes(
        "text-sm text-gray-400"
    )
    config_loader = ConfigurationController()
    selected_config = {"name": None, "config": None}

    async def handle_config_upload(event) -> None:
        try:
            file_name, content = await read_upload(event)
            if not file_name.lower().endswith(".json"):
                ui.notify("Please select a .json file.", type="negative")
                return

            config = config_loader.load_uploaded_configuration(content)
            config_name = Path(file_name).stem
            selected_config["name"] = config_name
            selected_config["config"] = config
            show_config(config, f"Loaded: {config_name}")
            config_load_error.text = ""
            config_load_error.visible = False
            load_dialog.close()
            ui.notify(f"Loaded '{file_name}'.", type="positive")
        except ConfigValidationError as error:
            problems = "; ".join(
                f"{problem.area}: {problem.message}"
                for problem in error.problems
            )
            config_load_error.text = f"Invalid configuration file: {problems}"
            config_load_error.visible = True
        except (OSError, ValueError, ConfigLoadError) as error:
            config_load_error.text = f"Unable to load configuration: {error}"
            config_load_error.visible = True
        finally:
            config_upload.reset()

    with ui.dialog() as load_dialog:
        with ui.card().classes("w-[480px] max-w-full gap-4"):
            ui.label("Load Configuration").classes(
                "text-lg font-semibold text-white"
            )
            ui.label(
                "Select a JSON configuration file from your computer."
            ).classes("text-sm text-gray-400")
            config_upload = ui.upload(
                label="Choose configuration file",
                auto_upload=True,
                on_upload=handle_config_upload,
                max_files=1,
            ).props("accept=.json flat bordered").classes("w-full")
            with ui.row().classes("w-full justify-end"):
                ui.button("Cancel", on_click=load_dialog.close).props("flat")

    load_button = ui.button(
        "Load configuration",
        icon="folder_open",
        on_click=load_dialog.open,
    ).props("outline").classes("mb-2")
    use_current_config = ui.checkbox(
        "Use current loaded configuration"
    ).props("dark").classes("text-gray-300")
    use_current_config.disable()

    ui.label("Generation Limit").classes(
        "text-lg font-semibold text-white mt-4"
    )
    configured_limit = ui.input(
        label="Configured Generation Limit",
        value="",
    ).classes("w-full max-w-xl").props("dark outlined readonly")
    ui.label(
        "The generation limit saved in the loaded configuration."
    ).classes("text-sm text-gray-400")
    generation_limit_override = ui.input(
        label="Temporary Generation Limit Override",
        value="",
        placeholder="Leave blank to use configured limit",
    ).classes("w-full max-w-xl mt-2").props("dark outlined")
    ui.label(
        "Optional. This only applies to the current generation "
        "and does not change the saved configuration."
    ).classes("text-sm text-gray-400 mb-6")

    ui.label("Time Slot Settings").classes(
        "text-lg font-semibold text-white mt-4"
    )
    configured_max_time_gap = ui.input(
        label="Configured Maximum Time Gap (minutes)",
        value="",
    ).classes("w-full max-w-xl").props("dark outlined readonly")
    configured_min_time_overlap = ui.input(
        label="Configured Minimum Time Overlap (minutes)",
        value="",
    ).classes("w-full max-w-xl").props("dark outlined readonly")
    ui.label(
        "The time-slot settings saved in the loaded configuration."
    ).classes("text-sm text-gray-400")

    max_time_gap_override = ui.input(
        label="Temporary Maximum Time Gap Override (minutes)",
        value="",
        placeholder="Leave blank to use configured value",
    ).classes("w-full max-w-xl mt-2").props("dark outlined")
    min_time_overlap_override = ui.input(
        label="Temporary Minimum Time Overlap Override (minutes)",
        value="",
        placeholder="Leave blank to use configured value",
    ).classes("w-full max-w-xl").props("dark outlined")
    ui.label(
        "Optional. These apply only to the current generation and do not "
        "change the saved configuration."
    ).classes("text-sm text-gray-400 mb-6")

    ui.label("Optimizer Options").classes(
        "text-lg font-semibold text-white"
    )
    ui.label(
        "Configured optimizer options are shown below. "
        "Temporary overrides can be enabled separately."
    ).classes("text-sm text-gray-400 mb-2")
    optimizer_flags = {
        "Faculty Course Preferences": "faculty_course",
        "Faculty Room Preferences": "faculty_room",
        "Faculty Lab Preferences": "faculty_lab",
        "Same Room": "same_room",
        "Same Lab": "same_lab",
        "Pack Rooms": "pack_rooms",
        "Pack Labs": "pack_labs",
    }

    ui.label("Configured Optimizer Options").classes(
        "text-md font-semibold text-white mt-2"
    )
    configured_optimizer_checkboxes = {}
    with ui.column().classes("gap-1"):
        for label, value in optimizer_flags.items():
            configured_optimizer_checkboxes[value] = (
                ui.checkbox(label)
                .props("dark disable")
                .classes("text-gray-400")
            )

    optimizer_override_enabled = ui.checkbox(
        "Use temporary optimizer overrides"
    ).props("dark").classes("text-gray-300 mt-4")
    ui.label(
        "When enabled, the selections below replace the configured "
        "optimizer options for this generation only."
    ).classes("text-sm text-gray-400")

    temporary_optimizer_checkboxes = {}
    with ui.column().classes("gap-1 mt-2 mb-6"):
        for label, value in optimizer_flags.items():
            temporary_optimizer_checkboxes[value] = (
                ui.checkbox(label)
                .props("dark")
                .classes("text-gray-400")
            )
    for checkbox in temporary_optimizer_checkboxes.values():
        checkbox.disable()

    def update_optimizer_override_state() -> None:
        for checkbox in temporary_optimizer_checkboxes.values():
            if optimizer_override_enabled.value:
                checkbox.enable()
            else:
                checkbox.disable()

    optimizer_override_enabled.on_value_change(
        update_optimizer_override_state
    )

    def display_config(config, label: str) -> None:
        config_name_label.text = label
        configured_limit.value = str(config.limit)
        configured_max_time_gap.value = str(
            config.time_slot_config.max_time_gap
        )
        configured_min_time_overlap.value = str(
            config.time_slot_config.min_time_overlap
        )
        configured_flags = {flag.value for flag in config.optimizer_flags}
        for value, checkbox in configured_optimizer_checkboxes.items():
            checkbox.value = value in configured_flags

    def show_config(config, label: str) -> None:
        display_config(config, label)
        generation_limit_override.value = ""
        max_time_gap_override.value = ""
        min_time_overlap_override.value = ""
        optimizer_override_enabled.value = False
        for checkbox in temporary_optimizer_checkboxes.values():
            checkbox.value = False
        update_optimizer_override_state()

    def handle_current_config_selection() -> None:
        current_config = editor_controller.configuration
        if use_current_config.value and current_config is not None:
            load_button.disable()
            show_config(
                current_config, "Using current loaded configuration"
            )
        else:
            load_button.enable()
            if selected_config["config"] is not None:
                show_config(
                    selected_config["config"],
                    f"Loaded: {selected_config['name']}",
                )
            else:
                config_name_label.text = "No configuration loaded."
                configured_limit.value = ""
                configured_max_time_gap.value = ""
                configured_min_time_overlap.value = ""
                for checkbox in configured_optimizer_checkboxes.values():
                    checkbox.value = False

    def sync_current_config_availability() -> None:
        if editor_controller.configuration is None:
            was_selected = use_current_config.value
            use_current_config.value = False
            use_current_config.disable()
            load_button.enable()
            if was_selected:
                handle_current_config_selection()
        else:
            use_current_config.enable()
            if use_current_config.value:
                load_button.disable()

    use_current_config.on_value_change(
        lambda _: handle_current_config_selection()
    )
    sync_current_config_availability()
    ui.timer(1.0, sync_current_config_availability)

    progress_display = ScheduleGenerationProgress(
        "w-full max-w-2xl gap-2 mt-6"
    )

    result_container = ui.column().classes(
        "w-full max-w-2xl mt-6"
    )
    completion_rendered = False

    def render_diagnosis(diagnosis) -> None:
        with result_container:
            ui.label(
                "No valid schedule could be generated "
                "for this configuration."
            ).classes("text-red-400 text-lg")
            ui.label(f"Status: {diagnosis.status}").classes(
                "text-gray-300"
            )
            if diagnosis.conflicting_constraints:
                ui.label("Conflicting Constraints").classes(
                    "text-md font-semibold text-white mt-4"
                )
                for finding in diagnosis.conflicting_constraints:
                    ui.label(f"• {finding.message}").classes(
                        "text-gray-400"
                    )
            if diagnosis.relaxation_suggestions:
                ui.label("Suggestions").classes(
                    "text-md font-semibold text-white mt-4"
                )
                for suggestion in diagnosis.relaxation_suggestions:
                    ui.label(f"• {suggestion.message}").classes(
                        "text-gray-400"
                    )

    def update_progress() -> None:
        nonlocal completion_rendered
        state: ScheduleGenerationState = controller.state_snapshot()
        if not state.running and not state.finished:
            return

        progress_result = progress_display.update(state)
        if progress_result == "running":
            return

        if not state.finished or completion_rendered:
            return
        completion_rendered = True
        progress_timer.cancel()

        if state.error:
            with result_container:
                ui.label(
                    "An error occurred while generating "
                    f"schedules: {state.error}"
                ).classes("text-red-400")
            return

        if state.generated == 0:
            if state.diagnosis is not None:
                render_diagnosis(state.diagnosis)
            return

        with result_container:
            ui.label("Scheduler ran successfully.").classes(
                "text-green-400 text-lg font-semibold"
            )
            ui.label(f"Generated {state.generated} schedule(s).").classes(
                "text-gray-300"
            )
            ui.label(f"Valid schedules: {state.valid}").classes(
                "text-gray-300"
            )
    progress_timer = ui.timer(
        0.2,
        update_progress,
        active=False,
    )

    def generate_schedules() -> None:
        nonlocal completion_rendered
        if controller.state_snapshot().running:
            ui.label(
                "Generation is already in progress. Please wait for it to finish."
            ).classes("text-red-400")
            return
        result_container.clear()
        completion_rendered = False

        optimizer_override = None
        if optimizer_override_enabled.value:
            optimizer_override = [
                value
                for value, checkbox in temporary_optimizer_checkboxes.items()
                if checkbox.value
            ]

        requested, error = controller.start_generation(
            (
                "current configuration"
                if use_current_config.value
                else selected_config["name"]
            ),
            generation_limit_override.value,
            optimizer_override,
            max_time_gap_override.value,
            min_time_overlap_override.value,
            (
                editor_controller.configuration
                if use_current_config.value
                else selected_config["config"]
            ),
        )
        if error:
            with result_container:
                ui.label(error).classes("text-red-400")
            return
        if requested is None:
            return

        if generation_limit_override.value is not None and str(
            generation_limit_override.value
        ).strip():
            starting_message = (
                f"Starting scheduler for '{selected_config['name']}' with "
                f"temporary limit override of {requested}..."
            )
        else:
            starting_message = (
                f"Starting scheduler for '{selected_config['name']}' using "
                f"configured limit of {requested}..."
            )
        progress_display.start(requested, starting_message)
        progress_timer.active = True

    ui.button(
        "Generate Schedules",
        icon="auto_awesome",
        on_click=generate_schedules,
    ).props("color=primary").classes("mt-2")
