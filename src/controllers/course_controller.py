"""GUI controller for course updates.

Used by: GUI."""

from src.controllers.course_operations_controller import (
    add_course_from_values,
    delete_course_from_values,
    update_course_from_values,
)
from src.models.configuration_observer import ConfigurationSubject, EntityChangeEvent


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
        change_subject: ConfigurationSubject | None = None,
    ):
        old_course_id = existing_course.course_id
        updated_course = update_course_from_values(
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
        if updated_course.course_id != old_course_id and change_subject is not None:
            change_subject.notify(
                EntityChangeEvent(
                    "course", "renamed", old_course_id, updated_course.course_id
                )
            )
        return updated_course

    @staticmethod
    def delete_course(
        course_members,
        course_to_delete,
        change_subject: ConfigurationSubject | None = None,
    ):
        old_course_id = course_to_delete.course_id
        deleted_course = delete_course_from_values(course_members, course_to_delete)
        if change_subject is not None:
            change_subject.notify(
                EntityChangeEvent("course", "deleted", old_course_id)
            )
        return deleted_course
