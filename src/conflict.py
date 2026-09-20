# conflict.py

# ---- validation helpers -----------------------------------------------

def _is_valid_conflict_candidate(course_id, candidate, courses):
    """True if candidate is a real, different course_id (case-insensitive)."""
    if candidate.lower() == course_id.lower():
        print(f"'{candidate}': a course cannot conflict with itself. Skipped.")
        return False
    if not any(c.course_id.lower() == candidate.lower() for c in courses):
        print(f"Course '{candidate}' does not exist. Skipped.")
        return False
    return True


def _parse_course_ids(raw):
    """Split a comma-separated (or single) entry into a clean id list."""
    return [c.strip() for c in raw.split(",") if c.strip()]


def _find_existing(conflicts, candidate):
    """Case-insensitive lookup of candidate's actual stored value in conflicts."""
    return next((c for c in conflicts if c.lower() == candidate.lower()), None)


# ---- actions (operate on a plain course_id + conflicts list) ----------

def add_conflicts(course_id, conflicts, courses):
    """Add one or more new conflicts. Accepts a single course number or a
    comma-separated list. Skips invalid or already-present entries."""
    raw = input("Enter course(s) to add as conflicts (comma-separated): ").strip()
    if not raw:
        print("No conflicts added.")
        return conflicts

    added = []
    for candidate in _parse_course_ids(raw):
        if not _is_valid_conflict_candidate(course_id, candidate, courses):
            continue
        if _find_existing(conflicts, candidate) is not None:
            print(f"'{candidate}' is already a conflict for this course.")
            continue
        conflicts.append(candidate)
        added.append(candidate)

    print(f"Added conflict(s): {added}" if added else "No conflicts added.")
    return conflicts


def delete_conflicts(course_id, conflicts):
    """Delete one or more existing conflicts. Accepts a single course
    number or a comma-separated list."""
    if not conflicts:
        print(f"{course_id} has no conflicts to delete.")
        return conflicts

    raw = input("Enter course(s) to remove as conflicts (comma-separated): ").strip()
    if not raw:
        print("No conflicts removed.")
        return conflicts

    removed = []
    for candidate in _parse_course_ids(raw):
        match = _find_existing(conflicts, candidate)
        if match is None:
            print(f"'{candidate}' is not currently a conflict for this course.")
            continue
        conflicts.remove(match)
        removed.append(match)

    print(f"Removed conflict(s): {removed}" if removed else "No conflicts removed.")
    return conflicts


def toggle_conflicts(course_id, conflicts, courses):
    """Modify conflicts by toggling presence. Accepts a single course
    number or a comma-separated list: each one is removed if it's already
    a conflict, or added if it isn't (after the usual validation)."""
    raw = input("Enter course(s) to toggle as conflicts (comma-separated): ").strip()
    if not raw:
        print("No changes made.")
        return conflicts

    for candidate in _parse_course_ids(raw):
        if not _is_valid_conflict_candidate(course_id, candidate, courses):
            continue
        match = _find_existing(conflicts, candidate)
        if match is not None:
            conflicts.remove(match)
            print(f"'{match}' was already a conflict — removed.")
        else:
            conflicts.append(candidate)
            print(f"'{candidate}' was not a conflict — added.")

    return conflicts


def view_conflicts_list(course_id, conflicts):
    """Print the current conflict list for course_id."""
    print(f"CONFLICTS for {course_id}: {conflicts or 'none'}")


# ---- menu ---------------------------------------------------------------

def conflicts_menu(course_id, courses, conflicts=None):
    """Interactive add/modify/delete/view loop for a course's conflicts.

    Works both before a CourseConfig exists -- e.g. courses_service.py's
    add_course() calling `conflicts = conflicts_menu(course_id, courses)`
    while building up a new course -- and after, via modify_conflicts()
    below. Returns the final conflicts list once the user types "done";
    the caller is responsible for persisting it (either passing it
    straight to CourseConfig(...) at creation time, or reassigning
    course.conflicts = ... at modify time so Pydantic's
    validate_assignment runs).
    """
    conflicts = list(conflicts) if conflicts else []

    while True:
        print(f"\nCONFLICTS — {course_id}")
        print(f"Current conflicts: {conflicts or 'none'}")
        print("Options: add, modify, delete, view, done")

        choice = input("Enter an option: ").strip().lower()

        if choice == "add":
            conflicts = add_conflicts(course_id, conflicts, courses)
        elif choice == "modify":
            conflicts = toggle_conflicts(course_id, conflicts, courses)
        elif choice == "delete":
            conflicts = delete_conflicts(course_id, conflicts)
        elif choice == "view":
            view_conflicts_list(course_id, conflicts)
        elif choice == "done":
            return conflicts
        else:
            print("Invalid selection.")


def modify_conflicts(course, courses):
    """
    Entry point for the conflict submenu, called by modify_course() once a
    course has been selected, e.g.:

        elif choice == N:  # "conflict"
            modify_conflicts(selected_course, courses)

    Runs the interactive conflicts_menu() and persists the result back onto
    the course in a single validated reassignment when the user is done.
    """
    updated_conflicts = conflicts_menu(course.course_id, courses, course.conflicts)

    try:
        course.conflicts = updated_conflicts
        print("Conflicts updated successfully")
    except Exception as e:
        print(f"Error occurred while updating conflicts: {e}")
        print("Conflicts were not updated.")