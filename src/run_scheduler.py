from services.config_service import load_config as config_load, config_exists
from scheduler.scheduler import Scheduler
from schedule_result import ScheduleResult


def confirm_yes_no(prompt):
    """Ask a yes/no question, looping until a valid answer is given."""
    while True:
        answer = input(f"{prompt} (yes/no): ").strip().lower()
        if answer in ("yes", "y"):
            return True
        if answer in ("no", "n"):
            return False
        print("Please enter yes or no.")


def run_scheduler(schedules):
    """Load a saved configuration by name and run the scheduler on it,
    generating up to config.limit schedules."""
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

    generated = []
    for schedule in sched.get_models():
        generated.append(schedule)
        if len(generated) >= full_config.limit:
            break

    if not generated:
        print("No valid schedule could be generated for this configuration.")
        diagnosis = sched.diagnose()
        print(f"Status: {diagnosis.status}")
        for finding in diagnosis.conflicting_constraints:
            print(f"  - {finding.message}")
        for suggestion in diagnosis.relaxation_suggestions:
            print(f"  Suggestion: {suggestion.message}")
        return

    valid_count = sum(1 for schedule in generated if sched.audit_schedule(schedule).is_valid)

    schedules.extend(ScheduleResult(config_name=config_name, schedule=s) for s in generated)

    print(f"Scheduler ran successfully. Generated {len(generated)} schedule(s), {valid_count} valid.")