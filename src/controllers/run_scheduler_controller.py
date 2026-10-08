"""Runs the scheduler from a named saved configuration and reports results.

Used by: CLI."""

from src.models.schedule_result import ScheduleResult
from src.models.configuration_model import (
    config_exists,
    load_config as config_load,
)
from scheduler.scheduler import Scheduler


def confirm_yes_no(prompt: str) -> bool:
    """Ask a yes/no question, looping until a valid answer is given."""
    while True:
        answer = input(f"{prompt} (yes/no): ").strip().lower()
        if answer in ("yes", "y"):
            return True
        if answer in ("no", "n"):
            return False
        print("Please enter yes or no.")


def run_scheduler(
    schedules,
    *,
    config_loader=None,
    exists_checker=None,
    scheduler_factory=None,
    result_type=None,
):
    """Load a saved configuration and append generated schedules to the list."""
    config_loader = config_loader or config_load
    exists_checker = exists_checker or config_exists
    scheduler_factory = scheduler_factory or Scheduler
    result_type = result_type or ScheduleResult
    config_name = input("Enter the name of the configuration to run: ").strip()

    if not exists_checker(config_name):
        print(f"No saved configuration named '{config_name}'.")
        return

    try:
        full_config = config_loader(config_name)
    except Exception as error:
        print(f"Failed to load configuration '{config_name}': {error}")
        return

    try:
        scheduler = scheduler_factory(full_config)
    except Exception as error:
        print(f"Error occurred while starting the scheduler: {error}")
        return

    generated = []
    for schedule in scheduler.get_models():
        generated.append(schedule)
        if len(generated) >= full_config.limit:
            break

    if not generated:
        print("No valid schedule could be generated for this configuration.")
        diagnosis = scheduler.diagnose()
        print(f"Status: {diagnosis.status}")
        for finding in diagnosis.conflicting_constraints:
            print(f"  - {finding.message}")
        for suggestion in diagnosis.relaxation_suggestions:
            print(f"  Suggestion: {suggestion.message}")
        return

    valid_count = sum(
        1 for schedule in generated if scheduler.audit_schedule(schedule).is_valid
    )

    schedules.extend(
        result_type(config_name=config_name, schedule=s, config=full_config)
        for s in generated
    )

    print(
        f"Scheduler ran successfully. Generated {len(generated)} schedule(s), "
        f"{valid_count} valid."
    )
