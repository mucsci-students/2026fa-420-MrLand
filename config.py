from pydantic import ValidationError
from scheduler.config import FacultyConfig


faculty_members = []

def coursePreference():
    preferences = []
    while True:
        course = input("Enter course name (or 'done' to finish): ")
        if course.lower() == 'done':
            break
        
        preferences.append(course)
    return preferences

def add_faculty():
    print("ADD NEW FACULTY MEMBER")
    name = input("Enter faculty name: ")
    max_credits = int(input("Enter maximum credits: "))
    min_credits = int(input("Enter minimum credits: "))
    course_limit = int(input("Enter course limit: "))
    max_days = int(input("Enter maximum days: "))


