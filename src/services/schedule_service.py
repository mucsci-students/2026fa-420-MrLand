import os

from schedule_result import ScheduleResult

filepath = os.path.join("src", "schedules")


def view_schedules(schedules: list[ScheduleResult]) -> None:
    """Print all generated schedules in a readable format."""
    if not schedules:
        print("No schedules generated yet.")
        return

    for i, result in enumerate(schedules, start=1):
        print(f"\nSchedule {i} — config: {result.config_name}")
        for instance in result.schedule:
            print(
                f"  {instance.course}: {instance.faculty}, "
                f"room={instance.room}, lab={instance.lab}, time={instance.time}"
            )


def export_schedules(schedules: list[ScheduleResult]) -> None:
    """Export all generated schedules to CSV files, one per schedule,
    named <config_name>_schedule<n>.csv, numbered per config."""
    if not schedules:
        print("No schedules generated yet.")
        return

    os.makedirs(filepath, exist_ok=True)

    per_config_counts: dict[str, int] = {}

    for result in schedules:
        per_config_counts[result.config_name] = per_config_counts.get(result.config_name, 0) + 1
        n = per_config_counts[result.config_name]

        filename = f"{result.config_name}_schedule{n}.csv"
        path = os.path.join(filepath, filename)

        header = "course,faculty,room,lab,times\n"
        rows = "\n".join(instance.as_csv() for instance in result.schedule)

        with open(path, "w", encoding="utf-8", newline="") as f:
            f.write(header + rows)

        print(f"Exported: {filename}")