"""Non-interactive course operations with legacy console-name re-exports."""

from scheduler.config import CourseConfig

from src.controllers.course_helpers import course_exists


def _build_course_from_values(
    course_members,
    course_id,
    section_id,
    credits,
    capacity,
    modality,
    room,
    lab,
    required_room_features,
    required_lab_features,
    reserve_room_during_lab,
    conflicts,
    faculty,
    exclude=None,
):
    course_id = course_id.strip()
    if not course_id:
        raise ValueError("Course ID cannot be empty.")
    section_id = section_id.strip() if section_id and section_id.strip() else None
    if course_exists(course_members, course_id, section_id, exclude=exclude):
        raise ValueError("That course section already exists.")
    if isinstance(credits, bool) or not isinstance(credits, int) or credits <= 0:
        raise ValueError("Credits must be greater than 0.")
    if isinstance(capacity, bool) or not isinstance(capacity, int) or capacity <= 0:
        raise ValueError("Capacity must be greater than 0.")
    if modality not in {"in_person", "online", "hybrid"}:
        raise ValueError("Modality must be in_person, online, or hybrid.")

    room = list(room or [])
    lab = list(lab or [])
    required_room_features = set(required_room_features or [])
    required_lab_features = set(required_lab_features or [])
    if modality == "online":
        room = []
        lab = []
        required_room_features = set()
        required_lab_features = set()
        reserve_room_during_lab = False
    else:
        if not room or any(not name.strip() for name in room):
            raise ValueError("At least one room must be entered.")
        if len(room) != len(set(room)):
            raise ValueError("Duplicate rooms are not allowed.")
        if any(not name.strip() for name in lab):
            raise ValueError("Lab names cannot be empty.")
        if len(lab) != len(set(lab)):
            raise ValueError("Duplicate labs are not allowed.")

    if any(not feature.strip() for feature in required_room_features):
        raise ValueError("Room feature names cannot be empty.")
    if any(not feature.strip() for feature in required_lab_features):
        raise ValueError("Lab feature names cannot be empty.")

    conflicts = list(conflicts or [])
    if any(not conflict.strip() for conflict in conflicts):
        raise ValueError("Conflict names cannot be empty.")
    if len(conflicts) != len(set(conflicts)):
        raise ValueError("Duplicate conflicts are not allowed.")
    for conflict in conflicts:
        if conflict.lower() == course_id.lower():
            raise ValueError("A course cannot conflict with itself.")
        if not any(
            course.course_id.lower() == conflict.lower()
            for course in course_members
            if course is not exclude
        ):
            raise ValueError(f"Course '{conflict}' does not exist.")

    if faculty is not None:
        faculty = list(faculty)
        if any(not person.strip() for person in faculty):
            raise ValueError("Faculty names cannot be empty.")
        if len(faculty) != len(set(faculty)):
            raise ValueError("Duplicate faculty members are not allowed.")

    return CourseConfig(
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


def add_course_from_values(
    course_members,
    course_id,
    section_id,
    credits,
    capacity,
    modality,
    room,
    lab,
    required_room_features,
    required_lab_features,
    reserve_room_during_lab,
    conflicts,
    faculty,
):
    """Validate and append course values supplied by a non-interactive caller."""
    course = _build_course_from_values(
        course_members,
        course_id,
        section_id,
        credits,
        capacity,
        modality,
        room,
        lab,
        required_room_features,
        required_lab_features,
        reserve_room_during_lab,
        conflicts,
        faculty,
    )
    course_members.append(course)
    return course


def update_course_from_values(
    course_members,
    existing_course,
    course_id,
    section_id,
    credits,
    capacity,
    modality,
    room,
    lab,
    required_room_features,
    required_lab_features,
    reserve_room_during_lab,
    conflicts,
    faculty,
):
    """Replace a course after validating its complete replacement values."""
    if not any(course is existing_course for course in course_members):
        raise ValueError("Course no longer exists.")

    updated_course = _build_course_from_values(
        course_members,
        course_id,
        section_id,
        credits,
        capacity,
        modality,
        room,
        lab,
        required_room_features,
        required_lab_features,
        reserve_room_during_lab,
        conflicts,
        faculty,
        exclude=existing_course,
    )
    existing_course.course_id = updated_course.course_id
    existing_course.section_id = updated_course.section_id
    existing_course.credits = updated_course.credits
    existing_course.capacity = updated_course.capacity
    existing_course.modality = updated_course.modality
    existing_course.room = updated_course.room
    existing_course.lab = updated_course.lab
    existing_course.required_room_features = updated_course.required_room_features
    existing_course.required_lab_features = updated_course.required_lab_features
    existing_course.reserve_room_during_lab = updated_course.reserve_room_during_lab
    existing_course.conflicts = updated_course.conflicts
    existing_course.faculty = updated_course.faculty
    return existing_course


def delete_course_from_values(course_members, course_to_delete):
    """Remove and return a selected course by object identity."""
    try:
        index = next(i for i, course in enumerate(course_members) if course is course_to_delete)
    except StopIteration as exc:
        raise ValueError("Course no longer exists.") from exc
    return course_members.pop(index)


from src.controllers.course_cli_controller import (
    add_course,
    delete_course,
    get_capacity,
    get_conflicts,
    get_course_id,
    get_credits,
    get_faculty,
    get_lab,
    get_modality,
    get_required_lab_features,
    get_required_room_features,
    get_reserve_room,
    get_room,
    get_section_id,
    modify_course,
    view_courses,
)

__all__ = [
    "add_course",
    "add_course_from_values",
    "course_exists",
    "delete_course",
    "delete_course_from_values",
    "get_capacity",
    "get_conflicts",
    "get_course_id",
    "get_credits",
    "get_faculty",
    "get_lab",
    "get_modality",
    "get_required_lab_features",
    "get_required_room_features",
    "get_reserve_room",
    "get_room",
    "get_section_id",
    "modify_course",
    "update_course_from_values",
    "view_courses",
]
