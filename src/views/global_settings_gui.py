"""NiceGUI controls for global scheduler settings.

Used by: GUI."""

from collections.abc import Callable

from nicegui import ui
from scheduler.config import CombinedConfig, OptimizerFlags

from src.controllers.settings_controller import SettingsController
from src.models.quality_grading import QualityGradeSettings
from src.views.common import ConfigurationChangeHandler, run_configuration_change

controller = SettingsController()


def global_settings_gui(
    combined_config: CombinedConfig,
    on_change: ConfigurationChangeHandler | None = None,
    on_pending_change: Callable[[], None] | None = None,
    on_applied: Callable[[], None] | None = None,
    quality_grade_settings: QualityGradeSettings | None = None,
    on_quality_settings_change: Callable[[QualityGradeSettings], None] | None = None,
) -> Callable[[], bool]:
    """Build controls for generation settings and per-config quality grade targets."""
    ui.label("Global settings").classes("text-xl font-semibold text-white")
    ui.label("Configure schedule generation behavior.").classes("text-sm text-[#9fb2b8]")

    generation_limit = ui.number(
        "Generation limit", value=combined_config.limit, min=1, step=1
    ).classes("w-56")
    optimizer_flags = (
        ui.select(
            [flag.value for flag in OptimizerFlags],
            value=[flag.value for flag in combined_config.optimizer_flags],
            multiple=True,
            label="Optimizer flags",
        )
        .props("use-chips clearable")
        .classes("w-full max-w-2xl")
    )
    if quality_grade_settings is not None:
        with ui.expansion("Quality grade targets", icon="grade").classes("w-full"):
            ui.label(
                "Targets define an A. Lower-is-better grades use 1.25×, 1.5×, and 2× "
                "target limits for B, C, and D; utilization grades use 85%, 70%, and "
                "50% of target minimums."
            ).classes("text-sm text-[#9fb2b8]")
            faculty_gap_target = ui.number(
                "Max weekly faculty gap for A (minutes)",
                value=quality_grade_settings.max_faculty_gap_minutes,
                min=0,
                step=30,
            ).classes("w-72")
            room_utilization_target = ui.number(
                "Min room utilization for A (%)",
                value=quality_grade_settings.min_room_utilization_percent,
                min=0,
                max=100,
                step=5,
            ).classes("w-72")
            lab_utilization_target = ui.number(
                "Min lab utilization for A (%)",
                value=quality_grade_settings.min_lab_utilization_percent,
                min=0,
                max=100,
                step=5,
            ).classes("w-72")
            faculty_balance_target = ui.number(
                "Max faculty workload standard deviation for A (hours)",
                value=quality_grade_settings.max_faculty_workload_stddev_hours,
                min=0,
                step=0.25,
            ).classes("w-72")
            weekday_balance_target = ui.number(
                "Max weekday teaching-hours standard deviation for A (hours)",
                value=quality_grade_settings.max_weekday_teaching_hours_stddev,
                min=0,
                step=0.25,
            ).classes("w-72")
    current_settings = ui.label().classes("text-sm text-[#9fb2b8]")
    pending_settings = False

    # Keep the summary synchronized with the current configuration values.
    def refresh_summary() -> None:
        active_flags = ", ".join(flag.value for flag in combined_config.optimizer_flags) or "None"
        current_settings.set_text(
            f"Current settings: generation limit {combined_config.limit}; "
            f"optimizer flags {active_flags}"
        )

    # Validate the form and apply pending settings to the current draft.
    def apply_settings(*, notify: bool) -> bool:
        nonlocal pending_settings
        value = generation_limit.value
        if value is None or not float(value).is_integer():
            ui.notify("Generation limit must be a whole number.", type="negative")
            return False
        updated_quality_settings = None
        try:
            if quality_grade_settings is not None:
                gap_value = faculty_gap_target.value
                if gap_value is None or not float(gap_value).is_integer():
                    ui.notify(
                        "Maximum faculty gap must be a whole number of minutes.",
                        type="negative",
                    )
                    return False
                if any(
                    field.value is None
                    for field in (
                        room_utilization_target,
                        lab_utilization_target,
                        faculty_balance_target,
                        weekday_balance_target,
                    )
                ):
                    ui.notify("Enter a value for every quality grade target.", type="negative")
                    return False
                updated_quality_settings = QualityGradeSettings(
                    max_faculty_gap_minutes=int(gap_value),
                    min_room_utilization_percent=float(room_utilization_target.value),
                    min_lab_utilization_percent=float(lab_utilization_target.value),
                    max_faculty_workload_stddev_hours=float(faculty_balance_target.value),
                    max_weekday_teaching_hours_stddev=float(weekday_balance_target.value),
                )
            if not run_configuration_change(
                on_change,
                lambda: controller.update_settings(
                    combined_config,
                    int(value),
                    optimizer_flags.value or [],
                ),
            ):
                return False
            if (
                updated_quality_settings is not None
                and on_quality_settings_change is not None
            ):
                on_quality_settings_change(updated_quality_settings)
        except (TypeError, ValueError) as exc:
            ui.notify(str(exc), type="negative")
            return False
        except OSError as exc:
            ui.notify(f"Unable to save quality grade targets: {exc}", type="negative")
            return False
        pending_settings = False
        if on_applied is not None:
            on_applied()
        refresh_summary()
        if notify:
            ui.notify("Global settings saved to the current draft.", type="positive")
        return True

    def settings_changed() -> None:
        nonlocal pending_settings
        pending_settings = True
        if on_pending_change is not None:
            on_pending_change()

    generation_limit.on_value_change(lambda _: settings_changed())
    optimizer_flags.on_value_change(lambda _: settings_changed())
    if quality_grade_settings is not None:
        for field in (
            faculty_gap_target,
            room_utilization_target,
            lab_utilization_target,
            faculty_balance_target,
            weekday_balance_target,
        ):
            field.on_value_change(lambda _: settings_changed())

    def save_settings() -> None:
        apply_settings(notify=True)

    def flush_pending_settings() -> bool:
        if not pending_settings:
            return True
        return apply_settings(notify=False)

    # Restore the controller's default settings in both data and form controls.
    def reset_to_defaults() -> None:
        nonlocal pending_settings
        if not run_configuration_change(
            on_change, lambda: controller.reset_settings(combined_config)
        ):
            return
        generation_limit.value = combined_config.limit
        optimizer_flags.value = [flag.value for flag in combined_config.optimizer_flags]
        if quality_grade_settings is not None:
            defaults = QualityGradeSettings()
            faculty_gap_target.value = defaults.max_faculty_gap_minutes
            room_utilization_target.value = defaults.min_room_utilization_percent
            lab_utilization_target.value = defaults.min_lab_utilization_percent
            faculty_balance_target.value = defaults.max_faculty_workload_stddev_hours
            weekday_balance_target.value = defaults.max_weekday_teaching_hours_stddev
            if on_quality_settings_change is not None:
                try:
                    on_quality_settings_change(defaults)
                except OSError as exc:
                    ui.notify(
                        f"Unable to reset quality grade targets: {exc}",
                        type="negative",
                    )
                    return
        pending_settings = False
        if on_applied is not None:
            on_applied()
        refresh_summary()
        ui.notify("Global settings reset to defaults.", type="positive")

    with ui.row().classes("w-full flex-wrap items-center gap-2"):
        ui.button("Save settings", icon="save", on_click=save_settings).props("unelevated").classes(
            "bg-[#75e6da] text-[#101820]"
        )
        ui.button("Reset defaults", icon="restart_alt", on_click=reset_to_defaults).props(
            "outline"
        ).classes("border-[#45616b] text-[#d8e7e8]")

    refresh_summary()
    return flush_pending_settings
