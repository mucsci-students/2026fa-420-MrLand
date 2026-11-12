"""Shared course identity checks used by GUI and console operations."""


def course_exists(course_members, course_id, section_id, exclude=None):
    for course in course_members:
        if course is exclude:
            continue

        if course.course_id.lower() == course_id.lower() and course.section_id == section_id:
            return True

    return False
