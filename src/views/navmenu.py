"""Interactive text menu for configuration and schedule workflows.

Used by: CLI."""

from dataclasses import dataclass, field
from pathlib import Path
import sys
from typing import Callable, Optional

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.controllers.lab_operations_controller import add_lab, modify_lab, delete_lab, view_labs
from src.controllers.faculty_operations_controller import add_faculty, modify_faculty, delete_faculty, view_faculty
from src.controllers.room_operations_controller import add_rooms, modify_rooms, delete_rooms, view_rooms
from src.controllers.course_operations_controller import add_course, modify_course, delete_course, view_courses
from src.controllers.class_pattern_operations_controller import (
    add_class_pattern, modify_class_pattern, delete_class_pattern, view_class_patterns,
    add_meeting, modify_meeting, delete_meeting, view_meetings,
)
from src.controllers.time_block_operations_controller import (
    add_time_block, modify_time_block, delete_time_block, view_time_blocks,
)
import src.models.configuration_model as config_service
from src.controllers.run_scheduler_controller import confirm_yes_no, run_scheduler
from src.models.schedule_files import records_from_result
from src.models.schedule_viewer_model import ScheduleViewerModel
import src.controllers.settings_operations_controller as settings_service
import src.controllers.time_slot_settings_operations_controller as time_slot_settings_service

current_config = None
config_name = None
cur_schedules = []

@dataclass(frozen=True)
class Command:

    aliases: tuple[str, ...]
    description: str
    action: Callable

    @classmethod
    def parse(cls, spec: str, description: str, action: Callable) -> "Command":
        return cls(tuple(spec.split("|")), description, action)

    def matches(self, user_input: str) -> bool:
        return user_input in self.aliases

    def display(self) -> str:
        if len(self.aliases) == 1:
            return self.aliases[0]

        letter, word = self.aliases[0], self.aliases[-1]
        return f"({letter}){word[len(letter):]}"


@dataclass
class Page:
    name: str
    commands: list[Command] = field(default_factory=list)

    def find(self, user_input: str) -> Optional[Command]:
        for command in self.commands:
            if command.matches(user_input):
                return command
        return None

# Individual menus

def home():
    return Page("home", [
        Command.parse("c|config", "add or load a configuration", config),
        Command.parse("s|schedule", "build a class schedule", schedule),
    ])


def reset_config_state():
    global current_config, config_name
    current_config = None
    config_name = None


def config():
    return Page("config", [
        Command.parse("c|create", "create new configuration", create),
        Command.parse("l|load", "load a configuration", load_get_name),
        Command.parse("h|home", "go to home page", home),
    ])


def create():
    global current_config, config_name

    name = input("Please enter a name for the configuration: ")
    if not name.strip():
        print("Configuration name cannot be empty.")
        return create()

    current_config = config_service.create_draft_config()
    config_name = name
    print(f"Configuration '{name}' created. Add rooms, courses, and faculty before saving.")
    return config_dashboard()


def load_get_name():
    global current_config, config_name

    file_name = input("Please enter the name of the configuration: ")
    try:
        current_config = config_service.load_config(file_name)
        config_name = file_name
        print(f"Configuration '{file_name}' loaded successfully.")
    except FileNotFoundError as e:
        print(e)
        return config()

    return config_dashboard()


def save_current_config():
    config_service.save_config(current_config, config_name)
    return None


def config_dashboard():
    return Page("Configuration Dashboard", [
        Command.parse("f|faculty", "faculty", faculty),
        Command.parse("c|courses", "load course", courses),
        Command.parse("l|labs", "load lab", labs),
        Command.parse("r|rooms", "load room", rooms),
        Command.parse("t|timeslots", "manage time blocks and class patterns", time_slots),
        Command.parse("g|settings", "manage global settings", settings),
        Command.parse("s|save", "save current config", save_current_config),
        Command.parse("h|home", "go to home page", home),
    ])
def settings():
    return Page(
        "global settings",
        [
            Command.parse("v|view", "view global settings", lambda: settings_service.view_settings(current_config)),
            Command.parse("m|modify", "modify global settings", lambda: settings_service.modify_settings(current_config)),
            Command.parse("r|reset", "reset global settings", lambda: settings_service.reset_settings(current_config)),
            Command.parse("h|home", "go to home page", home),
        ]
    )
#FACULTY FUNCTIONS
def faculty():
    return Page(
        "faculty",
        [Command.parse("a|add", "add faculty", lambda: add_faculty(current_config.config.faculty)),
        Command.parse("m|modify", "modify faculty", lambda: modify_faculty(current_config.config.faculty)),
        Command.parse("d|delete", "delete faculty", lambda: delete_faculty(current_config.config.faculty)),
        Command.parse("v|view", "view faculty", lambda: view_faculty(current_config.config.faculty)),
        Command.parse("h|home", "go to home page", home)]
    )


def courses():
    return Page(
        "courses",
        [
            Command.parse("a|add", "add course", lambda: add_course(current_config.config.courses)),
            Command.parse("m|modify", "modify course", lambda: modify_course(current_config.config.courses)),
            Command.parse("d|delete", "delete course", lambda: delete_course(current_config.config.courses)),
            Command.parse("v|view", "view course", lambda: view_courses(current_config.config.courses)),
            Command.parse("h|home", "go to home page", home),
        ]
    )

def labs():
    return Page(
        "labs",
        [
            Command.parse("a|add", "add lab", lambda: add_lab(current_config.config.labs)),
            Command.parse("m|modify", "modify lab", lambda: modify_lab(current_config.config.labs)),
            Command.parse("d|delete", "delete lab", lambda: delete_lab(current_config.config.labs)),
            Command.parse("v|view", "view lab", lambda: view_labs(current_config.config.labs)),
            Command.parse("h|home", "go to home page", home),
        ]
    )


def rooms():
    return Page(
        "rooms",
        [Command.parse("a|add", "add room", lambda: add_rooms(current_config.config.rooms)),
        Command.parse("m|modify", "modify room", lambda: modify_rooms(current_config.config.rooms)),
        Command.parse("d|delete", "delete room", lambda: delete_rooms(current_config.config.rooms)),
        Command.parse("v|view", "view room", lambda: view_rooms(current_config.config.rooms)),
        Command.parse("h|home", "go to home page", home)]
    )


def time_slots():
    return Page(
        "time slots",
        [
            Command.parse("tb|timeblocks", "manage time blocks", time_blocks),
            Command.parse("cp|classpatterns", "manage class patterns", class_patterns),
            Command.parse("s|settings", "manage time slot settings", time_slot_settings),
            Command.parse("h|home", "go to home page", home),
        ]
    )

def time_blocks():
    return Page(
        "time blocks",
        [
            Command.parse("a|add", "add time block", lambda: add_time_block(current_config.time_slot_config)),
            Command.parse("m|modify", "modify time block", lambda: modify_time_block(current_config.time_slot_config)),
            Command.parse("d|delete", "delete time block", lambda: delete_time_block(current_config.time_slot_config)),
            Command.parse("v|view", "view time blocks", lambda: view_time_blocks(current_config.time_slot_config)),
            Command.parse("h|home", "go to home page", home),
        ]
    )


def class_patterns():
    return Page(
        "class patterns",
        [
            Command.parse("a|add", "add class pattern", lambda: add_class_pattern(current_config.time_slot_config)),
            Command.parse("m|modify", "modify class pattern", lambda: modify_class_pattern(current_config.time_slot_config)),
            Command.parse("d|delete", "delete class pattern", lambda: delete_class_pattern(current_config.time_slot_config)),
            Command.parse("v|view", "view class patterns", lambda: view_class_patterns(current_config.time_slot_config)),
            Command.parse("am|addmeeting", "add meeting", lambda: add_meeting(current_config.time_slot_config)),
            Command.parse("mm|modifymeeting", "modify meeting", lambda: modify_meeting(current_config.time_slot_config)),
            Command.parse("dm|deletemeeting", "delete meeting", lambda: delete_meeting(current_config.time_slot_config)),
            Command.parse("vm|viewmeetings", "view meetings", lambda: view_meetings(current_config.time_slot_config)),
            Command.parse("h|home", "go to home page", home),
        ]
    )
def time_slot_settings():
    return Page(
        "time slot settings",
        [
            Command.parse("v|view", "view time slot settings", lambda: time_slot_settings_service.view_time_slot_settings(current_config.time_slot_config)),
            Command.parse("m|modify", "modify time slot settings", lambda: time_slot_settings_service.modify_time_slot_settings(current_config.time_slot_config)),
            Command.parse("r|reset", "reset time slot settings", lambda: time_slot_settings_service.reset_time_slot_settings(current_config.time_slot_config)),
            Command.parse("h|home", "go to home page", home),
        ]
    )


def view_schedules(schedules):
    if not schedules:
        print("No schedules are available to view.")
        return

    for number, result in enumerate(schedules, start=1):
        print(f"\nSchedule {number} — {result.config_name}")
        for record in records_from_result(result):
            details = [
                f"Course: {record['course']}",
                f"Faculty: {record['faculty']}",
                f"Room: {record['room'] or 'N/A'}",
                f"Lab: {record['lab'] or 'N/A'}",
                f"Times: {record['times']}",
            ]
            print("  " + " | ".join(details))


def export_schedules(schedules):
    model = ScheduleViewerModel()
    model.set_generated(schedules)
    entries = model.entries
    if not entries:
        print("No schedules are available to export.")
        return

    print("Schedules:")
    for number, entry in enumerate(entries, start=1):
        print(f"  {number}. {entry.label}")

    while True:
        choice = input("Select a schedule to export (or q to cancel): ").strip().lower()
        if choice == "q":
            return
        try:
            selected = int(choice) - 1
        except ValueError:
            print("Enter a schedule number or q.")
            continue
        if 0 <= selected < len(entries):
            break
        print(f"Choose a number from 1 to {len(entries)}.")

    file_format = input("Export format (csv/json): ").strip().lower()
    if file_format not in {"csv", "json"}:
        print("Please choose CSV or JSON.")
        return

    entry = entries[selected]
    default_name = model.default_export_file_name(entry, file_format)
    file_name = input(f"File name [{default_name}]: ").strip()
    try:
        content, safe_name, _media_type = model.export(entry, file_format, file_name)
        model.directory.mkdir(parents=True, exist_ok=True)
        path = model.directory / safe_name
        if path.exists() and not confirm_yes_no(f"'{safe_name}' already exists. Overwrite it?"):
            return
        path.write_bytes(content)
    except (OSError, ValueError) as error:
        print(f"Could not export schedule: {error}")
        return

    print(f"Schedule exported to {path}.")


def schedule():
    return Page(
        "schedule",
        [
            Command.parse("r|run", "run scheduler on a saved config", lambda: run_scheduler(cur_schedules)),
            Command.parse("v|view", "view generated schedules", lambda: view_schedules(cur_schedules)),
            Command.parse("e|export", "export schedules to csv or json", lambda: export_schedules(cur_schedules)),
            Command.parse("h|home", "go to home page", home),
        ]
    )

# Global commands

def go_back(current_page: Page, history: list[Page]) -> Page:
    if history:
        return history.pop()

    print("Already on home page.")
    return current_page


def quit_program(current_page: Page, history: list[Page]) -> None:
    print("Quit the program")
    return None

GLOBAL_COMMANDS = [
    Command.parse("b|back", "go back", go_back),
    Command.parse("q|quit", "exit the program", quit_program),
]


def find_global(user_input: str) -> Optional[Command]:
    for command in GLOBAL_COMMANDS:
        if command.matches(user_input):
            return command
    return None


def print_menu(page: Page) -> None:
    print(f"\n{page.name.upper()}")
    print("\nCommands:")

    for command in page.commands:
        print(f"  {command.display()}: {command.description}")

    for command in GLOBAL_COMMANDS:
        print(f"  {command.display()}: {command.description}")


def main():
    print("Type q to exit")

    current_page = home()
    history: list[Page] = []

    while True:
        print_menu(current_page)
        user_input = input("\n> ").strip().lower()

        global_command = find_global(user_input)
        if global_command is not None:
            result = global_command.action(current_page, history)
            if result is None:
                break
            current_page = result
            if current_page.name == "home":
                reset_config_state()
            continue

        command = current_page.find(user_input)
        if command is None:
            print("Invalid command.")
            continue

        history.append(current_page)
        result = command.action()

        if result is not None:
            current_page = result
        else:
            current_page = history.pop()

        if current_page.name == "home":
            reset_config_state()

if __name__ == "__main__":
    main()
