# File name: schedule_filters_controller.py
# Primary Author: Dylan Groff


"""
General Use case examples:

schedule = load_schedule_csv("schedule.csv")
resource_schedule = create_resource_schedule(schedule)
print(resource_schedule)

"""

import csv


def load_schedule_csv(filename):
    """
    Load the generated schedule CSV file.

    Returns:
        A list of dictionaries, one for each course.
    """
    schedule = []

    with open(filename, "r", newline="") as file:
        reader = csv.DictReader(file)

        for row in reader:
            schedule.append(row)

    return schedule


def create_resource_schedule(schedule):
    """
    Convert the course-based schedule into one row per meeting.

    Each meeting is associated with either its room or lab.
    """

    resource_schedule = []

    for course in schedule:
        course_name = course["course"]
        faculty = course["faculty"]
        room = course["room"]
        lab = course["lab"]

        # A course can have multiple meeting times
        for time in course["times"].split(","):
            time = time.strip()

            # ^ indicates a lab meeting
            is_lab = time.endswith("^")

            # Remove the lab marker
            if is_lab:
                time = time[:-1]

            # Split "MON 09:00-09:50"
            day, times = time.split(" ")

            # Split "09:00-09:50"
            start, end = times.split("-")

            # Use the lab for lab meetings.
            # Otherwise use the room.
            if is_lab:
                resource = lab
            else:
                resource = room

            resource_schedule.append({
                "resource": resource,
                "course": course_name,
                "faculty": faculty,
                "day": day,
                "start": start,
                "end": end
            })

    return resource_schedule


def sort_schedule(schedule, column=None, descending=False):
    """
    Sort the schedule.

    If no column is provided, the schedule is sorted by:
        1. Day
        2. Start time

    This is the default chronological order.

    A specific column can also be provided for sorting.
    """

    day_order = {
        "MON": 1,
        "TUE": 2,
        "WED": 3,
        "THU": 4,
        "FRI": 5
    }

    # Default sort: day -> start time
    if column is None:
        return sorted(
            schedule,
            key=lambda row: (
                day_order[row["day"]],
                row["start"]
            ),
            reverse=descending
        )

    # Special handling for day sorting
    if column == "day":
        return sorted(
            schedule,
            key=lambda row: day_order[row["day"]],
            reverse=descending
        )

    # Normal column sorting
    return sorted(
        schedule,
        key=lambda row: row[column],
        reverse=descending
    )


def filter_by_resource(schedule, resource):
    """
    Return only meetings using the specified room or lab.
    """

    return [
        row for row in schedule
        if row["resource"] == resource
    ]


def filter_by_faculty(schedule, faculty):
    """
    Return only meetings for the specified faculty member.
    """

    return [
        row for row in schedule
        if row["faculty"] == faculty
    ]


def filter_by_course(schedule, course):
    """
    Return only meetings for the specified course.
    """

    return [
        row for row in schedule
        if row["course"] == course
    ]