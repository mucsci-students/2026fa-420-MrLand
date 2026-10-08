"""Looks up course, faculty, room, and lab details for schedule inspection.

Used by: GUI."""

# File name: schedule_filters_controller.py
# Primary Author: Dylan Groff


# function used to get course details from the config file based on the course_id
def get_course_details(schedule, course_id):
    for course_instance in schedule:
        if str(course_instance.course) == str(course_id):
            return course_instance.course
        
    return None

# function used to get faculty details from the config file based on the faculty_name
def get_faculty_details(config, faculty_name):
    for faculty in config.config.faculty:
        if faculty.name == faculty_name:
            return faculty

# function used to get room details from the config file based on the room_name
def get_room_details(config, room_name):
    for room in config.config.rooms:
        if room.name == room_name:
            return room

# function used to get lab details from the config file based on the lab_name
def get_lab_details(config, lab_name):
    for lab in config.config.labs:
        if lab.name == lab_name:
            return lab
