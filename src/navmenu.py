from dataclasses import dataclass, field
from typing import Callable, Optional
from services.lab_service import add_lab, modify_lab, delete_lab, view_labs
from services.faculty_service import add_faculty, modify_faculty, delete_faculty, view_faculty
from services.rooms_service import add_rooms, modify_rooms, delete_rooms, view_rooms
from services.course_service import add_course, modify_course, delete_course, view_courses
from services.class_pattern_service import (
    add_class_pattern, modify_class_pattern, delete_class_pattern, view_class_patterns,
    add_meeting, modify_meeting, delete_meeting, view_meetings,
)
from services.time_block_service import (
    add_time_block, modify_time_block, delete_time_block, view_time_blocks,
)
import services.config_service as config_service
from run_scheduler import run_scheduler
from services.schedule_service import view_schedules, export_schedules

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
        Command.parse("s|save", "save current config", save_current_config),
        Command.parse("h|home", "go to home page", home),
    ])

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


def schedule():
    return Page(
        "schedule",
        [
            Command.parse("r|run", "run scheduler on a saved config", lambda: run_scheduler(cur_schedules)),
            Command.parse("v|view", "view generated schedules", lambda: view_schedules(cur_schedules)),
            Command.parse("e|export", "export schedules to csv", lambda: export_schedules(cur_schedules)),
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