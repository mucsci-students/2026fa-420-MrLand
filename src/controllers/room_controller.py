from src.services.rooms_service import (
    add_room_from_values,
    delete_room_from_values,
    update_room_from_values,
)


class RoomController:
    """Coordinate room CRUD for GUI views without leaking service details."""

    @staticmethod
    def add_room(rooms, name, capacity, features, availability):
        return add_room_from_values(rooms, name, capacity, features, availability)

    @staticmethod
    def update_room(rooms, existing_room, name, capacity, features, availability):
        return update_room_from_values(
            rooms,
            existing_room,
            name,
            capacity,
            features,
            availability,
        )

    @staticmethod
    def delete_room(rooms, room_to_delete):
        return delete_room_from_values(rooms, room_to_delete)
