# config_builder.py
#
# Assembles a complete CombinedConfig (SchedulerConfig + TimeSlotConfig) from
# the data collected by the create() menu, and saves it via config_io.
#
# NOTE: adjust these four imports to match where your team's lists actually
# live. As observed across the codebase:
#   - faculty_members and rooms appear to live in config.py
#   - courses is local to course.py
#   - labs is local to services/lab_service.py
from config import faculty_members, rooms
from course import courses
from services.lab_service import labs

from scheduler.config import (
    ClassPattern,
    CombinedConfig,
    Meeting,
    SchedulerConfig,
    TimeBlock,
    TimeSlotConfig,
)
from config_io import config_load as _config_load_file
from config_io import config_exists, config_save

WEEKDAYS = ["MON", "TUE", "WED", "THU", "FRI"]


# ---- small input helpers --------------------------------------------------


def _get_int(prompt, predicate=lambda n: True, error="Please enter a valid number."):
    """Prompt for an int, looping until predicate(value) is True."""
    while True:
        raw = input(prompt).strip()
        try:
            value = int(raw)
        except ValueError:
            print(error)
            continue
        if not predicate(value):
            print(error)
            continue
        return value


def _confirm_yes_no(prompt):
    answer = input(f"{prompt} (yes/no): ").strip().lower()
    if answer in ("yes", "y"):
        return True
    if answer in ("no", "n"):
        return False
    print("Please enter yes or no.")
    return _confirm_yes_no(prompt)


# ---- TimeBlock / times ------------------------------------------------


def get_time_block(day):
    """Prompt for one TimeBlock, retrying on validation failure."""
    print(f"\nTime block for {day}")
    start = input("Enter start time (HH:MM): ").strip()
    end = input("Enter end time (HH:MM): ").strip()
    spacing = _get_int(
        "Enter spacing in minutes: ",
        predicate=lambda n: n > 0,
        error="Spacing must be a positive number of minutes.",
    )
    try:
        return TimeBlock(start=start, spacing=spacing, end=end)
    except Exception as e:
        print(f"Invalid time block: {e}")
        return get_time_block(day)


def get_times_for_all_days():
    """
    Prompt for time blocks for every weekday.

    TimeSlotConfig requires every weekday (MON-FRI) to have at least one
    TimeBlock, so each day is re-prompted until at least one block exists.
    """
    times = {}
    for day in WEEKDAYS:
        blocks = []
        print(f"\nAvailability blocks for {day}")
        print("At least one block is required for this day.")
        print("Enter 'done' when finished with this day.")
        while True:
            answer = input("Add a time block? (enter/'done'): ").strip()
            if answer.lower() == "done":
                if not blocks:
                    print(f"{day} needs at least one time block before you can move on.")
                    continue
                break
            blocks.append(get_time_block(day))
        times[day] = blocks
    return times


# ---- Meeting / ClassPattern --------------------------------------------


def get_meeting():
    """Prompt for one Meeting within a class pattern."""
    day = input("Enter meeting day (MON/TUE/WED/THU/FRI): ").strip().upper()
    if day not in WEEKDAYS:
        print("Invalid day. Please enter MON, TUE, WED, THU, or FRI.")
        return get_meeting()

    duration = _get_int(
        "Enter meeting duration (minutes): ",
        predicate=lambda n: n > 0,
        error="Duration must be a positive number of minutes.",
    )

    start_time = input(
        "Enter a fixed start time for this meeting (HH:MM), or press Enter to skip: "
    ).strip()
    start_time = start_time or None

    is_lab = _confirm_yes_no("Is this the lab meeting?")

    delivery = "in_person"
    if is_lab:
        print("Lab meetings must be in_person; delivery set to in_person.")
    else:
        online = _confirm_yes_no("Is this meeting held online?")
        delivery = "online" if online else "in_person"

    try:
        return Meeting(
            day=day,
            start_time=start_time,
            duration=duration,
            lab=is_lab,
            delivery=delivery,
        )
    except Exception as e:
        print(f"Invalid meeting: {e}")
        return get_meeting()


def get_class_pattern():
    """Prompt for one ClassPattern (credits + one or more meetings)."""
    credits = _get_int(
        "Enter credits for this pattern: ",
        predicate=lambda n: n > 0,
        error="Credits must be a positive number.",
    )

    meetings = []
    print("\nEnter meetings for this pattern. At least one is required.")
    while True:
        meetings.append(get_meeting())
        if meetings and not _confirm_yes_no("Add another meeting to this pattern?"):
            break

    pattern_start_time = input(
        "Enter a fallback start time for meetings without one (HH:MM), or press Enter to skip: "
    ).strip()
    pattern_start_time = pattern_start_time or None

    disabled = _confirm_yes_no("Should this pattern start out disabled?")

    try:
        return ClassPattern(
            credits=credits,
            meetings=meetings,
            disabled=disabled,
            start_time=pattern_start_time,
        )
    except Exception as e:
        print(f"Invalid class pattern: {e}")
        return get_class_pattern()


def get_class_patterns():
    """
    Prompt for one or more ClassPatterns.

    TimeSlotConfig requires at least one *enabled* pattern, so this keeps
    prompting until that condition is met.
    """
    patterns = []
    print("\nEnter class meeting patterns. At least one enabled pattern is required.")
    while True:
        patterns.append(get_class_pattern())
        if not _confirm_yes_no("Add another class pattern?"):
            if any(not p.disabled for p in patterns):
                break
            print("At least one enabled pattern is required before you can finish.")
    return patterns


# ---- TimeSlotConfig ------------------------------------------------------


def build_time_slot_config():
    """Interactively build a complete, validated TimeSlotConfig."""
    times = get_times_for_all_days()
    classes = get_class_patterns()

    use_defaults = _confirm_yes_no(
        "Use default gap/overlap settings (max_time_gap=30, min_time_overlap=45)?"
    )
    if use_defaults:
        try:
            return TimeSlotConfig(times=times, classes=classes)
        except Exception as e:
            print(f"Invalid time slot configuration: {e}")
            return build_time_slot_config()

    max_time_gap = _get_int(
        "Enter max_time_gap in minutes: ",
        predicate=lambda n: n >= 0,
        error="max_time_gap must be zero or a positive number of minutes.",
    )
    min_time_overlap = _get_int(
        "Enter min_time_overlap in minutes: ",
        predicate=lambda n: n > 0,
        error="min_time_overlap must be a positive number of minutes.",
    )

    try:
        return TimeSlotConfig(
            times=times,
            classes=classes,
            max_time_gap=max_time_gap,
            min_time_overlap=min_time_overlap,
        )
    except Exception as e:
        print(f"Invalid time slot configuration: {e}")
        return build_time_slot_config()


# ---- SchedulerConfig + CombinedConfig -------------------------------------


def build_scheduler_config():
    """Assemble a SchedulerConfig from the existing rooms/labs/courses/faculty lists."""
    return SchedulerConfig(
        rooms=rooms,
        labs=labs,
        courses=courses,
        faculty=faculty_members,
    )


def finalize_and_save_config():
    """
    Assemble everything entered so far (faculty, courses, rooms, labs, and a
    newly-collected TimeSlotConfig) into a CombinedConfig, and save it.

    Intended to be wired into navmenu.py's create() page as the "finish" /
    "save" step once the user is done adding resources.
    """
    if not courses or not faculty_members or not rooms:
        print("Add at least one course, faculty member, and room before saving a configuration.")
        return

    try:
        scheduler_config = build_scheduler_config()
    except Exception as e:
        print(f"Configuration is invalid, cannot save: {e}")
        return

    print("\nNow enter the time slot configuration for this schedule.")
    time_slot_config = build_time_slot_config()

    try:
        full_config = CombinedConfig(config=scheduler_config, time_slot_config=time_slot_config)
    except Exception as e:
        print(f"Configuration is invalid, cannot save: {e}")
        return

    config_name = input("Enter a name for this configuration: ").strip()
    if not config_name:
        print("Configuration name cannot be empty. Not saved.")
        return

    try:
        config_save(full_config, config_name)
    except Exception as e:
        print(f"Failed to save configuration '{config_name}': {e}")
        return

    print(f"Configuration '{config_name}' saved successfully.")


def load_config(config_name):
    """
    Load a saved CombinedConfig by name and replace the app's in-memory
    state (faculty_members, rooms, courses, labs) with its contents.

    This is the counterpart to finalize_and_save_config(): that function
    builds a CombinedConfig from the in-memory lists and saves it; this
    function loads a CombinedConfig and populates the in-memory lists
    from it, so view/modify/delete menus see the loaded data.

    Note: time_slot_config from the loaded file is not currently surfaced
    anywhere (no in-memory list holds it), since nothing else in the app
    reads it back out except run_scheduler(), which reloads the file
    itself via config_io.config_load() rather than through this function.
    """
    config_name = config_name.strip()

    if not config_name:
        print("Configuration name cannot be empty.")
        return

    if not config_exists(config_name):
        print(f"No saved configuration named '{config_name}'.")
        return

    try:
        full_config = _config_load_file(config_name)
    except Exception as e:
        print(f"Failed to load configuration '{config_name}': {e}")
        return

    faculty_members.clear()
    faculty_members.extend(full_config.config.faculty)

    rooms.clear()
    rooms.extend(full_config.config.rooms)

    courses.clear()
    courses.extend(full_config.config.courses)

    labs.clear()
    labs.extend(full_config.config.labs)

    print(f"Configuration '{config_name}' loaded successfully.")
    print(
        f"  {len(faculty_members)} faculty, {len(rooms)} rooms, "
        f"{len(courses)} courses, {len(labs)} labs."
    )