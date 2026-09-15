# File name: course.py
# Author: Dylan Groff


from scheduler.config import CourseConfig


# list to hold the courses
courses = []

def add_course():
    # get information from user
    course_id = get_course_id()
    section = get_section_id()
    credits = get_credits()
    capacity = get_capacity()
    modality = get_modality()
    rooms = get_rooms()
    labs = get_labs()
    required_room_features = get_required_room_features()
    required_lab_features = get_required_lab_features()
    reserve_room_during_lab = get_reserve_room()
    conflicts = get_conflicts()
    faculties = get_faculty()

    courses.append(CourseConfig(
        course_id=course_id,
        section=section,
        credits=credits,
        capacity=capacity,
        modality=modality,
        rooms=rooms,
        labs=labs,
        required_room_features=required_room_features,
        required_lab_features=required_lab_features,
        reserve_room_during_lab=reserve_room_during_lab,
        conflicts=conflicts,
        faculties=faculties
    ))
    

def modify_course():
    if not courses:
        print("No courses found.")
        return

    print("COURSES:")
    for i, course in enumerate(courses, start=1):
        print(f"{i}. {course.course_id}")

    try:
        index = int(input("Enter the number of the course to modify: ")) - 1

        if 0 <= index < len(courses):
            selected_course = courses[index]

            print(f"Modifying course: {selected_course.course_id}")
            print("1. Course ID")
            print("2. Credits")
            print("3. Capacity")
            print("4. Rooms")
            print("5. Labs")
            print("6. Conflicts")
            print("7. Faculty")
            print("8. Section ID")
            print("9. Modality")
            print("10. Required Room Features")
            print("11. Required Lab Features")
            print("12. Reserve Room During Lab")

            choice = int(input("Enter the number of the field to modify: "))

            if choice == 1:
                selected_course.course_id = get_course_id()
            elif choice == 2:
                selected_course.credits = get_credits()
            elif choice == 3:
                selected_course.capacity = get_capacity()
            elif choice == 4:
                selected_course.rooms = get_rooms()
            elif choice == 5:
                selected_course.labs = get_labs()
            elif choice == 6:
                selected_course.conflicts = get_conflicts()
            elif choice == 7:
                selected_course.faculties = get_faculty()
            elif choice == 8:
                selected_course.section_id = get_section_id()
            elif choice == 9:
                selected_course.modality = get_modality()
            elif choice == 10:
                selected_course.required_room_features = get_required_room_features()
            elif choice == 11:
                selected_course.required_lab_features = get_required_lab_features()
            elif choice == 12:
                selected_course.reserve_room_during_lab = get_reserve_room()
            else:
                print("Invalid selection.")
                return

            print(f"Updated course: {selected_course.course_id}")

        else:
            print("Invalid selection.")

    except ValueError:
        print("Invalid input. Please enter a valid number.")


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


def get_course_id():
    try:
        course_id = input("Enter course ID: ")

        if not course_id.strip():
            raise ValueError("Course ID cannot be empty.")

        return course_id

    except ValueError as e:
        print(f"Invalid input: {e}")
        return get_course_id()
    

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
    

def get_section_id():
    try:
        section_id = input("Enter section ID (or press Enter for none): ")

        if not section_id.strip():
            return None

        return section_id

    except ValueError as e:
        print(f"Invalid input: {e}")
        return get_section_id()
    

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
    
    
def get_modality():
    try:
        modality = input("Enter course modality (in_person, online, hybrid): ").lower()

        if modality not in ["in_person", "online", "hybrid"]:
            raise ValueError("Modality must be in_person, online, or hybrid.")

        return modality

    except ValueError as e:
        print(f"Invalid input: {e}")
        return get_modality()
        

def get_required_room_features():
    try:
        features = input("Enter required room features (comma-separated): ")

        if not features.strip():
            return set()

        features = {feature.strip() for feature in features.split(",")}

        return features

    except ValueError as e:
        print(f"Invalid input: {e}")
        return get_required_room_features()
    

def get_required_lab_features():
    try:
        features = input("Enter required lab features (comma-separated): ")

        if not features.strip():
            return set()

        features = {feature.strip() for feature in features.split(",")}

        return features

    except ValueError as e:
        print(f"Invalid input: {e}")
        return get_required_lab_features()
    

def get_reserve_room():
    try:
        reserve_room = input("Reserve room during lab? (yes/no): ").lower()

        if reserve_room == "yes":
            return True
        elif reserve_room == "no":
            return False
        else:
            raise ValueError("Please enter yes or no.")

    except ValueError as e:
        print(f"Invalid input: {e}")
        return get_reserve_room()
    

