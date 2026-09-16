from scheduler.config import FacultyConfig
from config import *


#getters to get faculty information from user input
def get_name():
    name = input("Enter faculty name: ")
    for faculty in faculty_members:
        if faculty.name.lower() == name.lower():
            print("Faculty member already exists. Please enter a different name.")
            return get_name()
    return name

def get_max_credits():
    try:
        max_credits = int(input("Enter maximum credits: "))
        return max_credits
    except ValueError:
        print("Invalid input. Please enter a valid integer for maximum credits.")
        return get_max_credits()

def get_min_credits():
    try:
        min_credits = int(input("Enter minimum credits: "))
        return min_credits
    except ValueError:
        print("Invalid input. Please enter a valid integer for minimum credits.")
        return get_min_credits()

def get_course_limit():
    try:
        course_limit = int(input("Enter course limit: "))
        return course_limit
    except ValueError:
        print("Invalid input. Please enter a valid integer for course limit.")
        return get_course_limit()

def get_max_days():
    try:
        max_days = int(input("Enter maximum days: "))
        return max_days
    except ValueError:
        print("Invalid input. Please enter a valid integer for maximum days.")
        return get_max_days()

#helper function to get time availability from user input
def faculty_times():
    times = {}
    days = ["MON", "TUE", "WED", "THU", "FRI"]
    print("Availability for each day:")
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
def course_preference_getter():
    course_preferences = {}
    print("Course Preferences:")
    while True:
        course = input("Enter preferred course name (or 'done' to finish): ")
        if course.lower() == 'done':
            break
        #elif course in course_preferences:
        #    print("Course already entered. Please enter a different course.")
        #    return course_preference_getter()

        preference = input("Enter preference (1-10): ")
        while (not preference.isdigit() or int(preference) < 1 or int(preference) > 10):
            print("Invalid preference. Please enter a number between 1 and 10.")
            preference = input("Enter preference (1-10): ")
        course_preferences[course] = int(preference)
    return course_preferences

#helper function to get room preferences from user input
def room_preference_getter():
    room_preferences = {}
    print("Room Preferences:")
    while True:
        room = input("Enter preferred room (or 'done' to finish): ")
        if room.lower() == 'done':
            break
        #elif room in room_preferences:
        #    print("Room already entered. Please enter a different room.")
        #    return room_preference_getter()

        preference = input("Enter preference (1-10): ")
        while (not preference.isdigit() or int(preference) < 1 or int(preference) > 10):
            print("Invalid preference. Please enter a number between 1 and 10.")
            preference = input("Enter preference (1-10): ")
        room_preferences[room] = int(preference)
    return room_preferences

#helper function to get lab preferences from user input
def lab_preference_getter():
    lab_preferences = {}
    print("Lab Preferences:")
    while True:
        lab = input("Enter preferred lab (or 'done' to finish): ")
        if lab.lower() == 'done':
            break
        #elif lab in lab_preferences:
        #    print("Lab already entered. Please enter a different lab.")
        #    return lab_preference_getter()
        preference = input("Enter preference (1-10): ")
        while (not preference.isdigit() or int(preference) < 1 or int(preference) > 10):
            print("Invalid preference. Please enter a number between 1 and 10.")
            preference = input("Enter preference (1-10): ")
        lab_preferences[lab] = int(preference)
    return lab_preferences

#helper function to get mandatory teaching days from user input
def mandatory_days_getter():
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

#adds a faculty member to the faculty_members list, with error handling for invalid input
def add_faculty():
    print("ADD NEW FACULTY MEMBER")
    name = get_name()
    max_credits = get_max_credits()
    min_credits = get_min_credits()
    course_limit = get_course_limit()
    times = faculty_times()
    max_days = get_max_days()
    course_preferences = course_preference_getter()
    room_preferences = room_preference_getter()
    lab_preferences = lab_preference_getter()
    mandatory_days = mandatory_days_getter()

    try: 
        faculty_members.append(FacultyConfig(
        name=name,
        maximum_credits=max_credits,
        minimum_credits=min_credits,
        unique_course_limit=course_limit,
        times=times,
        maximum_days=max_days,
        course_preferences=course_preferences,
        room_preferences=room_preferences,
        lab_preferences=lab_preferences,
        mandatory_days=mandatory_days))
        print("Faculty member added successfully.")
    
    except Exception as e:
        print(f"Error occurred while adding faculty member: {e}")
        print("Faculty member was not added.")
        print("Commands:\n  (r)etry\n  (f)aculty\n")
        choice = input()
        while choice not in ["r", "f"]:
            print("INVALID COMMAND.\n  (r)etry\n  (f)aculty\n")
            choice = input()
        if choice == "r":
            add_faculty()
        else:
            return
def  view_faculty_names():
    if not faculty_members:
        print("No faculty members found.")
        return False
    print("FACULTY MEMBERS:")
    for i, faculty in enumerate(faculty_members, start=1):
        print(f"{i}. {faculty.name}")
    return True
#modify a faculty member's information, with error handling for invalid input
def modify_faculty():
    if (not view_faculty_names()):
        return
    try:
        index = int(input("Enter the number of the faculty member to modify: ")) - 1
    except ValueError:
        print("Invalid input. Please enter a valid number.")
        return modify_faculty()
    if 0 <= index < len(faculty_members):
        try:
            selected_faculty = faculty_members[index]
            print(f"Modifying faculty member: {selected_faculty.name}")
            print("1. Faculty Name")
            print("2. Maximum Credits")
            print("3. Minimum Credits")
            print("4. Course Limit")
            print("5. Times")
            print("6. Maximum Days")
            print("7. Course Preferences")
            print("8. Room Preferences")
            print("9. Lab Preferences")
            print("10. Mandatory Days")
            choice = int(input("Enter the number of the attribute to modify: "))
            if choice == 1:
                selected_faculty.name = get_name()
            elif choice == 2:
                selected_faculty.maximum_credits = get_max_credits()
            elif choice == 3:
                selected_faculty.minimum_credits = get_min_credits()
            elif choice == 4:
                selected_faculty.unique_course_limit = get_course_limit()
            elif choice == 5:
                selected_faculty.times = faculty_times()
            elif choice == 6:
                selected_faculty.maximum_days = get_max_days()
            elif choice == 7:
                selected_faculty.course_preferences = course_preference_getter()
            elif choice == 8:
                selected_faculty.room_preferences = room_preference_getter()
            elif choice == 9:
                selected_faculty.lab_preferences = lab_preference_getter()
            elif choice == 10:
                selected_faculty.mandatory_days = mandatory_days_getter()
            else:
                print("Invalid selection.")
        except Exception as e:
            print(f"Error occurred while modifying faculty member: {e}")
            print("Faculty member was not modified.")
            print("Commands:\n  (r)etry\n  (f)aculty\n")
            choice = input()
            while choice not in ["r", "f"]:
                print("INVALID COMMAND.\n  (r)etry\n  (f)aculty\n")
                choice = input()
            if choice == "r":
                modify_faculty()
            else:
                return
        print(f"Updated faculty member: {selected_faculty.name}")
    else:
        print("Invalid selection.")

#prints out all the faculty members and their information
def view_faculty():
    if not faculty_members:
        print("No faculty members found.")
        return
    print("FACULTY MEMBERS:")
    for i, faculty in enumerate(faculty_members, start=1):
        print(f"{i}. {faculty.name}")
        print(f"   Maximum Credits: {faculty.maximum_credits}")
        print(f"   Minimum Credits: {faculty.minimum_credits}")
        print(f"   Course Limit: {faculty.unique_course_limit}")
        print(f"   Times: {faculty.times}")
        print(f"   Maximum Days: {faculty.maximum_days}")
        print(f"   Course Preferences: {faculty.course_preferences}")
        print(f"   Room Preferences: {faculty.room_preferences}")
        print(f"   Lab Preferences: {faculty.lab_preferences}")
        print(f"   Mandatory Days: {faculty.mandatory_days}")

#deletes a specified faculty member
def delete_faculty():
    view_faculty_names()
    try:
        index = int(input("Enter the number of the faculty member to delete: ")) - 1
    except ValueError:
        print("Invalid input. Please enter a valid number.")
        return
    if 0 <= index < len(faculty_members):
        deleted_faculty = faculty_members.pop(index)
        print(f"Deleted faculty member: {deleted_faculty.name}")
    else:
        print("Invalid selection.")
