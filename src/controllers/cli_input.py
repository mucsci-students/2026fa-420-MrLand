"""Shared prompt parsing for the legacy interactive controllers."""


def get_weekday(prompt: str, invalid_message: str) -> str | None:
    """Read a supported weekday, preserving each controller's prompt wording."""
    day = input(prompt).strip().upper()
    if day not in {"MON", "TUE", "WED", "THU", "FRI"}:
        print(invalid_message)
        return None
    return day


def get_integer(prompt: str) -> int:
    """Keep prompting until an integer is entered."""
    while True:
        try:
            return int(input(prompt).strip())
        except ValueError:
            print("Please enter a valid number.")
