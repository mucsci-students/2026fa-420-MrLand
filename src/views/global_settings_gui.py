"""NiceGUI controls for global scheduler settings.

Used by: GUI."""

from collections.abc import Callable

from nicegui import ui
from scheduler.config import CombinedConfig, OptimizerFlags

from src.controllers.settings_controller import SettingsController
from src.views.common import ConfigurationChangeHandler, run_configuration_change

controller = SettingsController()


def global_settings_gui(
    combined_config: CombinedConfig,
    on_change: ConfigurationChangeHandler | None = None,
    on_pending_change: Callable[[], None] | None = None,
) -> Callable[[], bool]:
    """Build controls for the configuration's generation limit and optimizer flags."""
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
        try:
            if not run_configuration_change(
                on_change,
                lambda: controller.update_settings(
                    combined_config,
                    int(value),
                    optimizer_flags.value or [],
                ),
            ):
                return False
        except (TypeError, ValueError) as exc:
            ui.notify(str(exc), type="negative")
            return False
        pending_settings = False
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
        pending_settings = False
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
