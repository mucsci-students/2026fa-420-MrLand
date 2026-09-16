# File name: course.py
# Primary Author: Dylan Groff


from scheduler.config import CourseConfig


# list to hold the courses
courses = []

from conflict import modify_conflicts, conflicts_menu

# method to add a course to the list of courses
# prompts for data and then uses CourseConfig to create the object
def add_course():
    # get information from user

    # check for duplicate courseIDs with the same sectionID
    while True:
        course_id = get_course_id()
        section_id = get_section_id()

        if course_exists(course_id, section_id):
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
    conflicts = conflicts_menu(course_id)
    faculty = get_faculty()

    # adds course to the list after using CourseConfig constructor
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

        # command interface to let user retry or quit to courses
        choice = input()

        while choice not in ["r", "c"]:
            print("INVALID COMMAND.\n  (r)etry\n  (c)ourses\n")
            choice = input()

        if choice == "r":
            add_course()
        else:
            return
    

# method to allow user to pick a course and modify it
def modify_course():
    # checks to make sure there is at least one course
    if not courses:
        print("No courses found.")
        return

    # prints out courses
    view_courses()

    try:
        index = int(input("Enter the number of the course to modify: ")) - 1

        if 0 <= index < len(courses):
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

            choice = int(input("Enter the number of the field to modify: "))

            # course_id
            if choice == 1:
                new_course_id = get_course_id()

                # validation check to ensure no courseID and sectionID combinations
                if course_exists(new_course_id, selected_course.section_id, selected_course):
                    print("That course section already exists.")
                    return

                selected_course.course_id = new_course_id

            # section_id
            elif choice == 2:
                new_section_id = get_section_id()

                # validation check to ensure no courseID and sectionID combinations
                if course_exists(selected_course.course_id, new_section_id, selected_course):
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

                # adds check to take away room
                if new_modality == "online":
                    selected_course.room = []
                    selected_course.lab = []
                
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
                selected_course.required_room_features = get_required_room_features()

            # required lab features
            elif choice == 9:
                selected_course.required_lab_features = get_required_lab_features()
            
            # reserve room
            elif choice == 10:
                selected_course.reserve_room_during_lab = get_reserve_room()
            
            # conflicts
            elif choice == 11:
                modify_conflicts(selected_course)
            
            # faculty
            elif choice == 12:
                selected_course.faculty = get_faculty()
                 
            else:
                print("Invalid selection.")
                return

            print(f"Updated course: {selected_course.course_id}")

        else:
            print("Invalid selection.")

    except Exception as e:
        print(f"Error occurred while modifying course: {e}")
        print("Course was not modified.")
        print("Commands:\n  (r)etry\n  (c)ourses\n")

        choice = input()

        while choice not in ["r", "c"]:
            print("INVALID COMMAND.\n  (r)etry\n  (c)ourses\n")
            choice = input()

        if choice == "r":
            modify_course()
        else:
            return


# method to delete a course from the courses list
def delete_course():
    # checks to make sure there is at least one course
    if not courses:
        print("No courses found.")
        return

    # prints out courses
    view_courses()

    try:
        index = int(input("Enter the number of the course to delete: ")) - 1

        if 0 <= index < len(courses):
            deleted_course = courses.pop(index)
            print(f"Deleted course: {deleted_course.course_id}")
        else:
            print("Invalid selection.")

    except ValueError:
        print("Invalid input. Please enter a valid number.")


# method to print out all the courses in the course list in a readable manner
def view_courses():
    # checks to make sure there is at least one course
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
def course_exists(course_id, section_id, exclude=None):
    for course in courses:
        if course is exclude:
            continue

        if (course.course_id.lower() == course_id.lower() and
                course.section_id == section_id):
            return True

    return False



#------------------- Getters for course data -----------------------------

# getter to get the course ID
def get_course_id():
    try:
        course_id = input("Enter course ID: ")

        if not course_id.strip():
            raise ValueError("Course ID cannot be empty.")

        return course_id

    except ValueError as e:
        print(f"Invalid input: {e}")
        return get_course_id()
    
# getter to get the number of credits for the course
def get_credits():
    try:
        credits = int(input("Enter number of credits: "))

        if credits <= 0:
            raise ValueError("Credits must be greater than 0.")

        return credits

    except ValueError as e:
        print(f"Invalid input: {e}")
        return get_credits()
    
# getter to get the capacity of students for the course
def get_capacity():
    try:
        capacity = int(input("Enter course capacity: "))

        if capacity <= 0:
            raise ValueError("Capacity must be greater than 0.")

        return capacity

    except ValueError as e:
        print(f"Invalid input: {e}")
        return get_capacity()
    
# getter to get the section ID for a course
def get_section_id():
    try:
        section_id = input("Enter section ID (or press Enter for none): ")

        if not section_id.strip():
            return None

        return section_id

    except ValueError as e:
        print(f"Invalid input: {e}")
        return get_section_id()
    
# getter to get the possible rooms the course could be in
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
    
# getter to get the conflicts between other courses
def get_conflicts(course_id):
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
            if not any(course.course_id.lower() == conflict.lower() for course in courses):
                raise ValueError(f"Course '{conflict}' does not exist.")

        return conflicts

    except ValueError as e:
        print(f"Invalid input: {e}")
        return get_conflicts(course_id)
    
# getter for the faculty that can teach the course
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
    
# getter to get the possible lab rooms for the course
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
    
# getter to get the modality of the course
def get_modality():
    try:
        modality = input("Enter course modality (in_person, online, hybrid): ").lower()

        if modality not in ["in_person", "online", "hybrid"]:
            raise ValueError("Modality must be in_person, online, or hybrid.")

        return modality

    except ValueError as e:
        print(f"Invalid input: {e}")
        return get_modality()
        
# getter to get required features of the room
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
    
# getter to get the required features of the lab
def get_required_lab_features():
    try:
        features = input("Enter required lab features (comma-separated): ")

        if not features.strip():
            return set()

        features = [feature.strip() for feature in features.split(",")]

        # checks for duplicates
        if len(features) != len(set(features)):
            raise ValueError("Duplicate lab features are not allowed.")

        return set(features)

    except ValueError as e:
        print(f"Invalid input: {e}")
        return get_required_lab_features()
    
# getter to get a bool to reserve a room or not
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
    

