from dataclasses import dataclass
from typing import Callable

# implements system to set up new pages
@dataclass
class Page:
    name: str
    commands: dict[str, tuple[str, Callable]]

# displays the command option in CLI as (letter)word
# where letter is the first letter and word is the rest of the word
def command_display(command: str) -> str:
    aliases = command.split("|")

    if len(aliases) == 1:
        return aliases[0]

    letter = aliases[0]
    word = aliases[-1]

    return f"({letter}){word[len(letter):]}"

# checks user input for letter or full word in a command
def command_matches(command: str, user_input: str) -> bool:
    aliases = command.split("|")
    return user_input in aliases

# Individual Menus

def home():
    return Page(
        "home",
        {
            "c|config": ("add or load a configuration", config),
            "s|schedule": ("", schedule)
        }
    )


def config():
    return Page(
        "config",
        {
            "c|create": ("create new configuration", create),
            "l|load": ("load a configuration", load),
            "h|home": ("go to home page", home)
        }
    )


def create():
    return Page(
        "create",
        {
            "f|faculty": ("add faculty", faculty),
            "c|courses": ("add course", courses),
            "l|labs": ("add lab", labs),
            "r|rooms": ("add room", rooms),
            "h|home": ("go to home page", home)
        }
    )


def load():
    return Page(
        "load",
        {
            "f|faculty": ("load faculty", faculty),
            "c|courses": ("load course", courses),
            "l|labs": ("load lab", labs),
            "r|rooms": ("load room", rooms)
        }
    )

def faculty():
    return Page(
        
    )


def courses():
    return Page(
        
    )


def labs():
    return Page(
        
    )


def rooms():
    return Page(
        
    )


def schedule():
    return Page(
        
    )

# Global Commands

def back(current_page, history):
    if history:
        return history.pop()

    print("Already on home page.")
    return current_page

def quit(current_page, history):
    print("Quit the program")
    return None

global_commands = {
    "b|back": ("go back", back),
    "q|quit": ("exit the program", quit)
}

def main():
    print("Type q to exit")

    current_page = home()
    history = []

    while True:
        print(f"\n{current_page.name.upper()}")
        print("\nCommands:")

        # page commands
        for command, (description, _) in current_page.commands.items():
            display = command_display(command)
            print(f"  {display}: {description}")

        # Global commands
        for command, (description, _) in global_commands.items():
            display = command_display(command)
            print(f"  {display}: {description}")

        command = input("\n> ").strip().lower()
        global_function = None

        # check whether or not to perform global command
        for aliases, (_, function) in global_commands.items():
            if command_matches(aliases, command):
                global_function = function
                break

        if global_function is not None:
            result = global_function(current_page, history)

            if result is None:
                break

            current_page = result
            continue

        next_page = None

        for aliases, (_, page_function) in current_page.commands.items():
            if command_matches(aliases, command):
                next_page = page_function
                break

        # check for invalid commands
        if next_page is None:
            print("Invalid command.")
            continue

        history.append(current_page)

        current_page = next_page()

if __name__ == "__main__":
    main()
