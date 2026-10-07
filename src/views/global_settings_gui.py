from nicegui import ui
from scheduler.config import CombinedConfig, OptimizerFlags

from src.controllers.settings_controller import SettingsController

controller = SettingsController()


def global_settings_gui(
    combined_config: CombinedConfig,
    on_change: ConfigurationChangeHandler | None = None,
) -> None:
    ui.label("Global settings").classes("text-xl font-semibold text-white")
    ui.label("Configure schedule generation behavior.").classes(
        "text-sm text-[#9fb2b8]"
    )

    generation_limit = ui.number(
        "Generation limit", value=combined_config.limit, min=1, step=1
    ).classes("w-56")
    optimizer_flags = ui.select(
        [flag.value for flag in OptimizerFlags],
        value=[flag.value for flag in combined_config.optimizer_flags],
        multiple=True,
        label="Optimizer flags",
    ).props("use-chips clearable").classes("w-full max-w-2xl")
    current_settings = ui.label().classes("text-sm text-[#9fb2b8]")

    def refresh_summary() -> None:
        active_flags = ", ".join(
            flag.value for flag in combined_config.optimizer_flags
        ) or "None"
        current_settings.set_text(
            f"Current settings: generation limit {combined_config.limit}; "
            f"optimizer flags {active_flags}"
        )

    def save_settings() -> None:
        value = generation_limit.value
        if value is None or not float(value).is_integer():
            ui.notify("Generation limit must be a whole number.", type="negative")
            return
        try:
            controller.update_settings(
                combined_config,
                int(value),
                optimizer_flags.value or [],
            )
        except (TypeError, ValueError) as exc:
            ui.notify(str(exc), type="negative")
            return
        refresh_summary()
        ui.notify("Global settings saved to the current draft.", type="positive")

    def reset_to_defaults() -> None:
        controller.reset_settings(combined_config)
        generation_limit.value = combined_config.limit
        optimizer_flags.value = [
            flag.value for flag in combined_config.optimizer_flags
        ]
        refresh_summary()
        ui.notify("Global settings reset to defaults.", type="positive")

    with ui.row().classes("w-full flex-wrap items-center gap-2"):
        ui.button(
            "Save settings", icon="save", on_click=save_settings
        ).props("unelevated").classes("bg-[#75e6da] text-[#101820]")
        ui.button(
            "Reset defaults", icon="restart_alt", on_click=reset_to_defaults
        ).props("outline").classes("border-[#45616b] text-[#d8e7e8]")

    refresh_summary()
