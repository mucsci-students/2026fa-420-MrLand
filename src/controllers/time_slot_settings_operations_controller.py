from scheduler.config import TimeSlotConfig


DEFAULT_MAX_TIME_GAP = 30
DEFAULT_MIN_TIME_OVERLAP = 45


def get_integer(prompt):
    """Get a valid integer from the user."""
    while True:
        try:
            return int(input(prompt).strip())
        except ValueError:
            print("Please enter a valid number.")


def view_time_slot_settings(time_slot_config: TimeSlotConfig):
    print("\nTIME SLOT SETTINGS")
    print(f"Max time gap: {time_slot_config.max_time_gap} minutes")
    print(f"Min time overlap: {time_slot_config.min_time_overlap} minutes")


def modify_time_slot_settings(time_slot_config: TimeSlotConfig):
    print("\nMODIFY TIME SLOT SETTINGS")

    max_time_gap = get_integer(
        f"Enter max time gap in minutes "
        f"(current: {time_slot_config.max_time_gap}): "
    )

    if max_time_gap <= 0:
        print("Max time gap must be greater than 0.")
        return

    min_time_overlap = get_integer(
        f"Enter min time overlap in minutes "
        f"(current: {time_slot_config.min_time_overlap}): "
    )

    if min_time_overlap <= 0:
        print("Min time overlap must be greater than 0.")
        return

    try:
        time_slot_config.max_time_gap = max_time_gap
        time_slot_config.min_time_overlap = min_time_overlap
    except ValueError as e:
        print("Unable to modify time slot settings:")
        print(f"  - {e}")
        return

    print("Time slot settings modified successfully.")


def reset_time_slot_settings(time_slot_config: TimeSlotConfig):
    time_slot_config.max_time_gap = DEFAULT_MAX_TIME_GAP
    time_slot_config.min_time_overlap = DEFAULT_MIN_TIME_OVERLAP

    print("Time slot settings reset successfully.")