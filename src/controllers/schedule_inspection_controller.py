# File name: schedule_filters_controller.py
# Primary Author: Dylan Groff



def get_course_details(config, course_id):
    for course in config.config.courses:
        if course.course_id == course_id:
            return course

    return None


def get_faculty_details(config, faculty_name):
    for faculty in config.config.faculty:
        if faculty.name == faculty_name:
            return faculty


def get_room_details(config, room_name):
    for room in config.config.rooms:
        if room.name == room_name:
            return room


def get_lab_details(config, lab_name):
    for lab in config.config.labs:
        if lab.name == lab_name:
            return lab