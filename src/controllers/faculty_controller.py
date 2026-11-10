"""GUI controller for faculty updates.

Used by: GUI."""

from src.controllers.faculty_operations_controller import (
    add_faculty_from_values,
    delete_faculty_from_values,
    update_faculty_from_values,
)
from src.models.configuration_observer import ConfigurationSubject, EntityChangeEvent


class FacultyController:
    """Coordinate faculty CRUD for GUI views without leaking service details."""

    @staticmethod
    def add_member(
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
        return add_faculty_from_values(
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

    @staticmethod
    def update_member(
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
        change_subject: ConfigurationSubject | None = None,
    ):
        old_name = existing_member.name
        updated_member = update_faculty_from_values(
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
        )
        if updated_member.name != old_name and change_subject is not None:
            change_subject.notify(
                EntityChangeEvent("faculty", "renamed", old_name, updated_member.name)
            )
        return updated_member

    @staticmethod
    def delete_member(
        faculty_members,
        member_to_delete,
        change_subject: ConfigurationSubject | None = None,
    ):
        old_name = member_to_delete.name
        deleted_member = delete_faculty_from_values(faculty_members, member_to_delete)
        if change_subject is not None:
            change_subject.notify(EntityChangeEvent("faculty", "deleted", old_name))
        return deleted_member
