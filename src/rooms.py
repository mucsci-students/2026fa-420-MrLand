from scheduler.config import RoomConfig, TimeRange

rooms = []

def get_room_name():
    while True:                 
        name = input("Enter room name: ").strip()
        if not name:
            print("Room name cannot be empty. Please try again.")
            continue
        if any(room.name.lower() == name.lower() for room in rooms):
            print("Room name already exists. Please try again.")
            continue
        return name


def get_room_capacity():
    while True:
        capacity_str = input("Enter room capacity: ").strip()

        if not capacity_str.isdigit():
            print("Capacity must be a positive integer. Please try again.")
            continue

        capacity = int(capacity_str)

        if capacity <= 0:
            print("Capacity must be greater than zero. Please try again.")
            continue

        return capacity


def get_room_features():
    features = []

    while True:
        feature = input("Enter a feature (or 'done' to finish): ").strip()

        if feature.lower() == "done":
            break

        if feature:
            features.append(feature)

    return features


def get_room_availability():
    availability = {}
    valid_days = ["MON", "TUE", "WED", "THU", "FRI"]

    print("Enter availability entries one at a time.")
    print("Format: DAY HH:MM-HH:MM (e.g., MON 09:00-10:00)")
    print("Type 'done' when finished.")

    while True:
        entry = input("Enter availability: ").strip()

        if entry.lower() == "done":
            break

        parts = entry.split()
        if len(parts) != 2:
            print("Invalid format. Please use the format: DAY HH:MM-HH:MM")
            continue

        day = parts[0].upper()
        time_range = parts[1]

        if day not in valid_days:
            print(f"Invalid day. Please use one of the following: {', '.join(valid_days)}")
            continue

        try:
            validated_range = TimeRange.from_string(time_range)
        except (ValueError, TypeError):
            print("Invalid time range. Use HH:MM-HH:MM with end after start.")
            continue
        
        if day not in availability:
            availability[day] = []
        availability[day].append(validated_range)

    return availability


def add_rooms():
    try:
        room = RoomConfig(
            name=get_room_name(),
            capacity=get_room_capacity(),
            features=get_room_features(),
            times=get_room_availability(),
        )

        rooms.append(room)
        print(f"Room added: {room.name}")

    except Exception as exc:
        print(f"Room validation failed: {exc}")
        return None


def view_rooms():
    if not rooms:
        print("No rooms found.")
        return

    print("ROOMS:")
    for i, room in enumerate(rooms, start=1):
        print(f"{i}. {room.name}")
        print(f"   Capacity: {room.capacity}")
        print(f"   Features: {room.features}")
        print(f"   Availability: {room.times}")


def modify_rooms():
    if not rooms:
        print("No rooms found.")
        return

    view_rooms()
    try:
        index = int(input("Enter the room number to modify: ").strip()) - 1
    except ValueError:
        print("Invalid room number.")
        return

    if index < 0 or index >= len(rooms):
        print("Invalid room number.")
        return

    room = rooms[index]
    print(f"Modifying room: {room.name}")

    print("1. Name")
    print("2. Capacity")
    print("3. Features")
    print("4. Availability")

    try:
        choice = int(input("Select field to change: ").strip())
    except ValueError:
        print("Invalid selection.")
        return

    old_room = room.model_dump()

    try:
        if choice == 1:
            room.name = get_room_name()
        elif choice == 2:
            room.capacity = get_room_capacity()
        elif choice == 3:
            room.features = get_room_features()
        elif choice == 4:
            room.times = get_room_availability()
        else:
            print("Invalid selection.")
            return

        print(f"Room updated: {room.name}")

    except Exception as exc:
        # Restore previous valid state
        rooms[index] = type(room).model_validate(old_room)
        print(f"Update failed: {exc}")
        print("Previous valid room data was restored.")


def delete_rooms():
    if not rooms:
        print("No rooms found.")
        return

    view_rooms()
    try:
        index = int(input("Enter the room number to delete: ").strip()) - 1
    except ValueError:
        print("Invalid room number.")
        return

    if index < 0 or index >= len(rooms):
        print("Invalid room number.")
        return

    deleted = rooms.pop(index)
    print(f"Room deleted: {deleted.name}")
