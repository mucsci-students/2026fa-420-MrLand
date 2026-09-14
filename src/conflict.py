# conflict.py
from scheduler.config import CourseConfig 
#from course import course_members


# ---- getters ---------------------------------------------------------------

def getConflictCourseId(current_course):
    """Get one course_id to conflict with current_course, validated like getName()."""
    course_id = input("Enter the course that conflicts with this course: ").strip()

    if course_id == current_course.course_id:
        print("A course cannot conflict with itself. Please enter a different course.")
        return getConflictCourseId(current_course)

    if not any(c.course_id == course_id for c in course_members):
        print(f"Course '{course_id}' does not exist. Please enter a valid course.")
        return getConflictCourseId(current_course)

    if course_id in current_course.conflicts:
        print(f"'{course_id}' is already a conflict for this course. Please enter a different course.")
        return getConflictCourseId(current_course)

    return course_id


def getConflicts(current_course):
    """Get one or more conflicting course_ids, same 'enter until done' pattern as coursePreference()."""
    conflicts = []
    while True:
        course_id = input(
            "Enter a course that conflicts with this course (or 'done' to finish): "
        ).strip()
        if course_id.lower() == "done":
            break
        if course_id == current_course.course_id:
            print("A course cannot conflict with itself. Please enter a different course.")
            continue
        if not any(c.course_id == course_id for c in course_members):
            print(f"Course '{course_id}' does not exist. Please enter a valid course.")
            continue
        if course_id in current_course.conflicts or course_id in conflicts:
            print(f"'{course_id}' is already a conflict for this course.")
            continue
        conflicts.append(course_id)
    return conflicts


def getConflictIndexToDelete(current_course):
    """Get the index of an existing conflict to delete, validated like getName()."""
    for i, conflict_id in enumerate(current_course.conflicts, start=1):
        print(f"{i}. {conflict_id}")
    try:
        index = int(input("Enter the number of the conflict to delete: ")) - 1
    except ValueError:
        print("Invalid input. Please enter a number.")
        return getConflictIndexToDelete(current_course)

    if not (0 <= index < len(current_course.conflicts)):
        print("Invalid selection. Please enter a valid number.")
        return getConflictIndexToDelete(current_course)

    return index


# ---- actions -----------------------------------------------------------

def add_conflict(course):
    """Add one or more conflicts to the given course, mirroring add_faculty()'s shape."""
    print(f"ADD CONFLICT — {course.course_id}")
    print(f"Current conflicts: {course.conflicts or 'none'}")

    new_conflicts = getConflicts(course)
    if not new_conflicts:
        print("No conflicts entered.")
        return

    try:
        # Reassign (not .append) so Pydantic's validate_assignment actually runs.
        course.conflicts = course.conflicts + new_conflicts
        print("Conflict(s) successfully added")
    except Exception as e:
        print(f"Error occurred while adding conflict(s): {e}")
        print("Conflict(s) were not added.")
        print("Commands:\n  (r)etry\n  (c)onflict menu\n")
        choice = input()
        while choice not in ["r", "c"]:
            print("INVALID COMMAND.\n  (r)etry\n  (c)onflict menu\n")
            choice = input()
        if choice == "r":
            add_conflict(course)
        else:
            return


def delete_conflict(course):
    """Delete one existing conflict from the given course."""
    if not course.conflicts:
        print(f"{course.course_id} has no conflicts to delete.")
        return

    print(f"DELETE CONFLICT — {course.course_id}")
    index = getConflictIndexToDelete(course)
    deleted = course.conflicts[index]

    try:
        course.conflicts = [c for c in course.conflicts if c != deleted]
        print(f"Deleted conflict: {deleted}")
        print("Conflict(s) successfully deleted")
    except Exception as e:
        print(f"Error occurred while deleting conflict: {e}")
        print("Conflict was not deleted.")


def view_conflicts(course):
    """Print the current conflict list for the given course."""
    print(f"CONFLICTS for {course.course_id}: {course.conflicts or 'none'}")


def modify_conflicts(course):
    """
    Entry point for the conflict submenu, called by modify_course() once a
    course has been selected, e.g.:

        elif choice == N:  # "conflict"
            modify_conflicts(selected_course)
    """
    print(f"MODIFY CONFLICTS — {course.course_id}")
    print("1. Add a conflict")
    print("2. Delete a conflict")
    print("3. View conflicts")

    try:
        choice = int(input("Enter the number of the option: "))
    except ValueError:
        print("Invalid input. Please enter a number.")
        return modify_conflicts(course)

    if choice == 1:
        add_conflict(course)
    elif choice == 2:
        delete_conflict(course)
    elif choice == 3:
        view_conflicts(course)
    else:
        print("Invalid selection.")