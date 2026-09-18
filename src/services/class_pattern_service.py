from pydantic import ValidationError

from scheduler.config import (
    TimeSlotConfig,
    ClassPattern,
    Meeting,
    Day,
    DeliveryMode,
)


def get_day():
    """Get a valid Day from the user."""
    day_input = input(
        "Enter day (MON, TUE, WED, THU, FRI): "
    ).strip().upper()

    try:
        return Day(day_input)
    except ValueError:
        print("Invalid day. Please enter MON, TUE, WED, THU, or FRI.")
        return None


def get_integer(prompt):
    """Get a valid integer from the user."""
    while True:
        try:
            return int(input(prompt).strip())
        except ValueError:
            print("Please enter a valid number.")


def get_delivery_mode():
    """Get a valid delivery mode from the user."""
    delivery_input = input(
        "Enter delivery mode (in_person/online): "
    ).strip().lower()

    if delivery_input == "in_person":
        return DeliveryMode.IN_PERSON

    if delivery_input == "online":
        return DeliveryMode.ONLINE

    print("Invalid delivery mode.")
    return None


def create_meeting():
    """Create one Meeting from user input."""
    day = get_day()

    if day is None:
        return None

    start_time = input(
        "Enter meeting start time (HH:MM), or press Enter for none: "
    ).strip()

    if not start_time:
        start_time = None

    duration = get_integer("Enter duration in minutes: ")

    lab = (
        input("Is this a lab meeting? (y/n): ")
        .strip()
        .lower() == "y"
    )

    delivery = get_delivery_mode()

    if delivery is None:
        return None

    try:
        return Meeting(
            day=day,
            start_time=start_time,
            duration=duration,
            lab=lab,
            delivery=delivery
        )
    except ValidationError as e:
        print("Invalid meeting:")
        for error in e.errors():
            print(f"  - {error['msg']}")
        return None


def add_class_pattern(time_slot_config: TimeSlotConfig):
    print("\nADD CLASS PATTERN")

    credits = get_integer("Enter credits: ")

    disabled = (
        input("Is this pattern disabled? (y/n): ")
        .strip()
        .lower() == "y"
    )

    start_time = input(
        "Enter start time (HH:MM), or press Enter for none: "
    ).strip()

    if not start_time:
        start_time = None

    meetings = []

    while True:
        add_more = input("Add a meeting? (y/n): ").strip().lower()

        if add_more != "y":
            break

        meeting = create_meeting()

        if meeting is not None:
            meetings.append(meeting)

    try:
        pattern = ClassPattern(
            credits=credits,
            meetings=meetings,
            disabled=disabled,
            start_time=start_time
        )
    except ValidationError as e:
        print("Invalid class pattern:")
        for error in e.errors():
            print(f"  - {error['msg']}")
        return

    time_slot_config.classes.append(pattern)

    print("Class pattern added successfully.")


def view_class_patterns(time_slot_config: TimeSlotConfig):
    print("\nCLASS PATTERNS")

    if not time_slot_config.classes:
        print("No class patterns found.")
        return

    for i, pattern in enumerate(time_slot_config.classes, start=1):
        status = "Disabled" if pattern.disabled else "Enabled"

        print(f"\n{i}. Credits: {pattern.credits}")
        print(f"   Status: {status}")
        print(f"   Start time: {pattern.start_time}")

        print("   Meetings:")

        if not pattern.meetings:
            print("     No meetings.")
        else:
            for j, meeting in enumerate(pattern.meetings, start=1):
                print(
                    f"     {j}. "
                    f"{meeting.day.value} "
                    f"{meeting.start_time or 'No start time'} "
                    f"({meeting.duration} min) "
                    f"Lab: {meeting.lab} "
                    f"Delivery: {meeting.delivery.value}"
                )


def select_class_pattern(time_slot_config):
    """Return a selected class pattern or None."""
    if not time_slot_config.classes:
        print("No class patterns found.")
        return None

    view_class_patterns(time_slot_config)

    index = get_integer(
        "\nEnter the class pattern number: "
    ) - 1

    if index < 0 or index >= len(time_slot_config.classes):
        print("Invalid class pattern.")
        return None

    return time_slot_config.classes[index]


def modify_class_pattern(time_slot_config: TimeSlotConfig):
    pattern = select_class_pattern(time_slot_config)

    if pattern is None:
        return

    credits = get_integer(
        f"Enter credits [{pattern.credits}]: "
    )

    disabled = (
        input("Is this pattern disabled? (y/n): ")
        .strip()
        .lower() == "y"
    )

    start_time = input(
        "Enter start time (HH:MM), or press Enter for none: "
    ).strip()

    if not start_time:
        start_time = None

    try:
        pattern.credits = credits
        pattern.disabled = disabled
        pattern.start_time = start_time
    except ValidationError as e:
        print("Invalid class pattern:")
        for error in e.errors():
            print(f"  - {error['msg']}")
        return

    print("Class pattern modified successfully.")


def delete_class_pattern(time_slot_config: TimeSlotConfig):
    pattern = select_class_pattern(time_slot_config)

    if pattern is None:
        return

    time_slot_config.classes.remove(pattern)

    print("Class pattern deleted successfully.")


# ---------------- MEETING CRUD ----------------

def select_meeting(time_slot_config):
    """Select a class pattern and one of its meetings."""
    pattern = select_class_pattern(time_slot_config)

    if pattern is None:
        return None, None

    if not pattern.meetings:
        print("No meetings found for this class pattern.")
        return None, None

    print("\nMEETINGS")

    for i, meeting in enumerate(pattern.meetings, start=1):
        print(
            f"{i}. {meeting.day.value} "
            f"{meeting.start_time or 'No start time'} "
            f"({meeting.duration} min) "
            f"Lab: {meeting.lab} "
            f"Delivery: {meeting.delivery.value}"
        )

    index = get_integer(
        "Enter the meeting number: "
    ) - 1

    if index < 0 or index >= len(pattern.meetings):
        print("Invalid meeting.")
        return None, None

    return pattern, index


def add_meeting(time_slot_config: TimeSlotConfig):
    pattern = select_class_pattern(time_slot_config)

    if pattern is None:
        return

    meeting = create_meeting()

    if meeting is None:
        return

    try:
        # Build a temporary pattern so the ClassPattern validators
        # can check duplicate days and lab rules before changing data.
        test_meetings = pattern.meetings + [meeting]

        ClassPattern(
            credits=pattern.credits,
            meetings=test_meetings,
            disabled=pattern.disabled,
            start_time=pattern.start_time
        )
    except ValidationError as e:
        print("Meeting cannot be added:")
        for error in e.errors():
            print(f"  - {error['msg']}")
        return

    pattern.meetings.append(meeting)

    print("Meeting added successfully.")


def view_meetings(time_slot_config: TimeSlotConfig):
    pattern = select_class_pattern(time_slot_config)

    if pattern is None:
        return

    if not pattern.meetings:
        print("No meetings found.")
        return

    print("\nMEETINGS")

    for i, meeting in enumerate(pattern.meetings, start=1):
        print(
            f"{i}. {meeting.day.value} "
            f"{meeting.start_time or 'No start time'} "
            f"({meeting.duration} min) "
            f"Lab: {meeting.lab} "
            f"Delivery: {meeting.delivery.value}"
        )


def modify_meeting(time_slot_config: TimeSlotConfig):
    pattern, index = select_meeting(time_slot_config)

    if pattern is None:
        return

    meeting = create_meeting()

    if meeting is None:
        return

    new_meetings = pattern.meetings.copy()
    new_meetings[index] = meeting

    try:
        ClassPattern(
            credits=pattern.credits,
            meetings=new_meetings,
            disabled=pattern.disabled,
            start_time=pattern.start_time
        )
    except ValidationError as e:
        print("Meeting cannot be modified:")
        for error in e.errors():
            print(f"  - {error['msg']}")
        return

    pattern.meetings[index] = meeting

    print("Meeting modified successfully.")


def delete_meeting(time_slot_config: TimeSlotConfig):
    pattern, index = select_meeting(time_slot_config)

    if pattern is None:
        return

    pattern.meetings.pop(index)

    print("Meeting deleted successfully.")