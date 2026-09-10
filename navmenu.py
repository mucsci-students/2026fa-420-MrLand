from dataclasses import dataclass
from typing import Callable

@dataclass
class Page:
    name: str
    commands: dict[str, tuple[str, Callable]]

# individual menus
def home():
    return Page(
        "home",
        {
            "config":("add or load a configuration", config),
            "schedule":("", schedule)
        }
    )


def config():
    return Page(
        "config",
        {
            "create": ("create new configuration", create),
            "load": ("load a configuration", load),
            "home": ("go to home page", home)
        }
    )

def create():
    return Page(
        "create",
        {
            "faculty": ("add faculty", faculty),
            "courses": ("add course", courses),
            "labs": ("add lab", labs),
            "rooms": ("add room", rooms),
            "home": ("go to home page", home)
        }
    )

def load():
    return Page(
        "load",
        {
            "faculty": ("load faculty", faculty),
            "courses": ("load course", courses),
            "labs": ("load lab", labs),
            "rooms": ("load room", rooms)
        }
    )

def faculty():
    return Page(
        "faculty",
        {
            # import from another file?
        }
    )


def courses():
    return Page(
        "courses",
        {

        }
    )


def labs():
    return Page(
        "labs",
        {

        }
    )


def rooms():
    return Page(
        "rooms",
        {

        }
    )

def schedule():
    return Page(
        "schedule",
    )

# Global commands always accessible




def main():
    print("Type 'help' for commands, exit to quit")
    currentPage = home()
    history = []
    while True:
        print(f"{currentPage.name.upper()}")

        # Dynamic help
        print("\nCommands:")

        for command, (description, _) in currentPage.commands.items():
            print(f"  {command}: {description}")

        print("  back: go back")
        print("  exit: quit")

        command = input("\n> ").strip().lower()

        if command == "exit":
            print("Exited the Program")
            break

        if command == "back":
            if history:
                currentPage = history.pop()
            else:
                print("Already at home.")
            continue

        if command not in currentPage.commands:
            print("Invalid command.")
            continue

        history.append(currentPage)

        _, nextPage = currentPage.commands[command]
        currentPage = nextPage()

if __name__ == "__main__":
    main()
