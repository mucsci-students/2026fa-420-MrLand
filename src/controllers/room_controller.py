"""GUI controller for room updates.

Used by: GUI."""

from src.controllers.room_operations_controller import (
    add_room_from_values,
    delete_room_from_values,
    update_room_from_values,
)
from src.models.configuration_observer import ConfigurationSubject, EntityChangeEvent


class RoomController:
    """Coordinate room CRUD for GUI views without leaking service details."""

    @staticmethod
    def add_room(rooms, name, capacity, features, availability):
        return add_room_from_values(rooms, name, capacity, features, availability)

    @staticmethod
    def update_room(
        rooms,
        existing_room,
        name,
        capacity,
        features,
        availability,
        change_subject: ConfigurationSubject | None = None,
    ):
        old_name = existing_room.name
        updated_room = update_room_from_values(
            rooms,
            existing_room,
            name,
            capacity,
            features,
            availability,
        )
        if updated_room.name != old_name and change_subject is not None:
            change_subject.notify(
                EntityChangeEvent("room", "renamed", old_name, updated_room.name)
            )
        return updated_room

    @staticmethod
    def delete_room(
        rooms,
        room_to_delete,
        change_subject: ConfigurationSubject | None = None,
    ):
        old_name = room_to_delete.name
        deleted_room = delete_room_from_values(rooms, room_to_delete)
        if change_subject is not None:
            change_subject.notify(EntityChangeEvent("room", "deleted", old_name))
        return deleted_room
