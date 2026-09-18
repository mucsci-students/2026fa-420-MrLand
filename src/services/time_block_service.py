from pydantic import ValidationError

from scheduler.config import TimeSlotConfig, TimeBlock


VALID_DAYS = {"MON", "TUE", "WED", "THU", "FRI"}


def get_day():
    """Get a valid weekday from the user."""
    day = input(
        "Enter day (MON, TUE, WED, THU, FRI): "
    ).strip().upper()

    if day not in VALID_DAYS:
        print("Invalid day. Please enter MON, TUE, WED, THU, or FRI.")
        return None

    return day


def get_integer(prompt):
    """Get a valid integer from the user."""
    while True:
        try:
            return int(input(prompt).strip())
        except ValueError:
            print("Please enter a valid number.")


def add_time_block(time_slot_config: TimeSlotConfig):
    print("\nADD TIME BLOCK")

    day = get_day()

    if day is None:
        return

    start = input("Enter start time (HH:MM): ").strip()
    spacing = get_integer("Enter spacing in minutes: ")
    end = input("Enter end time (HH:MM): ").strip()

    try:
        time_block = TimeBlock(
            start=start,
            spacing=spacing,
            end=end
        )
    except ValidationError as e:
        print("Invalid time block:")
        for error in e.errors():
            print(f"  - {error['msg']}")
        return

    if day not in time_slot_config.times:
        time_slot_config.times[day] = []

    time_slot_config.times[day].append(time_block)

    print("Time block added successfully.")


def view_time_blocks(time_slot_config: TimeSlotConfig):
    print("\nTIME BLOCKS")

    if not time_slot_config.times:
        print("No time blocks found.")
        return

    for day, blocks in time_slot_config.times.items():
        print(f"\n{day}:")

        if not blocks:
            print("  No time blocks.")
            continue

        for i, block in enumerate(blocks, start=1):
            print(
                f"  {i}. {block.start}-{block.end} "
                f"(spacing: {block.spacing} minutes)"
            )


def modify_time_block(time_slot_config: TimeSlotConfig):
    if not time_slot_config.times:
        print("No time blocks found.")
        return

    view_time_blocks(time_slot_config)

    day = get_day()

    if day is None:
        return

    if day not in time_slot_config.times:
        print("No time blocks found for that day.")
        return

    blocks = time_slot_config.times[day]

    if not blocks:
        print("No time blocks found for that day.")
        return

    index = get_integer(
        "Enter the number of the time block to modify: "
    ) - 1

    if index < 0 or index >= len(blocks):
        print("Invalid time block.")
        return

    start = input("Enter new start time (HH:MM): ").strip()
    spacing = get_integer("Enter new spacing in minutes: ")
    end = input("Enter new end time (HH:MM): ").strip()

    try:
        new_time_block = TimeBlock(
            start=start,
            spacing=spacing,
            end=end
        )
    except ValidationError as e:
        print("Invalid time block:")
        for error in e.errors():
            print(f"  - {error['msg']}")
        return

    blocks[index] = new_time_block

    print("Time block modified successfully.")


def delete_time_block(time_slot_config: TimeSlotConfig):
    if not time_slot_config.times:
        print("No time blocks found.")
        return

    view_time_blocks(time_slot_config)

    day = get_day()

    if day is None:
        return

    if day not in time_slot_config.times:
        print("No time blocks found for that day.")
        return

    blocks = time_slot_config.times[day]

    if not blocks:
        print("No time blocks found for that day.")
        return

    index = get_integer(
        "Enter the number of the time block to delete: "
    ) - 1

    if index < 0 or index >= len(blocks):
        print("Invalid time block.")
        return

    blocks.pop(index)

    print("Time block deleted successfully.")

