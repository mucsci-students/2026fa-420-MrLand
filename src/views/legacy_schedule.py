import json
import threading
from typing import Any

from nicegui import ui

from src.models.configuration_model import load_config as config_load, config_exists
from scheduler.scheduler import Scheduler
from src.models.schedule_result import ScheduleResult


# Stores generated schedules so the Schedule Viewer can access them.
generated_schedules: list[ScheduleResult] = []


# ----------------------------------------------------------------------
# Background scheduler state
# ----------------------------------------------------------------------

_scheduler_state: dict[str, Any] = {
    "running": False,
    "finished": False,
    "error": None,
    "config_name": None,
    "requested": 0,
    "generated": 0,
    "valid": 0,
    "message": "",
    "diagnosis": None,
}

_scheduler_lock = threading.Lock()


def _reset_scheduler_state() -> None:
    """Reset the shared scheduler state before a new generation."""

    with _scheduler_lock:
        _scheduler_state["running"] = True
        _scheduler_state["finished"] = False
        _scheduler_state["error"] = None
        _scheduler_state["config_name"] = None
        _scheduler_state["requested"] = 0
        _scheduler_state["generated"] = 0
        _scheduler_state["valid"] = 0
        _scheduler_state["message"] = "Starting scheduler..."
        _scheduler_state["diagnosis"] = None


# ----------------------------------------------------------------------
# Background Scheduler
# ----------------------------------------------------------------------

def _scheduler_worker(
    config_name: str,
    limit_override: int | None,
    optimizer_override: list[str] | None,
) -> None:
    """
    Run the scheduler in a background thread.

    This function must NOT modify NiceGUI UI elements directly.
    """

    try:
        with _scheduler_lock:
            _scheduler_state["config_name"] = config_name
            _scheduler_state["message"] = (
                f"Loading configuration '{config_name}'..."
            )

        # --------------------------------------------------------------
        # Load configuration
        # --------------------------------------------------------------

        full_config = config_load(config_name)

        # --------------------------------------------------------------
        # Apply temporary GUI overrides.
        # --------------------------------------------------------------

        if limit_override is not None:
            full_config.limit = limit_override

        if optimizer_override is not None:
            full_config.optimizer_flags = optimizer_override

        limit = full_config.limit

        with _scheduler_lock:
            _scheduler_state["requested"] = limit
            _scheduler_state["message"] = (
                "Starting Z3 scheduler..."
            )

        # --------------------------------------------------------------
        # Start scheduler
        # --------------------------------------------------------------

        sched = Scheduler(full_config)

        with _scheduler_lock:
            _scheduler_state["message"] = (
                "Generating schedules..."
            )

        generated = []

        # --------------------------------------------------------------
        # Generate schedules
        # --------------------------------------------------------------

        for schedule in sched.get_models():
            generated.append(schedule)

            with _scheduler_lock:
                _scheduler_state["generated"] = len(generated)
                _scheduler_state["message"] = (
                    f"Generated {len(generated)} of {limit} schedules. "
                    "Searching for another schedule..."
                )

            if len(generated) >= limit:
                break

        # --------------------------------------------------------------
        # No schedules
        # --------------------------------------------------------------

        if not generated:
            diagnosis = sched.diagnose()

            with _scheduler_lock:
                _scheduler_state["message"] = (
                    "No valid schedules could be generated."
                )
                _scheduler_state["diagnosis"] = diagnosis
                _scheduler_state["finished"] = True
                _scheduler_state["running"] = False

            return

        # --------------------------------------------------------------
        # Audit schedules
        # --------------------------------------------------------------

        valid_count = sum(
            1
            for schedule in generated
            if sched.audit_schedule(schedule).is_valid
        )

        # --------------------------------------------------------------
        # Store schedules
        # --------------------------------------------------------------

        generated_schedules.extend(
            ScheduleResult(
                config_name=config_name,
                schedule=schedule,
            )
            for schedule in generated
        )

        # --------------------------------------------------------------
        # Finished successfully
        # --------------------------------------------------------------

        with _scheduler_lock:
            _scheduler_state["generated"] = len(generated)
            _scheduler_state["valid"] = valid_count
            _scheduler_state["message"] = (
                f"Generated {len(generated)} of {limit} schedules."
            )
            _scheduler_state["finished"] = True
            _scheduler_state["running"] = False

    except Exception as e:
        with _scheduler_lock:
            _scheduler_state["error"] = str(e)
            _scheduler_state["message"] = (
                "Schedule generation failed."
            )
            _scheduler_state["finished"] = True
            _scheduler_state["running"] = False


# ----------------------------------------------------------------------
# Export Functions
# ----------------------------------------------------------------------

def schedules_to_json(
    schedules: list[ScheduleResult],
) -> bytes:
    """
    Convert all generated schedules into one JSON file.
    """

    schedule_data = []

    for index, result in enumerate(schedules, start=1):
        schedule_data.append({
            "schedule": index,
            "config": result.config_name,
            "meetings": [
                {
                    "course": str(instance.course),
                    "faculty": str(instance.faculty),
                    "room": str(instance.room),
                    "lab": str(instance.lab),
                    "times": str(instance.times),
                }
                for instance in result.schedule
            ],
        })

    return json.dumps(
        schedule_data,
        indent=4,
    ).encode("utf-8")


def schedules_to_csv(
    schedules: list[ScheduleResult],
) -> bytes:
    """
    Convert all generated schedules into one CSV file.
    """

    lines = [
        "schedule,config,course,faculty,room,lab,times"
    ]

    for schedule_number, result in enumerate(
        schedules,
        start=1,
    ):
        for instance in result.schedule:
            row = [
                str(schedule_number),
                result.config_name,
                str(instance.course),
                str(instance.faculty),
                str(instance.room),
                str(instance.lab),
                str(instance.times),
            ]

            # Escape CSV values.
            escaped_row = []

            for value in row:
                value = value.replace('"', '""')

                if any(
                    character in value
                    for character in [",", '"', "\n"]
                ):
                    value = f'"{value}"'

                escaped_row.append(value)

            lines.append(",".join(escaped_row))

    return "\n".join(lines).encode("utf-8")


# ----------------------------------------------------------------------
# Schedule Generator Page
# ----------------------------------------------------------------------

def schedule_generator() -> None:
    """Build the Schedule Generator page."""

    ui.label("Schedule Generator").classes(
        "text-2xl font-semibold text-white"
    )

    ui.label(
        "Generate schedules from a saved configuration."
    ).classes("text-gray-400 mb-6")

    # ------------------------------------------------------------------
    # Configuration
    # ------------------------------------------------------------------

    ui.label("Configuration").classes(
        "text-lg font-semibold text-white"
    )

    config_names = []

    try:
        import os

        config_directory = os.path.join(
            "src",
            "configs",
        )

        if os.path.exists(config_directory):
            for filename in os.listdir(config_directory):
                if filename.endswith(".json"):
                    config_name = filename[:-5]

                    if config_exists(config_name):
                        config_names.append(config_name)

    except Exception:
        config_names = []

    config_select = ui.select(
        options=config_names,
        label="Select Configuration",
    ).classes(
        "w-full max-w-xl"
    ).props(
        "dark outlined"
    )

    # ------------------------------------------------------------------
    # Configured Generation Limit
    # ------------------------------------------------------------------

    ui.label("Generation Limit").classes(
        "text-lg font-semibold text-white mt-4"
    )

    configured_limit = ui.input(
        label="Configured Generation Limit",
        value="",
    ).classes(
        "w-full max-w-xl"
    ).props(
        "dark outlined readonly"
    )

    ui.label(
        "The generation limit saved in the selected configuration."
    ).classes(
        "text-sm text-gray-400"
    )

    # ------------------------------------------------------------------
    # Temporary Generation Limit Override
    # ------------------------------------------------------------------

    generation_limit_override = ui.input(
        label="Temporary Generation Limit Override",
        value="",
        placeholder="Leave blank to use configured limit",
    ).classes(
        "w-full max-w-xl mt-2"
    ).props(
        "dark outlined"
    )

    ui.label(
        "Optional. This only applies to the current generation "
        "and does not change the saved configuration."
    ).classes(
        "text-sm text-gray-400 mb-6"
    )

    # ------------------------------------------------------------------
    # Optimizer Flags
    # ------------------------------------------------------------------

    ui.label("Optimizer Options").classes(
        "text-lg font-semibold text-white"
    )

    ui.label(
        "Configured optimizer options are shown below. "
        "Temporary overrides can be enabled separately."
    ).classes(
        "text-sm text-gray-400 mb-2"
    )

    optimizer_flags = {
        "Faculty Course Preferences": "faculty_course",
        "Faculty Room Preferences": "faculty_room",
        "Faculty Lab Preferences": "faculty_lab",
        "Same Room": "same_room",
        "Same Lab": "same_lab",
        "Pack Rooms": "pack_rooms",
        "Pack Labs": "pack_labs",
    }

    # ------------------------------------------------------------------
    # Configured Optimizer Options
    # ------------------------------------------------------------------

    ui.label(
        "Configured Optimizer Options"
    ).classes(
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

    # ------------------------------------------------------------------
    # Temporary Optimizer Overrides
    # ------------------------------------------------------------------

    optimizer_override_enabled = ui.checkbox(
        "Use temporary optimizer overrides"
    ).props(
        "dark"
    ).classes(
        "text-gray-300 mt-4"
    )

    ui.label(
        "When enabled, the selections below replace the configured "
        "optimizer options for this generation only."
    ).classes(
        "text-sm text-gray-400"
    )

    temporary_optimizer_checkboxes = {}

    with ui.column().classes(
        "gap-1 mt-2 mb-6"
    ):
        for label, value in optimizer_flags.items():
            temporary_optimizer_checkboxes[value] = (
                ui.checkbox(label)
                .props("dark")
                .classes("text-gray-400")
            )

    for checkbox in temporary_optimizer_checkboxes.values():
        checkbox.disable()

    def update_optimizer_override_state() -> None:
        """Enable or disable temporary optimizer controls."""

        if optimizer_override_enabled.value:
            for checkbox in temporary_optimizer_checkboxes.values():
                checkbox.enable()
        else:
            for checkbox in temporary_optimizer_checkboxes.values():
                checkbox.disable()

    optimizer_override_enabled.on_value_change(
        update_optimizer_override_state
    )

    # ------------------------------------------------------------------
    # Load Configuration Settings
    # ------------------------------------------------------------------

    def load_selected_config() -> None:
        """Load the selected configuration into the GUI."""

        config_name = config_select.value

        if not config_name:
            configured_limit.value = ""

            for checkbox in configured_optimizer_checkboxes.values():
                checkbox.value = False

            generation_limit_override.value = ""

            optimizer_override_enabled.value = False

            for checkbox in temporary_optimizer_checkboxes.values():
                checkbox.value = False

            update_optimizer_override_state()

            return

        try:
            config = config_load(config_name)

            # Show configured generation limit.
            configured_limit.value = str(config.limit)

            # Show configured optimizer options.
            configured_flags = set(
                config.optimizer_flags
            )

            for value, checkbox in (
                configured_optimizer_checkboxes.items()
            ):
                checkbox.value = (
                    value in configured_flags
                )

            # Clear temporary overrides when configuration changes.
            generation_limit_override.value = ""

            optimizer_override_enabled.value = False

            for checkbox in temporary_optimizer_checkboxes.values():
                checkbox.value = False

            update_optimizer_override_state()

        except Exception:
            configured_limit.value = ""

            for checkbox in configured_optimizer_checkboxes.values():
                checkbox.value = False

            generation_limit_override.value = ""

            optimizer_override_enabled.value = False

            for checkbox in temporary_optimizer_checkboxes.values():
                checkbox.value = False

            update_optimizer_override_state()

    config_select.on_value_change(
        load_selected_config
    )

    # ------------------------------------------------------------------
    # Progress Area
    # ------------------------------------------------------------------

    progress_container = ui.column().classes(
        "w-full max-w-2xl gap-2 mt-6"
    )

    progress_container.visible = False

    with progress_container:
        progress_label = ui.label(
            "Starting scheduler..."
        ).classes(
            "text-sm text-gray-300"
        )

        progress = ui.linear_progress(
            value=0
        ).classes(
            "w-full"
        )

        progress_percentage = ui.label(
            "0%"
        ).classes(
            "text-sm text-gray-300"
        )

        progress_status = ui.label(
            "Generated 0 of 0 schedules"
        ).classes(
            "text-sm text-gray-400"
        )

        with ui.row().classes(
            "items-center gap-2"
        ):
            spinner = ui.spinner(
                size="24px"
            )

            spinner_label = ui.label(
                "Z3 is searching for schedules..."
            ).classes(
                "text-sm text-gray-400"
            )

    # ------------------------------------------------------------------
    # Result Area
    # ------------------------------------------------------------------

    result_container = ui.column().classes(
        "w-full max-w-2xl mt-6"
    )

    # ------------------------------------------------------------------
    # Poll Background Scheduler
    # ------------------------------------------------------------------

    def update_progress() -> None:
        """Update the UI using the background scheduler state."""

        with _scheduler_lock:
            running = _scheduler_state["running"]
            finished = _scheduler_state["finished"]
            error = _scheduler_state["error"]
            requested = _scheduler_state["requested"]
            generated = _scheduler_state["generated"]
            valid = _scheduler_state["valid"]
            message = _scheduler_state["message"]
            diagnosis = _scheduler_state["diagnosis"]

        # Nothing is currently running.
        if not running and not finished:
            return

        # --------------------------------------------------------------
        # Update progress
        # --------------------------------------------------------------

        percentage = 0

        if requested > 0:
            percentage = min(
                (generated / requested) * 100,
                100,
            )

        progress.value = percentage / 100
        progress_percentage.text = (
            f"{percentage:.0f}%"
        )

        progress_label.text = message

        if requested > 0:
            progress_status.text = (
                f"Generated {generated} of "
                f"{requested} schedules"
            )

        # --------------------------------------------------------------
        # Still running
        # --------------------------------------------------------------

        if running:
            progress_container.visible = True
            spinner.visible = True

            spinner_label.text = (
                "Z3 is searching for schedules..."
            )

            return

        # --------------------------------------------------------------
        # Finished
        # --------------------------------------------------------------

        spinner.visible = False

        if not finished:
            return

        # --------------------------------------------------------------
        # Error
        # --------------------------------------------------------------

        if error:
            progress_label.text = (
                "Schedule generation failed."
            )

            with result_container:
                ui.label(
                    "An error occurred while generating "
                    f"schedules: {error}"
                ).classes(
                    "text-red-400"
                )

            return

        # --------------------------------------------------------------
        # No schedules
        # --------------------------------------------------------------

        if generated == 0:
            progress.value = 0
            progress_percentage.text = "0%"

            progress_label.text = (
                "No valid schedules could be generated."
            )

            if diagnosis is not None:
                with result_container:
                    ui.label(
                        "No valid schedule could be generated "
                        "for this configuration."
                    ).classes(
                        "text-red-400 text-lg"
                    )

                    ui.label(
                        f"Status: {diagnosis.status}"
                    ).classes(
                        "text-gray-300"
                    )

                    if diagnosis.conflicting_constraints:
                        ui.label(
                            "Conflicting Constraints"
                        ).classes(
                            "text-md font-semibold "
                            "text-white mt-4"
                        )

                        for finding in (
                            diagnosis.conflicting_constraints
                        ):
                            ui.label(
                                f"• {finding.message}"
                            ).classes(
                                "text-gray-400"
                            )

                    if diagnosis.relaxation_suggestions:
                        ui.label(
                            "Suggestions"
                        ).classes(
                            "text-md font-semibold "
                            "text-white mt-4"
                        )

                        for suggestion in (
                            diagnosis.relaxation_suggestions
                        ):
                            ui.label(
                                f"• {suggestion.message}"
                            ).classes(
                                "text-gray-400"
                            )

            return

        # --------------------------------------------------------------
        # Successful generation
        # --------------------------------------------------------------

        progress.value = 1
        progress_percentage.text = "100%"

        progress_label.text = (
            "Schedule generation complete."
        )

        progress_status.text = (
            f"Generated {generated} of "
            f"{requested} requested schedules"
        )

        with result_container:
            ui.label(
                "Scheduler ran successfully."
            ).classes(
                "text-green-400 text-lg font-semibold"
            )

            ui.label(
                f"Generated {generated} schedule(s)."
            ).classes(
                "text-gray-300"
            )

            ui.label(
                f"Valid schedules: {valid}"
            ).classes(
                "text-gray-300"
            )

            ui.label(
                "View the generated schedules in the "
                "Schedule Viewer tab."
            ).classes(
                "text-gray-400 mt-2"
            )

        # Stop polling once finished.
        progress_timer.cancel()

    # Check the worker about five times per second.
    progress_timer = ui.timer(
        0.2,
        update_progress,
        active=False,
    )

    # ------------------------------------------------------------------
    # Generate Button
    # ------------------------------------------------------------------

    def generate_schedules() -> None:
        """Start schedule generation in a background thread."""

        # Don't allow another generation while one is running.
        with _scheduler_lock:
            if _scheduler_state["running"]:
                return

        result_container.clear()

        # --------------------------------------------------------------
        # Validate configuration
        # --------------------------------------------------------------

        config_name = config_select.value

        if not config_name:
            with result_container:
                ui.label(
                    "Please select a configuration."
                ).classes(
                    "text-red-400"
                )

            return

        # --------------------------------------------------------------
        # Validate temporary generation limit override
        # --------------------------------------------------------------

        limit_override = None

        override_value = (
            generation_limit_override.value
        )

        if (
            override_value is not None
            and str(override_value).strip()
        ):
            try:
                limit_override = int(
                    override_value
                )

                if limit_override <= 0:
                    raise ValueError

            except (TypeError, ValueError):
                with result_container:
                    ui.label(
                        "Temporary generation limit must be "
                        "a positive whole number."
                    ).classes(
                        "text-red-400"
                    )

                return

        # --------------------------------------------------------------
        # Get temporary optimizer override
        # --------------------------------------------------------------

        optimizer_override = None

        if optimizer_override_enabled.value:
            optimizer_override = [
                value
                for value, checkbox
                in temporary_optimizer_checkboxes.items()
                if checkbox.value
            ]

        # --------------------------------------------------------------
        # Reset state
        # --------------------------------------------------------------

        generated_schedules.clear()

        _reset_scheduler_state()

        # --------------------------------------------------------------
        # Determine actual generation limit.
        # --------------------------------------------------------------

        try:
            config = config_load(
                config_name
            )

            if limit_override is not None:
                requested_limit = limit_override
            else:
                requested_limit = config.limit

        except Exception as e:
            with result_container:
                ui.label(
                    f"Could not load configuration: {e}"
                ).classes(
                    "text-red-400"
                )

            with _scheduler_lock:
                _scheduler_state["running"] = False
                _scheduler_state["finished"] = True

            return

        with _scheduler_lock:
            _scheduler_state["config_name"] = (
                config_name
            )

            _scheduler_state["requested"] = (
                requested_limit
            )

        # --------------------------------------------------------------
        # Reset UI
        # --------------------------------------------------------------

        progress_container.visible = True

        progress.value = 0
        progress_percentage.text = "0%"

        if limit_override is not None:
            progress_label.text = (
                f"Starting scheduler for "
                f"'{config_name}' with temporary "
                f"limit override of "
                f"{limit_override}..."
            )
        else:
            progress_label.text = (
                f"Starting scheduler for "
                f"'{config_name}' using configured "
                f"limit of {requested_limit}..."
            )

        progress_status.text = (
            f"Generated 0 of "
            f"{requested_limit} schedules"
        )

        spinner.visible = True

        spinner_label.text = (
            "Z3 is searching for schedules..."
        )

        # --------------------------------------------------------------
        # Start background thread
        # --------------------------------------------------------------

        worker = threading.Thread(
            target=_scheduler_worker,
            args=(
                config_name,
                limit_override,
                optimizer_override,
            ),
            daemon=True,
        )

        worker.start()

        # Start polling the worker.
        progress_timer.active = True

    # ------------------------------------------------------------------
    # Generate Button
    # ------------------------------------------------------------------

    ui.button(
        "Generate Schedules",
        icon="auto_awesome",
        on_click=generate_schedules,
    ).props(
        "color=primary"
    ).classes(
        "mt-2"
    )