# File name: course.py
# Author: Dylan Groff


from scheduler.config import CourseConfig


# list to hold the courses
courses = []

def add_course():
    # get information from user
    course_id = get_course_ID()
    credits = get_credits()
    capacity = get_capacity
    section = get_section_ID()
    labs = get_labs()
    rooms = get_rooms()
    conflicts = get_conflicts()
    faculties = get_faculty()

    courses.append(CourseConfig(
        course_id=course_id,
        credits=credits,
        capacity=capacity,
        section=section,
        labs=labs,
        rooms=rooms,
        conflicts=conflicts,
        faculties=faculties
    ))
    

def modify_course():
    # find course
    # ask which attribute to change
    # change it
    return


def delete_course():
    # find course
    # remove it from courses
    return


def view_courses():
    if not courses:
        print("No courses found.")
        return

    print("\nCOURSES")
    print("-" * 80)

    for i, course in enumerate(courses, start=1):
        print(f"Course {i}:")
        print(f"  Course ID:       {course.course_id}")
        print(f"  Section ID:      {course.section_id}")
        print(f"  Credits:         {course.credits}")
        print(f"  Capacity:        {course.capacity}")
        print(f"  Rooms:           {course.rooms}")
        print(f"  Labs:            {course.labs}")
        print(f"  Conflicts:       {course.conflicts}")
        print(f"  Faculty:         {course.faculties}")
        print(f"  Modality:        {course.modality}")
        print(f"  Room Features:   {course.required_room_features}")
        print(f"  Lab Features:    {course.required_lab_features}")
        print(f"  Reserve Room:    {course.reserve_room_during_lab}")
        print("-" * 80)



#------------------- Getters for course data -----------------------------


def get_course_ID():
    try:
        course_id = input("Enter course ID: ")

        if not course_id.strip():
            raise ValueError("Course ID cannot be empty.")

        return course_id

    except ValueError as e:
        print(f"Invalid input: {e}")
        return get_course_ID()
    

def get_credits():
    try:
        credits = int(input("Enter number of credits: "))

        if credits <= 0:
            raise ValueError("Credits must be greater than 0.")

        return credits

    except ValueError as e:
        print(f"Invalid input: {e}")
        return get_credits()
    

def get_capacity():
    try:
        capacity = int(input("Enter course capacity: "))

        if capacity <= 0:
            raise ValueError("Capacity must be greater than 0.")

        return capacity

    except ValueError as e:
        print(f"Invalid input: {e}")
        return get_capacity()
    

def get_section_ID():
    try:
        section_id = input("Enter section ID (or press Enter for none): ")

        if not section_id.strip():
            return None

        return section_id

    except ValueError as e:
        print(f"Invalid input: {e}")
        return get_section_ID()
    

def get_rooms():
    try:
        rooms = input("Enter available rooms (comma-separated): ")

        rooms = [room.strip() for room in rooms.split(",")]

        if not rooms or rooms == [""]:
            raise ValueError("At least one room must be entered.")

        if len(rooms) != len(set(rooms)):
            raise ValueError("Duplicate rooms are not allowed.")

        return rooms

    except ValueError as e:
        print(f"Invalid input: {e}")
        return get_rooms()
    

def get_conflicts():
    try:
        conflicts = input("Enter conflicting courses (comma-separated): ")

        if not conflicts.strip():
            return []

        conflicts = [course.strip() for course in conflicts.split(",")]

        if len(conflicts) != len(set(conflicts)):
            raise ValueError("Duplicate conflicts are not allowed.")

        return conflicts

    except ValueError as e:
        print(f"Invalid input: {e}")
        return get_conflicts()
    

def get_faculty():
    try:
        faculty = input("Enter faculty (comma-separated), or enter 'none': ")

        if faculty.lower().strip() == "none":
            return None

        faculty = [person.strip() for person in faculty.split(",")]

        if not faculty or faculty == [""]:
            raise ValueError("Faculty list cannot be empty.")

        if len(faculty) != len(set(faculty)):
            raise ValueError("Duplicate faculty members are not allowed.")

        return faculty

    except ValueError as e:
        print(f"Invalid input: {e}")
        return get_faculty()
    
    
def get_labs():
    try:
        labs = input("Enter available labs (comma-separated): ")

        if not labs.strip():
            return []

        labs = [lab.strip() for lab in labs.split(",")]

        if len(labs) != len(set(labs)):
            raise ValueError("Duplicate labs are not allowed.")

        return labs

    except ValueError as e:
        print(f"Invalid input: {e}")
        return get_labs()