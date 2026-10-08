from src.controllers.settings_operations_controller import (
    reset_settings_values,
    update_settings_from_values,
)


class SettingsController:
    """Coordinate global scheduler settings for the GUI."""

    @staticmethod
    def update_settings(combined_config, limit, optimizer_flags):
        return update_settings_from_values(combined_config, limit, optimizer_flags)

    @staticmethod
    def reset_settings(combined_config):
        return reset_settings_values(combined_config)
