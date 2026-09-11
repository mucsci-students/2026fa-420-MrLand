from pydantic import ValidationError
from scheduler.config import FacultyConfig


faculty_members = []

#helper function to get time availability from user input
def facultyTimes():
    times = {}
    days = ["MON", "TUE", "WED", "THU", "FRI"]
    for day in days:
        ranges = []
        print(f"\nAvailability for {day}")
        print("Enter 'done' when finished with this day.")
        while True:
            time_range = input("Enter time range (HH:MM-HH:MM): ")
            if time_range.lower() == "done":
                break
            ranges.append(time_range)
        if ranges:
            times[day] = ranges
    return times

#helper function to get course preferences from user input
def coursePreference():
    coursePreferences = {}
    while True:
        course = input("Enter course name (or 'done' to finish): ")
        if course.lower() == 'done':
            break
        
        preference = input("Enter preference (1-10): ")
        while (not preference.isdigit() or int(preference) < 1 or int(preference) > 10):
            print("Invalid preference. Please enter a number between 1 and 10.")
            preference = input("Enter preference (1-10): ")
        coursePreferences[course] = int(preference)
    return coursePreferences

#helper function to get room preferences from user input
def roomPreference():
    roomPreferences = {}
    while True:
        room = input("Enter room (or 'done' to finish): ")
        if room.lower() == 'done':
            break
        
        preference = input("Enter preference (1-10): ")
        while (not preference.isdigit() or int(preference) < 1 or int(preference) > 10):
            print("Invalid preference. Please enter a number between 1 and 10.")
            preference = input("Enter preference (1-10): ")
        roomPreferences[room] = int(preference)
    return roomPreferences
#helper function to get lab preferences from user input
def labPreference():
    labPreferences = {}
    while True:
        lab = input("Enter lab (or 'done' to finish): ")
        if lab.lower() == 'done':
            break
        
        preference = input("Enter preference (1-10): ")
        while (not preference.isdigit() or int(preference) < 1 or int(preference) > 10):
            print("Invalid preference. Please enter a number between 1 and 10.")
            preference = input("Enter preference (1-10): ")
        labPreferences[lab] = int(preference)
    return labPreferences
#helper function to get mandatory teaching days from user input
def mandatoryDays():
    days = set()
    while True:
        day = input(
            "Enter a mandatory teaching day "
            "(Mon/Tue/Wed/Thu/Fri, or 'done' to finish): "
        )
        if day.lower() == "done":
            break
        day = day.lower()
        if day == "mon":
            days.add("MON")
        elif day == "tue":
            days.add("TUE")
        elif day == "wed":
            days.add("WED")
        elif day == "thu":
            days.add("THU")
        elif day == "fri":
            days.add("FRI")
        else:
            print("Invalid day. Please enter Mon, Tue, Wed, Thu, or Fri.")
    return days

def add_faculty():
    print("ADD NEW FACULTY MEMBER")
    name = input("Enter faculty name: ")
    max_credits = int(input("Enter maximum credits: "))
    min_credits = int(input("Enter minimum credits: "))
    course_limit = int(input("Enter course limit: "))
    times = facultyTimes()
    max_days = int(input("Enter maximum days: "))
    course_preferences = coursePreference()
    room_preferences = roomPreference()
    lab_preferences = labPreference()
    mandatory_days = mandatoryDays()

    faculty_member.append(FacultyConfig(
        name=name,
        max_credits=max_credits,
        min_credits=min_credits,
        course_limit=course_limit,
        times=times,
        max_days=max_days,
        course_preferences=course_preferences,
        room_preferences=room_preferences,
        lab_preferences=lab_preferences,
        mandatory_days=mandatory_days)
    )
