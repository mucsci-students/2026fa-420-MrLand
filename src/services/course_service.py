# courses_service.py

from scheduler.config import CourseConfig
from conflict import modify_conflicts, conflicts_menu


# method to add a course to the list of courses
# prompts for data and then uses CourseConfig to create the object
def add_course(courses):
    while True:
        course_id = get_course_id()
        section_id = get_section_id()

        if course_exists(courses, course_id, section_id):
            print("That course section already exists. Please enter a different course or section.")
        else:
            break

    credits = get_credits()
    capacity = get_capacity()
    modality = get_modality()
    # Does not let user choose a room or lab if the class is online
    if modality != "online":
        room = get_room()
        lab = get_lab()
    else:
        room = []
        lab = []
    required_room_features = get_required_room_features()
    required_lab_features = get_required_lab_features()
    reserve_room_during_lab = get_reserve_room()
    conflicts = conflicts_menu(course_id, courses)
    faculty = get_faculty()

    try:
        courses.append(CourseConfig(
            course_id=course_id,
            section_id=section_id,
            credits=credits,
            capacity=capacity,
            modality=modality,
            room=room,
            lab=lab,
            required_room_features=required_room_features,
            required_lab_features=required_lab_features,
            reserve_room_during_lab=reserve_room_during_lab,
            conflicts=conflicts,
            faculty=faculty
        ))

        print(f"Course {course_id} added successfully.")
    except Exception as e:
        print(f"Error occurred while adding course: {e}")
        print("Course was not added.")

        choice = input("Commands:\n  (r)etry\n  (c)ourses\n")
        while choice not in ["r", "c"]:
            print("INVALID COMMAND.\n  (r)etry\n  (c)ourses\n")
            choice = input()

        if choice == "r":
            add_course(courses)
        else:
            return


# method to allow user to pick a course and modify it
def modify_course(courses):
    if not courses:
        print("No courses found.")
        return

    view_courses(courses)

    try:
        index = int(input("Enter the number of the course to modify: ")) - 1
    except ValueError:
        print("Invalid input. Please enter a valid number.")
        return

    if not (0 <= index < len(courses)):
        print("Invalid selection.")
        return

    selected_course = courses[index]

    print(f"Modifying course: {selected_course.course_id}")
    print("1. Course ID")
    print("2. Section ID")
    print("3. Credits")
    print("4. Capacity")
    print("5. Modality")
    print("6. Room")
    print("7. Lab")
    print("8. Required Room Features")
    print("9. Required Lab Features")
    print("10. Reserve Room During Lab")
    print("11. Conflicts")
    print("12. Faculty")

    try:
        choice = int(input("Enter the number of the field to modify: "))
    except ValueError:
        print("Invalid selection.")
        return

    try:
        if choice == 1:
            new_course_id = get_course_id()
            if course_exists(courses, new_course_id, selected_course.section_id, exclude=selected_course):
                print("That course section already exists.")
                return
            selected_course.course_id = new_course_id

        elif choice == 2:
            new_section_id = get_section_id()
            if course_exists(courses, selected_course.course_id, new_section_id, exclude=selected_course):
                print("That course section already exists.")
                return
            selected_course.section_id = new_section_id

        elif choice == 3:
            selected_course.credits = get_credits()

        elif choice == 4:
            selected_course.capacity = get_capacity()

        elif choice == 5:
            new_modality = get_modality()
            if new_modality == "online":
                selected_course.room = []
                selected_course.lab = []
            selected_course.modality = new_modality

        elif choice == 6:
            if selected_course.modality != "online":
                selected_course.room = get_room()
            else:
                print("Online classes can not have rooms.")

        elif choice == 7:
            if selected_course.modality != "online":
                selected_course.lab = get_lab()
            else:
                print("Online classes can not have labs.")

        elif choice == 8:
            selected_course.required_room_features = get_required_room_features()

        elif choice == 9:
            selected_course.required_lab_features = get_required_lab_features()

        elif choice == 10:
            selected_course.reserve_room_during_lab = get_reserve_room()

        elif choice == 11:
            modify_conflicts(selected_course, courses)

        elif choice == 12:
            selected_course.faculty = get_faculty()

        else:
            print("Invalid selection.")
            return

        print(f"Updated course: {selected_course.course_id}")

    except Exception as e:
        print(f"Error occurred while modifying course: {e}")
        print("Course was not modified.")
        print("Commands:\n  (r)etry\n  (c)ourses\n")

        retry_choice = input()
        while retry_choice not in ["r", "c"]:
            print("INVALID COMMAND.\n  (r)etry\n  (c)ourses\n")
            retry_choice = input()

        if retry_choice == "r":
            modify_course(courses)
        else:
            return


# method to delete a course from the courses list
def delete_course(courses):
    if not courses:
        print("No courses found.")
        return

    view_courses(courses)

    try:
        index = int(input("Enter the number of the course to delete: ")) - 1
    except ValueError:
        print("Invalid input. Please enter a valid number.")
        return

    if 0 <= index < len(courses):
        deleted_course = courses.pop(index)
        print(f"Deleted course: {deleted_course.course_id}")
    else:
        print("Invalid selection.")


# method to print out all the courses in the course list in a readable manner
def view_courses(courses):
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
        print(f"  Modality:        {course.modality}")
        print(f"  Room:           {course.room}")
        print(f"  Lab:            {course.lab}")
        print(f"  Room Features:   {course.required_room_features}")
        print(f"  Lab Features:    {course.required_lab_features}")
        print(f"  Reserve Room:    {course.reserve_room_during_lab}")
        print(f"  Conflicts:       {course.conflicts}")
        print(f"  Faculty:         {course.faculty}")
        print("-" * 80)


# helper to check for duplicate courseIDs with the same sectionID
def course_exists(courses, course_id, section_id, exclude=None):
    for course in courses:
        if course is exclude:
            continue
        if (course.course_id.lower() == course_id.lower() and
                course.section_id == section_id):
            return True
    return False


# ------------------- Getters for course data -----------------------------

def get_course_id():
    while True:
        course_id = input("Enter course ID: ")
        if not course_id.strip():
            print("Invalid input: Course ID cannot be empty.")
            continue
        return course_id


def get_credits():
    while True:
        try:
            credits = int(input("Enter number of credits: "))
        except ValueError:
            print("Invalid input: Credits must be a valid integer.")
            continue
        if credits <= 0:
            print("Invalid input: Credits must be greater than 0.")
            continue
        return credits


def get_capacity():
    while True:
        try:
            capacity = int(input("Enter course capacity: "))
        except ValueError:
            print("Invalid input: Capacity must be a valid integer.")
            continue
        if capacity <= 0:
            print("Invalid input: Capacity must be greater than 0.")
            continue
        return capacity


def get_section_id():
    section_id = input("Enter section ID (or press Enter for none): ")
    if not section_id.strip():
        return None
    return section_id


def get_room():
    while True:
        rooms = input("Enter available rooms (comma-separated): ")
        rooms = [room.strip() for room in rooms.split(",")]

        if not rooms or rooms == [""]:
            print("Invalid input: At least one room must be entered.")
            continue
        if any(not room for room in rooms):
            print("Invalid input: Room names cannot be empty.")
            continue
        if len(rooms) != len(set(rooms)):
            print("Invalid input: Duplicate rooms are not allowed.")
            continue

        return rooms


def get_faculty():
    while True:
        faculty = input("Enter faculty (comma-separated), or enter 'none': ")

        if faculty.lower().strip() == "none":
            return None

        faculty = [person.strip() for person in faculty.split(",")]

        if not faculty or faculty == [""]:
            print("Invalid input: Faculty list cannot be empty.")
            continue
        if any(not person for person in faculty):
            print("Invalid input: Faculty names cannot be empty.")
            continue
        if len(faculty) != len(set(faculty)):
            print("Invalid input: Duplicate faculty members are not allowed.")
            continue

        return faculty


def get_lab():
    while True:
        labs = input("Enter available labs (comma-separated): ")

        if not labs.strip():
            return []

        labs = [lab.strip() for lab in labs.split(",")]

        if any(not lab for lab in labs):
            print("Invalid input: Lab names cannot be empty.")
            continue
        if len(labs) != len(set(labs)):
            print("Invalid input: Duplicate labs are not allowed.")
            continue

        return labs


def get_modality():
    while True:
        modality = input("Enter course modality (in_person, online, hybrid): ").lower()
        if modality not in ["in_person", "online", "hybrid"]:
            print("Invalid input: Modality must be in_person, online, or hybrid.")
            continue
        return modality


def get_required_room_features():
    while True:
        features = input("Enter required room features (comma-separated): ")

        if not features.strip():
            return set()

        features = [feature.strip() for feature in features.split(",")]

        if any(not feature for feature in features):
            print("Invalid input: Room feature names cannot be empty.")
            continue
        if len(features) != len(set(features)):
            print("Invalid input: Duplicate room features are not allowed.")
            continue

        return set(features)


def get_required_lab_features():
    while True:
        features = input("Enter required lab features (comma-separated): ")

        if not features.strip():
            return set()

        features = [feature.strip() for feature in features.split(",")]

        if len(features) != len(set(features)):
            print("Invalid input: Duplicate lab features are not allowed.")
            continue

        return set(features)


def get_reserve_room():
    while True:
        reserve_room = input("Reserve room during lab? (yes/no): ").lower()
        if reserve_room == "yes":
            return True
        elif reserve_room == "no":
            return False
        else:
            print("Invalid input: Please enter yes or no.")