"""Legacy interactive console workflows for course management."""

from scheduler.config import CourseConfig

from src.controllers.course_helpers import course_exists


def add_course(course_members):
    # get information from user

    # check for duplicate courseIDs with the same sectionID
    while True:
        course_id = get_course_id()
        section_id = get_section_id()

        if course_exists(course_members, course_id, section_id):
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
        required_room_features = get_required_room_features()
        required_lab_features = get_required_lab_features()
        reserve_room_during_lab = get_reserve_room()
    else:
        room = []
        lab = []
        required_room_features = set()
        required_lab_features = set()
        reserve_room_during_lab = False
    conflicts = get_conflicts(course_members, course_id)
    faculty = get_faculty()

    # adds course to the list after using CourseConfig constructor
    try:
        course_members.append(
            CourseConfig(
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
                faculty=faculty,
            )
        )

        print(f"Course {course_id} added successfully.")
    except (TypeError, ValueError, AttributeError) as e:
        print(f"Error occurred while adding course: {e}")
        print("Course was not added.")

        # command interface to let user retry or quit to courses
        choice = input()

        while choice not in ["r", "c"]:
            print("INVALID COMMAND.\n  (r)etry\n  (c)ourses\n")
            choice = input()

        if choice == "r":
            add_course(course_members)
        else:
            return


def modify_course(course_members):
    # checks to make sure there is at least one course
    if not course_members:
        print("No courses found.")
        return

    # prints out courses
    view_courses(course_members)

    try:
        index = int(input("Enter the number of the course to modify: ")) - 1

        if 0 <= index < len(course_members):
            selected_course = course_members[index]

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

            choice = int(input("Enter the number of the field to modify: "))

            # course_id
            if choice == 1:
                new_course_id = get_course_id()

                # validation check to ensure no courseID and sectionID combinations
                if course_exists(
                    course_members, new_course_id, selected_course.section_id, selected_course
                ):
                    print("That course section already exists.")
                    return

                selected_course.course_id = new_course_id

            # section_id
            elif choice == 2:
                new_section_id = get_section_id()

                # validation check to ensure no courseID and sectionID combinations
                if course_exists(
                    course_members, selected_course.course_id, new_section_id, selected_course
                ):
                    print("That course section already exists.")
                    return

                selected_course.section_id = new_section_id

            # credits
            elif choice == 3:
                selected_course.credits = get_credits()

            # capacity
            elif choice == 4:
                selected_course.capacity = get_capacity()

            # modality
            elif choice == 5:
                new_modality = get_modality()

                # adds check to take away room and lab
                if new_modality == "online":
                    selected_course.room = []
                    selected_course.lab = []
                    selected_course.required_room_features = set()
                    selected_course.required_lab_features = set()
                    selected_course.reserve_room_during_lab = False

                selected_course.modality = new_modality

            # rooms
            elif choice == 6:
                # adds check for online modality
                if selected_course.modality != "online":
                    selected_course.room = get_room()
                else:
                    print("Online classes can not have rooms.")

            # labs
            elif choice == 7:
                # adds check for online modality
                if selected_course.modality != "online":
                    selected_course.lab = get_lab()
                else:
                    print("Online classes can not have labs.")

            # required room features
            elif choice == 8:
                if selected_course.modality != "online":
                    selected_course.required_room_features = get_required_room_features()
                else:
                    print("Online classes can not have required room features.")

            # required lab features
            elif choice == 9:
                if selected_course.modality != "online":
                    selected_course.required_lab_features = get_required_lab_features()
                else:
                    print("Online classes can not have required lab features.")

            # reserve room
            elif choice == 10:
                if selected_course.modality != "online":
                    selected_course.reserve_room_during_lab = get_reserve_room()
                else:
                    print("Online classes can not reserve rooms during labs.")

            # conflicts
            elif choice == 11:
                selected_course.conflicts = get_conflicts(course_members, selected_course.course_id)

            # faculty
            elif choice == 12:
                selected_course.faculty = get_faculty()

            else:
                print("Invalid selection.")
                return

            print(f"Updated course: {selected_course.course_id}")

        else:
            print("Invalid selection.")

    except (TypeError, ValueError, AttributeError) as e:
        print(f"Error occurred while modifying course: {e}")
        print("Course was not modified.")
        print("Commands:\n  (r)etry\n  (c)ourses\n")

        choice = input()

        while choice not in ["r", "c"]:
            print("INVALID COMMAND.\n  (r)etry\n  (c)ourses\n")
            choice = input()

        if choice == "r":
            modify_course(course_members)
        else:
            return


def delete_course(course_members):
    # checks to make sure there is at least one course
    if not course_members:
        print("No courses found.")
        return

    # prints out courses
    view_courses(course_members)

    try:
        index = int(input("Enter the number of the course to delete: ")) - 1

        if 0 <= index < len(course_members):
            deleted_course = course_members.pop(index)
            print(f"Deleted course: {deleted_course.course_id}")
        else:
            print("Invalid selection.")

    except ValueError:
        print("Invalid input. Please enter a valid number.")


def view_courses(course_members):
    # checks to make sure there is at least one course
    if not course_members:
        print("No courses found.")
        return

    print("\nCOURSES")
    print("-" * 80)

    for i, course in enumerate(course_members, start=1):
        print(f"Course {i}:")
        print(f"  Course ID:       {course.course_id}")
        print(f"  Section ID:      {course.section_id}")
        print(f"  Credits:         {course.credits}")
        print(f"  Capacity:        {course.capacity}")
        print(f"  Modality:        {course.modality}")
        print(f"  Room:            {course.room or 'None'}")
        print(f"  Lab:             {course.lab or 'None'}")
        print(f"  Room Features:   {course.required_room_features or 'None'}")
        print(f"  Lab Features:    {course.required_lab_features or 'None'}")
        print(f"  Reserve Room:    {course.reserve_room_during_lab}")
        print(f"  Conflicts:       {course.conflicts}")
        print(f"  Faculty:         {course.faculty}")
        print("-" * 80)


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


def get_room():
    try:
        rooms = input("Enter available rooms (comma-separated): ")

        rooms = [room.strip() for room in rooms.split(",")]

        if not rooms or rooms == [""]:
            raise ValueError("At least one room must be entered.")

        if any(not room for room in rooms):
            raise ValueError("Room names cannot be empty.")

        # checks for duplicates
        if len(rooms) != len(set(rooms)):
            raise ValueError("Duplicate rooms are not allowed.")

        return rooms

    except ValueError as e:
        print(f"Invalid input: {e}")
        return get_room()


def get_conflicts(course_members, course_id):
    try:
        conflicts = input("Enter conflicting courses (comma-separated): ")

        if not conflicts.strip():
            return []

        conflicts = [course.strip() for course in conflicts.split(",")]

        # checks for duplicates
        if len(conflicts) != len(set(conflicts)):
            raise ValueError("Duplicate conflicts are not allowed.")

        for conflict in conflicts:
            # ensures course does not conflict with itself
            if conflict.lower() == course_id.lower():
                raise ValueError("A course cannot conflict with itself.")

            # ensures conflict is a valid course
            if not any(course.course_id.lower() == conflict.lower() for course in course_members):
                raise ValueError(f"Course '{conflict}' does not exist.")

        return conflicts

    except ValueError as e:
        print(f"Invalid input: {e}")
        return get_conflicts(course_members, course_id)


def get_faculty():
    try:
        faculty = input("Enter faculty (comma-separated), or enter 'none': ")

        if faculty.lower().strip() == "none":
            return None

        faculty = [person.strip() for person in faculty.split(",")]

        if any(not person for person in faculty):
            raise ValueError("Faculty names cannot be empty.")

        if not faculty or faculty == [""]:
            raise ValueError("Faculty list cannot be empty.")

        # checks for duplicate faculty members
        if len(faculty) != len(set(faculty)):
            raise ValueError("Duplicate faculty members are not allowed.")

        return faculty

    except ValueError as e:
        print(f"Invalid input: {e}")
        return get_faculty()


def get_lab():
    try:
        labs = input("Enter available labs (comma-separated): ")

        if not labs.strip():
            return []

        labs = [lab.strip() for lab in labs.split(",")]

        if any(not lab for lab in labs):
            raise ValueError("Lab names cannot be empty.")

        # checks for duplicates
        if len(labs) != len(set(labs)):
            raise ValueError("Duplicate labs are not allowed.")

        return labs

    except ValueError as e:
        print(f"Invalid input: {e}")
        return get_lab()


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

        features = [feature.strip() for feature in features.split(",")]

        if any(not feature for feature in features):
            raise ValueError("Room feature names cannot be empty.")

        # checks for duplicates
        if len(features) != len(set(features)):
            raise ValueError("Duplicate room features are not allowed.")

        return set(features)

    except ValueError as e:
        print(f"Invalid input: {e}")
        return get_required_room_features()


def get_required_lab_features():
    try:
        features = input("Enter required lab features (comma-separated): ")

        if not features.strip():
            return set()

        features = [feature.strip() for feature in features.split(",")]

        if any(not feature for feature in features):
            raise ValueError("Lab feature names cannot be empty.")

        # checks for duplicates
        if len(features) != len(set(features)):
            raise ValueError("Duplicate lab features are not allowed.")

        return set(features)

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
