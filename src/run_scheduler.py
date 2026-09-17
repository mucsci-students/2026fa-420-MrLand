# run_scheduler.py

from services.config_service import load_config as config_load, config_exists
from scheduler.scheduler import Scheduler
from scheduler.config import TimeBlock, Meeting, ClassPattern, TimeSlotConfig

# Stores generated schedules so "display schedules" feature can read them.
generated_schedules = []

WEEKDAYS = ["MON", "TUE", "WED", "THU", "FRI"]


def confirm_yes_no(prompt):
    """Ask a yes/no question, looping until a valid answer is given."""
    answer = input(f"{prompt} (yes/no): ").strip().lower()
    if answer in ("yes", "y"):
        return True
    if answer in ("no", "n"):
        return False
    print("Please enter yes or no.")
    return confirm_yes_no(prompt)


# ---- time slot prompting --------------------------------------------------


def get_time_block(day):
    """Get one time block (start-spacing-end) for the given day."""
    print(f"\nTime block for {day}")
    start = input("Enter start time (HH:MM): ").strip()
    end = input("Enter end time (HH:MM): ").strip()
    try:
        spacing = int(input("Enter spacing in minutes: "))
    except ValueError:
        print("Invalid input. Please enter a number for spacing.")
        return get_time_block(day)
    try:
        return TimeBlock(start=start, spacing=spacing, end=end)
    except Exception as e:
        print(f"Invalid time block: {e}")
        return get_time_block(day)


def get_meeting():
    """Get one meeting within a class pattern."""
    day = input("Enter meeting day (MON/TUE/WED/THU/FRI): ").strip().upper()
    if day not in WEEKDAYS:
        print("Invalid day. Please enter MON, TUE, WED, THU, or FRI.")
        return get_meeting()
    try:
        duration = int(input("Enter meeting duration (minutes): "))
    except ValueError:
        print("Invalid input. Please enter a number for duration.")
        return get_meeting()
    is_lab = confirm_yes_no("Is this the lab meeting?")
    try:
        return Meeting(day=day, duration=duration, lab=is_lab)
    except Exception as e:
        print(f"Invalid meeting: {e}")
        return get_meeting()


def get_class_pattern():
    """Get one class pattern (credits + one or more meetings)."""
    try:
        credits = int(input("Enter credits for this pattern: "))
    except ValueError:
        print("Invalid input. Please enter a number for credits.")
        return get_class_pattern()

    meetings = []
    print("Enter meeting days for this pattern.")
    while True:
        meetings.append(get_meeting())
        if not confirm_yes_no("Add another meeting to this pattern?"):
            break

    try:
        return ClassPattern(credits=credits, meetings=meetings)
    except Exception as e:
        print(f"Invalid class pattern: {e}")
        return get_class_pattern()


def getTimeSlotConfig():
    """
    Interactively build a TimeSlotConfig.

    TimeSlotConfig requires every weekday (MON-FRI) to have at least one
    time block, and at least one enabled class pattern.
    """
    times = {}
    for day in WEEKDAYS:
        blocks = []
        print(f"\nAvailability blocks for {day}")
        print("At least one block is required. Enter 'done' when finished with this day.")
        while True:
            answer = input("Add a time block? (enter/'done'): ").strip()
            if answer.lower() == "done":
                if not blocks:
                    print(f"{day} needs at least one time block.")
                    continue
                break
            blocks.append(get_time_block(day))
        times[day] = blocks

    classes = []
    print("\nEnter class meeting patterns. At least one is required.")
    while True:
        classes.append(get_class_pattern())
        if not confirm_yes_no("Add another class pattern?"):
            break

    try:
        return TimeSlotConfig(times=times, classes=classes)
    except Exception as e:
        print(f"Invalid time slot configuration: {e}")
        return getTimeSlotConfig()


# ---- actions -------------------------------------------------------------


def run_scheduler():
    """Load a saved configuration by name, collect time slot data, and run the scheduler."""
    config_name = input("Enter the name of the configuration to run: ").strip()

    if not config_exists(config_name):
        print(f"No saved configuration named '{config_name}'.")
        return

    try:
        full_config = config_load(config_name)
    except Exception as e:
        print(f"Failed to load configuration '{config_name}': {e}")
        return

    print("\nEnter the time slot configuration to use for this run.")
    try:
        full_config.time_slot_config = getTimeSlotConfig()
    except Exception as e:
        print(f"Configuration is invalid, cannot run scheduler: {e}")
        return

    try:
        sched = Scheduler(full_config)
    except Exception as e:
        print(f"Error occurred while starting the scheduler: {e}")
        return

    schedule = next(sched.get_models(), None)

    if schedule is None:
        print("No valid schedule could be generated for this configuration.")
        diagnosis = sched.diagnose()
        print(f"Status: {diagnosis.status}")
        for finding in diagnosis.conflicting_constraints:
            print(f"  - {finding.message}")
        for suggestion in diagnosis.relaxation_suggestions:
            print(f"  Suggestion: {suggestion.message}")
        return

    generated_schedules.append(schedule)
    audit = sched.audit_schedule(schedule)

    print("Scheduler ran successfully.")
    print(f"Schedule valid: {audit.is_valid}")
    for instance in schedule:
        print(f"  {instance.course}: {instance.faculty}, room={instance.room}, lab={instance.lab}")


def view_schedules():
    """Print all schedules generated so far."""
    if not generated_schedules:
        print("Configuration has no saved schedules")
        return
    for i, schedule in enumerate(generated_schedules, start=1):
        print(f"\nSchedule {i}:")
        for instance in schedule:
            print(f"  {instance.course}: {instance.faculty}, room={instance.room}, lab={instance.lab}")