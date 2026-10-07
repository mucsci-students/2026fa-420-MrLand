from src.services.faculty_service import (
    add_faculty_from_values,
    delete_faculty_from_values,
    update_faculty_from_values,
)


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
    ):
        return update_faculty_from_values(
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

    @staticmethod
    def delete_member(faculty_members, member_to_delete):
        return delete_faculty_from_values(faculty_members, member_to_delete)
