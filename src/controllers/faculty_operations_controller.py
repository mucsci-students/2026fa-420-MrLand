"""Non-interactive faculty operations with legacy console-name re-exports."""

from scheduler.config import FacultyConfig


def _build_faculty_from_values(
    faculty_members,
    name,
    maximum_credits,
    minimum_credits,
    unique_course_limit,
    times,
    maximum_days,
    course_preferences,
    room_preferences,
    lab_preferences,
    mandatory_days,
    exclude=None,
):
    name = name.strip()
    if not name:
        raise ValueError("Name cannot be empty.")
    if any(
        member is not exclude and member.name.lower() == name.lower() for member in faculty_members
    ):
        raise ValueError("Faculty member already exists.")

    return FacultyConfig(
        name=name,
        maximum_credits=maximum_credits,
        minimum_credits=minimum_credits,
        unique_course_limit=unique_course_limit,
        times=times,
        maximum_days=maximum_days,
        course_preferences=course_preferences,
        room_preferences=room_preferences,
        lab_preferences=lab_preferences,
        mandatory_days=mandatory_days,
    )


def add_faculty_from_values(
    faculty_members,
    name,
    maximum_credits,
    minimum_credits,
    unique_course_limit,
    times,
    maximum_days,
    course_preferences,
    room_preferences,
    lab_preferences,
    mandatory_days,
):
    """Validate and append faculty data supplied by a non-interactive caller."""
    faculty_member = _build_faculty_from_values(
        faculty_members,
        name,
        maximum_credits,
        minimum_credits,
        unique_course_limit,
        times,
        maximum_days,
        course_preferences,
        room_preferences,
        lab_preferences,
        mandatory_days,
    )
    faculty_members.append(faculty_member)
    return faculty_member


def update_faculty_from_values(
    faculty_members,
    existing_member,
    name,
    maximum_credits,
    minimum_credits,
    unique_course_limit,
    times,
    maximum_days,
    course_preferences,
    room_preferences,
    lab_preferences,
    mandatory_days,
):
    """Replace a faculty member after validating all replacement values."""
    if not any(member is existing_member for member in faculty_members):
        raise ValueError("Faculty member no longer exists.")

    updated_member = _build_faculty_from_values(
        faculty_members,
        name,
        maximum_credits,
        minimum_credits,
        unique_course_limit,
        times,
        maximum_days,
        course_preferences,
        room_preferences,
        lab_preferences,
        mandatory_days,
        exclude=existing_member,
    )
    existing_member.name = updated_member.name
    existing_member.maximum_credits = updated_member.maximum_credits
    existing_member.minimum_credits = updated_member.minimum_credits
    existing_member.unique_course_limit = updated_member.unique_course_limit
    existing_member.times = updated_member.times
    existing_member.maximum_days = updated_member.maximum_days
    existing_member.course_preferences = updated_member.course_preferences
    existing_member.room_preferences = updated_member.room_preferences
    existing_member.lab_preferences = updated_member.lab_preferences
    existing_member.mandatory_days = updated_member.mandatory_days
    return existing_member


def delete_faculty_from_values(faculty_members, member_to_delete):
    """Remove and return a selected faculty member by object identity."""
    try:
        index = next(i for i, member in enumerate(faculty_members) if member is member_to_delete)
    except StopIteration as exc:
        raise ValueError("Faculty member no longer exists.") from exc
    return faculty_members.pop(index)


from src.controllers.faculty_cli_controller import (
    add_faculty,
    course_preference_getter,
    delete_faculty,
    faculty_times,
    get_course_limit,
    get_max_credits,
    get_max_days,
    get_min_credits,
    get_name,
    lab_preference_getter,
    mandatory_days_getter,
    modify_faculty,
    room_preference_getter,
    view_faculty,
    view_faculty_names,
)

__all__ = [
    "add_faculty",
    "add_faculty_from_values",
    "course_preference_getter",
    "delete_faculty",
    "delete_faculty_from_values",
    "faculty_times",
    "get_course_limit",
    "get_max_credits",
    "get_max_days",
    "get_min_credits",
    "get_name",
    "lab_preference_getter",
    "mandatory_days_getter",
    "modify_faculty",
    "room_preference_getter",
    "update_faculty_from_values",
    "view_faculty",
    "view_faculty_names",
]
