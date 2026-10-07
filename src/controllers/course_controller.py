from src.services.course_service import (
    add_course_from_values,
    delete_course_from_values,
    update_course_from_values,
)


class CourseController:
    """Coordinate course CRUD for GUI views without leaking service details."""

    @staticmethod
    def add_course(
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
        return add_course_from_values(
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

    @staticmethod
    def update_course(
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
        return update_course_from_values(
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
        )

    @staticmethod
    def delete_course(course_members, course_to_delete):
        return delete_course_from_values(course_members, course_to_delete)
