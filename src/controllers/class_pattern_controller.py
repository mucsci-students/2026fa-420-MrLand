"""GUI controller for class-pattern updates.

Used by: GUI."""

from src.controllers.class_pattern_operations_controller import (
    add_class_pattern_from_values,
    delete_class_pattern_from_values,
    update_class_pattern_from_values,
)


class ClassPatternController:
    """Validate and coordinate class pattern mutations for the GUI."""

    @staticmethod
    def add_pattern(patterns, credits, meetings, disabled=False, start_time=None):
        return add_class_pattern_from_values(
            patterns,
            credits,
            meetings,
            disabled=disabled,
            start_time=start_time,
        )

    @staticmethod
    def update_pattern(patterns, existing_pattern, credits, meetings, disabled=False, start_time=None):
        return update_class_pattern_from_values(
            patterns,
            existing_pattern,
            credits,
            meetings,
            disabled=disabled,
            start_time=start_time,
        )

    @staticmethod
    def delete_pattern(patterns, pattern_to_delete):
        return delete_class_pattern_from_values(patterns, pattern_to_delete)
