"""GUI controller for time-block updates.

Used by: GUI."""

from src.controllers.time_block_operations_controller import (
    add_time_block_from_values,
    delete_time_block_from_values,
    update_time_block_from_values,
)


class TimeBlockController:
    """Validate and coordinate time block mutations for the GUI."""

    @staticmethod
    def add_block(times, day, start, spacing, end):
        return add_time_block_from_values(times, day, start, spacing, end)

    @staticmethod
    def update_block(times, existing_day, existing_block, day, start, spacing, end):
        return update_time_block_from_values(
            times,
            existing_day,
            existing_block,
            day,
            start,
            spacing,
            end,
        )

    @staticmethod
    def delete_block(times, day, block_to_delete):
        return delete_time_block_from_values(times, day, block_to_delete)
