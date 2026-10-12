"""NiceGUI page for generating and downloading schedules.

Used by: GUI."""

from nicegui import ui

from src.controllers.schedule_generator_controller import (
    schedule_generator_controller as controller,
)
from src.models.schedule_generator_model import ScheduleGenerationState
from src.models.configuration_repository import ConfigLoadError


def schedule_generator() -> None:
    """Build the Schedule Generator page."""
    ui.label("Schedule Generator").classes(
        "text-2xl font-semibold text-white"
    )
    ui.label(
        "Generate schedules from a saved configuration."
    ).classes("text-gray-400 mb-6")

    ui.label("Configuration").classes(
        "text-lg font-semibold text-white"
    )
    config_select = ui.select(
        options=controller.list_config_names(),
        label="Select Configuration",
    ).classes("w-full max-w-xl").props("dark outlined")
    config_load_error = ui.label("").classes("text-red-400")
    config_load_error.visible = False
    config_select.on(
        "popup-show",
        lambda: config_select.set_options(
            controller.list_config_names(), value=config_select.value
        ),
    )

    ui.label("Generation Limit").classes(
        "text-lg font-semibold text-white mt-4"
    )
    configured_limit = ui.input(
        label="Configured Generation Limit",
        value="",
    ).classes("w-full max-w-xl").props("dark outlined readonly")
    ui.label(
        "The generation limit saved in the selected configuration."
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

    def reset_config_controls() -> None:
        config_load_error.text = ""
        config_load_error.visible = False
        configured_limit.value = ""
        for checkbox in configured_optimizer_checkboxes.values():
            checkbox.value = False
        generation_limit_override.value = ""
        optimizer_override_enabled.value = False
        for checkbox in temporary_optimizer_checkboxes.values():
            checkbox.value = False
        update_optimizer_override_state()

    def load_selected_config() -> None:
        config_name = config_select.value
        if not config_name:
            reset_config_controls()
            return

        try:
            config = controller.load_config(config_name)
        except (OSError, ValueError, ConfigLoadError) as error:
            reset_config_controls()
            config_load_error.text = f"Could not load configuration: {error}"
            config_load_error.visible = True
            return

        configured_limit.value = str(config.limit)
        configured_flags = {flag.value for flag in config.optimizer_flags}
        for value, checkbox in configured_optimizer_checkboxes.items():
            checkbox.value = value in configured_flags

        config_load_error.text = ""
        config_load_error.visible = False
        generation_limit_override.value = ""
        optimizer_override_enabled.value = False
        for checkbox in temporary_optimizer_checkboxes.values():
            checkbox.value = False
        update_optimizer_override_state()

    config_select.on_value_change(load_selected_config)

    progress_container = ui.column().classes(
        "w-full max-w-2xl gap-2 mt-6"
    )
    progress_container.visible = False
    with progress_container:
        progress_label = ui.label("Starting scheduler...").classes(
            "text-sm text-gray-300"
        )
        progress = ui.linear_progress(value=0).classes("w-full")
        progress_percentage = ui.label("0%").classes(
            "text-sm text-gray-300"
        )
        progress_status = ui.label(
            "Generated 0 of 0 schedules"
        ).classes("text-sm text-gray-400")
        with ui.row().classes("items-center gap-2"):
            spinner = ui.spinner(size="24px")
            spinner_label = ui.label(
                "Z3 is searching for schedules..."
            ).classes("text-sm text-gray-400")

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

        percentage = 0
        if state.requested > 0:
            percentage = min(
                state.generated / state.requested * 100,
                100,
            )
        progress.value = percentage / 100
        progress_percentage.text = f"{percentage:.0f}%"
        progress_label.text = state.message
        if state.requested > 0:
            progress_status.text = (
                f"Generated {state.generated} of "
                f"{state.requested} schedules"
            )

        if state.running:
            progress_container.visible = True
            spinner.visible = True
            spinner_label.text = "Z3 is searching for schedules..."
            return

        spinner.visible = False
        if not state.finished or completion_rendered:
            return
        completion_rendered = True
        progress_timer.cancel()

        if state.error:
            progress_label.text = "Schedule generation failed."
            with result_container:
                ui.label(
                    "An error occurred while generating "
                    f"schedules: {state.error}"
                ).classes("text-red-400")
            return

        if state.generated == 0:
            progress.value = 0
            progress_percentage.text = "0%"
            progress_label.text = "No valid schedules could be generated."
            if state.diagnosis is not None:
                render_diagnosis(state.diagnosis)
            return

        progress.value = 1
        progress_percentage.text = "100%"
        progress_label.text = "Schedule generation complete."
        progress_status.text = (
            f"Generated {state.generated} of "
            f"{state.requested} requested schedules"
        )
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
            ui.label(
                "View the generated schedules in the "
                "Schedule Viewer tab."
            ).classes("text-gray-400 mt-2")
    progress_timer = ui.timer(
        0.2,
        update_progress,
        active=False,
    )

    def generate_schedules() -> None:
        nonlocal completion_rendered
        if controller.state_snapshot().running:
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
            config_select.value,
            generation_limit_override.value,
            optimizer_override,
        )
        if error:
            with result_container:
                ui.label(error).classes("text-red-400")
            return
        if requested is None:
            return

        progress_container.visible = True
        progress.value = 0
        progress_percentage.text = "0%"
        if generation_limit_override.value is not None and str(
            generation_limit_override.value
        ).strip():
            progress_label.text = (
                f"Starting scheduler for '{config_select.value}' with "
                f"temporary limit override of {requested}..."
            )
        else:
            progress_label.text = (
                f"Starting scheduler for '{config_select.value}' using "
                f"configured limit of {requested}..."
            )
        progress_status.text = f"Generated 0 of {requested} schedules"
        spinner.visible = True
        spinner_label.text = "Z3 is searching for schedules..."
        progress_timer.active = True

    ui.button(
        "Generate Schedules",
        icon="auto_awesome",
        on_click=generate_schedules,
    ).props("color=primary").classes("mt-2")
