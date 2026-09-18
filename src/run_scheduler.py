# run_scheduler.py

from services.config_service import load_config as config_load, config_exists
from scheduler.scheduler import Scheduler

# Stores generated schedules so "display schedules" feature can read them.
generated_schedules = []


def confirm_yes_no(prompt):
    """Ask a yes/no question, looping until a valid answer is given."""
    answer = input(f"{prompt} (yes/no): ").strip().lower()
    if answer in ("yes", "y"):
        return True
    if answer in ("no", "n"):
        return False
    print("Please enter yes or no.")
    return confirm_yes_no(prompt)


# ---- actions -------------------------------------------------------------


def run_scheduler():
    """Load a saved configuration by name and run the scheduler on it."""
    config_name = input("Enter the name of the configuration to run: ").strip()

    if not config_exists(config_name):
        print(f"No saved configuration named '{config_name}'.")
        return

    try:
        full_config = config_load(config_name)
    except Exception as e:
        print(f"Failed to load configuration '{config_name}': {e}")
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