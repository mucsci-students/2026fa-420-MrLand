"""Validated, non-interactive room operations used by GUI controllers."""

from scheduler.config import RoomConfig, TimeRange


def _build_room_from_values(rooms, name, capacity, features, availability, exclude=None):
    name = name.strip()
    if not name:
        raise ValueError("Room name cannot be empty.")
    if any(room is not exclude and room.name.lower() == name.lower() for room in rooms):
        raise ValueError("Room name already exists.")
    if isinstance(capacity, bool) or not isinstance(capacity, int) or capacity <= 0:
        raise ValueError("Capacity must be a positive integer.")

    times = None
    if availability is not None:
        times = {}
        valid_days = {"MON", "TUE", "WED", "THU", "FRI"}
        for day, ranges in availability.items():
            day = day.upper()
            if day not in valid_days:
                raise ValueError(f"Invalid day: {day}")
            if ranges:
                times[day] = [TimeRange.from_string(value) for value in ranges]

    return RoomConfig(
        name=name,
        capacity=capacity,
        features=features,
        times=times,
    )


def add_room_from_values(rooms, name, capacity, features, availability):
    """Validate and append room values supplied by a non-interactive caller."""
    room = _build_room_from_values(rooms, name, capacity, features, availability)
    rooms.append(room)
    return room


def update_room_from_values(rooms, existing_room, name, capacity, features, availability):
    """Replace an existing room after validating all replacement values."""
    if not any(room is existing_room for room in rooms):
        raise ValueError("Room no longer exists.")

    updated_room = _build_room_from_values(
        rooms, name, capacity, features, availability, exclude=existing_room
    )
    existing_room.name = updated_room.name
    existing_room.capacity = updated_room.capacity
    existing_room.features = updated_room.features
    existing_room.times = updated_room.times
    return existing_room


def delete_room_from_values(rooms, room_to_delete):
    """Remove and return the selected room, or fail if it is no longer present."""
    try:
        index = next(i for i, room in enumerate(rooms) if room is room_to_delete)
    except StopIteration as exc:
        raise ValueError("Room no longer exists.") from exc
    return rooms.pop(index)
