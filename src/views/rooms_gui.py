from nicegui import ui

from src.services.rooms_service import (
    add_room_from_values,
    delete_room_from_values,
    update_room_from_values,
)


def _availability_text(times) -> str:
    if times is None:
        return "Unrestricted"
    if not times:
        return "None specified"
    return "; ".join(
        f"{day}: {', '.join(f'{item.start}-{item.end}' for item in ranges)}"
        for day, ranges in times.items()
    )


def rooms_gui(rooms: list) -> None:
    ui.label("Rooms").classes("text-xl font-semibold text-white")
    ui.label("Add a room and its scheduling constraints.").classes(
        "text-sm text-[#9fb2b8]"
    )

    with ui.row().classes("w-full flex-wrap gap-4"):
        name = ui.input("Room name").classes("min-w-56 flex-1")
        capacity = ui.number("Capacity", value=1, min=1, step=1).classes("w-40")
        features = ui.input(
            "Features", placeholder="Projector, whiteboard"
        ).classes("min-w-56 flex-1")

    unrestricted = ui.checkbox("Unrestricted availability", value=True).classes(
        "text-[#d8e7e8]"
    )
    availability_fields = {}
    with ui.grid(columns=2).classes("w-full gap-3"):
        for day in ("MON", "TUE", "WED", "THU", "FRI"):
            availability_fields[day] = ui.input(
                f"{day} availability",
                placeholder="09:00-12:00, 13:00-17:00",
            ).classes("w-full")

    def set_availability_enabled(event) -> None:
        for field in availability_fields.values():
            field.set_enabled(not event.value)

    unrestricted.on_value_change(set_availability_enabled)
    for field in availability_fields.values():
        field.set_enabled(False)

    editing_room = {"room": None}

    def form_values():
        capacity_value = capacity.value
        if capacity_value is None or not float(capacity_value).is_integer():
            raise ValueError("Capacity must be a positive integer.")

        availability = None
        if not unrestricted.value:
            availability = {
                day: [
                    value.strip()
                    for value in field.value.split(",")
                    if value.strip()
                ]
                for day, field in availability_fields.items()
            }

        parsed_features = [
            feature.strip()
            for feature in (features.value or "").split(",")
            if feature.strip()
        ]
        return name.value or "", int(capacity_value), parsed_features, availability

    def reset_form() -> None:
        editing_room["room"] = None
        name.value = ""
        capacity.value = 1
        features.value = ""
        unrestricted.value = True
        for field in availability_fields.values():
            field.value = ""
        add_button.set_visibility(True)
        update_button.set_visibility(False)
        cancel_button.set_visibility(False)

    def add_room() -> None:
        try:
            add_room_from_values(rooms, *form_values())
        except (TypeError, ValueError) as exc:
            ui.notify(str(exc), type="negative")
            return
        reset_form()
        refresh_rooms()
        ui.notify("Room added.", type="positive")

    def update_room() -> None:
        try:
            update_room_from_values(
                rooms, editing_room["room"], *form_values()
            )
        except (TypeError, ValueError) as exc:
            ui.notify(str(exc), type="negative")
            return
        reset_form()
        refresh_rooms()
        ui.notify("Room updated.", type="positive")

    def begin_edit(room) -> None:
        editing_room["room"] = room
        name.value = room.name
        capacity.value = room.capacity
        features.value = ", ".join(sorted(room.features))
        unrestricted.value = room.times is None
        for day, field in availability_fields.items():
            field.value = ", ".join(
                f"{item.start}-{item.end}"
                for item in (room.times or {}).get(day, [])
            )
        add_button.set_visibility(False)
        update_button.set_visibility(True)
        cancel_button.set_visibility(True)

    def delete_room(room, dialog) -> None:
        try:
            delete_room_from_values(rooms, room)
        except ValueError as exc:
            ui.notify(str(exc), type="negative")
            dialog.close()
            return
        if editing_room["room"] is room:
            reset_form()
        ui.notify("Room deleted.", type="positive")
        dialog.close()
        refresh_rooms()

    def refresh_rooms() -> None:
        room_list.clear()
        with room_list:
            if not rooms:
                ui.label("No rooms added yet.").classes("text-sm text-[#9fb2b8]")
                return
            for room in rooms:
                with ui.row().classes(
                    "w-full items-center justify-between gap-4 border-b border-[#29404b] py-3"
                ):
                    with ui.column().classes("min-w-0 gap-1"):
                        ui.label(room.name).classes("font-semibold text-white")
                        details = (
                            f"Capacity: {room.capacity}  |  "
                            f"Features: {', '.join(sorted(room.features)) or 'None'}  |  "
                            f"{_availability_text(room.times)}"
                        )
                        ui.label(details).classes("break-words text-sm text-[#9fb2b8]")
                    with ui.row().classes("shrink-0 items-center gap-1"):
                        ui.button(
                            icon="edit",
                            on_click=lambda selected=room: begin_edit(selected),
                        ).props("flat round dense").tooltip("Edit room")
                        with ui.dialog() as dialog, ui.card().classes(
                            "border border-[#29404b] bg-[#182630]"
                        ):
                            ui.label(f"Delete {room.name}?").classes(
                                "text-lg font-semibold text-white"
                            )
                            ui.label("This cannot be undone.").classes(
                                "text-sm text-[#9fb2b8]"
                            )
                            with ui.row().classes("mt-4 w-full justify-end gap-2"):
                                ui.button("Cancel", on_click=dialog.close).props("flat")
                                ui.button(
                                    "Delete",
                                    on_click=lambda selected=room, prompt=dialog: delete_room(
                                        selected, prompt
                                    ),
                                ).props("unelevated color=negative")
                        ui.button(icon="delete", on_click=dialog.open).props(
                            "flat round dense"
                        ).tooltip("Delete room")

    with ui.row().classes("w-full flex-wrap items-center gap-2"):
        add_button = ui.button("Add room", icon="add", on_click=add_room).props(
            "unelevated"
        ).classes("bg-[#75e6da] text-[#101820]")
        update_button = ui.button(
            "Save changes", icon="save", on_click=update_room
        ).props("unelevated").classes("bg-[#75e6da] text-[#101820]")
        update_button.set_visibility(False)
        cancel_button = ui.button("Cancel edit", on_click=reset_form).props(
            "outline"
        ).classes("border-[#45616b] text-[#d8e7e8]")
        cancel_button.set_visibility(False)

    ui.label("Existing rooms").classes("mt-4 text-lg font-semibold text-white")
    room_list = ui.column().classes("w-full gap-1")
    refresh_rooms()
