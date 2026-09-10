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
            "1":("config", config),
            "2":("schedule", schedule)
        }
    )


def config():
    return Page(
        "config",
        {
            "1": ("faculty", faculty),
            "2": ("courses", courses),
            "3": ("labs", labs),
            "4": ("rooms", rooms),
        }
    )

def create():
    return Page(
        "create",
        {
            
        }
    )

def load():
    return Page(
        "load",
        {
        }
    )

def faculty():
    return Page(
        "faculty",
        {

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



def main():
    print("Type 'help' for commands, exit to quit")
    currentPage = home()
    history = []
    while True:
        print(f"\n=== {currentPage.name.upper()} ===")

        # Dynamic help
        print("\nCommands:")

        for command, (description, _) in currentPage.commands.items():
            print(f"  {command} - {description}")

        print("back: go back")
        print("exit: quit")

        command = input("\n> ").strip().lower()

        if command == "exit":
            print("Goodbye!")
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
