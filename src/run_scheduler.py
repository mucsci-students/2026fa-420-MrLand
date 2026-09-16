# run_scheduler.py  
# check


from scheduler.config import CombinedConfig, SchedulerConfig, TimeSlotConfig
from scheduler.scheduler import Scheduler


from services.faculty_service import faculty_members
from services.course_service import course_members
from services.rooms_service import room_members
from services.lab_service import lab_members


# Stores generated schedules so Micah's "display schedules" feature can read them.
generated_schedules = []




# ---- getters -----------------------------------------------------------


def getTimeBlock(day):
    """Get one time block (start-spacing-end) for the given day."""
    print(f"\nTime block for {day}")
    start = input("Enter start time (HH:MM): ").strip()
    end = input("Enter end time (HH:MM): ").strip()
    try:
        spacing = int(input("Enter spacing in minutes: "))
    except ValueError:
        print("Invalid input. Please enter a number for spacing.")
        return getTimeBlock(day)
    return {"start": start, "spacing": spacing, "end": end}




def getTimeSlotConfig():
    """
    Build the TimeSlotConfig needed to run the scheduler.


    NOTE: no teammate currently owns building this — confirm with the team
    whether this belongs to its own feature before relying on it long-term.
    """
    days = ["MON", "TUE", "WED", "THU", "FRI"]
    times = {}
    for day in days:
        blocks = []
        print(f"\nAvailability blocks for {day}")
        print("Enter 'done' when finished with this day.")
        while True:
            answer = input("Add a time block? (enter/'done'): ").strip()
            if answer.lower() == "done":
                break
            blocks.append(getTimeBlock(day))
        if blocks:
            times[day] = blocks


    classes = []
    print("\nEnter class meeting patterns.")
    while True:
        answer = input("Add a class pattern? (enter/'done'): ").strip()
        if answer.lower() == "done":
            break
        try:
            credits = int(input("Enter credits for this pattern: "))
        except ValueError:
            print("Invalid input. Please enter a number for credits.")
            continue
        meetings = []
        while True:
            day = input("Enter meeting day (or 'done' to finish meetings): ").strip().upper()
            if day == "DONE":
                break
            try:
                duration = int(input("Enter meeting duration (minutes): "))
            except ValueError:
                print("Invalid input. Please enter a number for duration.")
                continue
            is_lab = confirm_yes_no("Is this the lab meeting?")
            meetings.append({"day": day, "duration": duration, "lab": is_lab})
        classes.append({"credits": credits, "meetings": meetings})


    return {"times": times, "classes": classes}




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
    """Assemble the current configuration and run the scheduler on it."""
    if not course_members or not faculty_members or not room_members:
        print("No saved configurations")
        return


    try:
        scheduler_config = SchedulerConfig(
            rooms=room_members,
            labs=lab_members,
            courses=course_members,
            faculty=faculty_members,
        )
        time_slot_config = getTimeSlotConfig()
        full_config = CombinedConfig(
            config=scheduler_config,
            time_slot_config=TimeSlotConfig(**time_slot_config),
        )
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

