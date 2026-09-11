from dataclasses import dataclass, field
from typing import Callable, Optional
from config import add_faculty, modify_faculty, delete_faculty, view_faculty


@dataclass(frozen=True)
class Command:

    aliases: tuple[str, ...]
    description: str
    action: Callable

    # reads input as "first letter of user input" and "full word of user input"
    @classmethod
    def parse(cls, spec: str, description: str, action: Callable) -> "Command":
        return cls(tuple(spec.split("|")), description, action)

    # checks whether input is valid
    def matches(self, user_input: str) -> bool:
        return user_input in self.aliases

    # displays options for user input as (letter)word 
    # ex: c(onfig)
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


def config():
    return Page("config", [
        Command.parse("c|create", "create new configuration", create),
        Command.parse("l|load", "load a configuration", load),
        Command.parse("h|home", "go to home page", home),
    ])


def create():
    return Page("create", [
        Command.parse("f|faculty", "add faculty", faculty),
        Command.parse("c|courses", "add course", courses),
        Command.parse("l|labs", "add lab", labs),
        Command.parse("r|rooms", "add room", rooms),
        Command.parse("h|home", "go to home page", home),
    ])


def load():
    return Page("load", [
        Command.parse("f|faculty", "load faculty", faculty),
        Command.parse("c|courses", "load course", courses),
        Command.parse("l|labs", "load lab", labs),
        Command.parse("r|rooms", "load room", rooms),
        Command.parse("h|home", "go to home page", home),
    ])

#FACULTY FUNCTIONS
def faculty():
    return Page(
        "faculty",
        [Command.parse("a|add", "add faculty", add_faculty),
        Command.parse("m|modify", "modify faculty", modify_faculty),
        Command.parse("d|delete", "delete faculty", delete_faculty),
        Command.parse("v|view", "view faculty", view_faculty),
        Command.parse("h|home", "go to home page", home)]
    )


def courses():
    return Page(
        "courses",
        {}
    )

def labs():
    return Page(
        "labs",
        {}
    )


def rooms():
    return Page(
        "labs",
        {}
    )


def schedule():
    return Page(
        "schedule",
        {}
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

        # check if user input requires global command
        global_command = find_global(user_input)
        if global_command is not None:
            result = global_command.action(current_page, history)
            if result is None:
                break
            current_page = result
            continue

        # check for invalid commands
        command = current_page.find(user_input)
        if command is None:
            print("Invalid command.")
            continue

        # navigate pages
        # tracks history and current page for back and command options
        history.append(current_page)

        result = command.action()

        if result is not None:
            current_page = result
        else:
            current_page = history.pop()

if __name__ == "__main__":
    main()