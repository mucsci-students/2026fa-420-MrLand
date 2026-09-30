from nicegui import ui

from services.lab_service import (
    add_lab_from_values,
    delete_lab_from_values,
    update_lab_from_values,
)

DAYS = ("MON", "TUE", "WED", "THU", "FRI")


def _availability_text(times) -> str:
    if times is None:
        return "Unrestricted"
    if not times:
        return "No availability"
    return "; ".join(
        f"{day}: {', '.join(f'{item.start}-{item.end}' for item in ranges)}"
        for day, ranges in times.items()
    )


def labs_gui(labs: list) -> None:
    ui.label("Labs").classes("text-xl font-semibold text-white")
    ui.label("Add a lab, its capacity, features, and availability.").classes(
        "text-sm text-[#9fb2b8]"
    )

    with ui.row().classes("w-full flex-wrap gap-4"):
        name = ui.input("Lab name").classes("min-w-56 flex-1")
        capacity = ui.number("Capacity", value=20, min=1, step=1).classes("w-40")
        features = ui.input(
            "Features", placeholder="Projector, fume hood"
        ).classes("min-w-56 flex-1")

    unrestricted = ui.checkbox("Unrestricted availability", value=True).classes(
        "text-[#d8e7e8]"
    )
    availability_fields = {}
    with ui.grid(columns=2).classes("w-full gap-3"):
        for day in DAYS:
            availability_fields[day] = ui.input(
                f"{day} availability",
                placeholder="09:00-12:00, 13:00-17:00",
            ).classes("w-full")

    def set_availability_enabled(enabled: bool) -> None:
        for field in availability_fields.values():
            field.set_enabled(enabled)

    def availability_changed(event) -> None:
        set_availability_enabled(not event.value)

    unrestricted.on_value_change(availability_changed)
    set_availability_enabled(False)

    editing_lab = {"lab": None}

    def form_values():
        capacity_value = capacity.value
        if capacity_value is None or not float(capacity_value).is_integer():
            raise ValueError("Capacity must be a whole number.")

        times = None
        if not unrestricted.value:
            times = {
                day: [
                    value.strip()
                    for value in field.value.split(",")
                    if value.strip()
                ]
                for day, field in availability_fields.items()
            }

        feature_values = [
            value.strip()
            for value in (features.value or "").split(",")
            if value.strip()
        ]
        return name.value or "", int(capacity_value), feature_values, times

    def reset_form() -> None:
        editing_lab["lab"] = None
        name.value = ""
        capacity.value = 20
        features.value = ""
        unrestricted.value = True
        set_availability_enabled(False)
        for field in availability_fields.values():
            field.value = ""
        add_button.set_visibility(True)
        update_button.set_visibility(False)
        cancel_button.set_visibility(False)

    def add_lab() -> None:
        try:
            add_lab_from_values(labs, *form_values())
        except (TypeError, ValueError) as exc:
            ui.notify(str(exc), type="negative")
            return
        reset_form()
        refresh_labs()
        ui.notify("Lab added.", type="positive")

    def update_lab() -> None:
        try:
            update_lab_from_values(labs, editing_lab["lab"], *form_values())
        except (TypeError, ValueError) as exc:
            ui.notify(str(exc), type="negative")
            return
        reset_form()
        refresh_labs()
        ui.notify("Lab updated.", type="positive")

    def begin_edit(lab) -> None:
        editing_lab["lab"] = lab
        name.value = lab.name
        capacity.value = lab.capacity
        features.value = ", ".join(sorted(lab.features))
        unrestricted.value = lab.times is None
        set_availability_enabled(lab.times is not None)
        for day, field in availability_fields.items():
            field.value = ", ".join(
                f"{item.start}-{item.end}"
                for item in (lab.times or {}).get(day, [])
            )
        add_button.set_visibility(False)
        update_button.set_visibility(True)
        cancel_button.set_visibility(True)

    def delete_lab(lab, dialog) -> None:
        try:
            delete_lab_from_values(labs, lab)
        except ValueError as exc:
            ui.notify(str(exc), type="negative")
            dialog.close()
            return
        if editing_lab["lab"] is lab:
            reset_form()
        ui.notify("Lab deleted.", type="positive")
        dialog.close()
        refresh_labs()

    def refresh_labs() -> None:
        lab_list.clear()
        with lab_list:
            if not labs:
                ui.label("No labs added yet.").classes("text-sm text-[#9fb2b8]")
                return
            for lab in labs:
                with ui.row().classes(
                    "w-full items-center justify-between gap-4 border-b border-[#29404b] py-3"
                ):
                    with ui.column().classes("min-w-0 gap-1"):
                        ui.label(lab.name).classes("font-semibold text-white")
                        details = (
                            f"Capacity: {lab.capacity}  |  "
                            f"Features: {', '.join(sorted(lab.features)) or 'None'}  |  "
                            f"{_availability_text(lab.times)}"
                        )
                        ui.label(details).classes("break-words text-sm text-[#9fb2b8]")
                    with ui.row().classes("shrink-0 items-center gap-1"):
                        ui.button(
                            icon="edit",
                            on_click=lambda selected=lab: begin_edit(selected),
                        ).props("flat round dense").tooltip("Edit lab")
                        with ui.dialog() as dialog, ui.card().classes(
                            "border border-[#29404b] bg-[#182630]"
                        ):
                            ui.label(f"Delete {lab.name}?").classes(
                                "text-lg font-semibold text-white"
                            )
                            ui.label("This cannot be undone.").classes(
                                "text-sm text-[#9fb2b8]"
                            )
                            with ui.row().classes("mt-4 w-full justify-end gap-2"):
                                ui.button("Cancel", on_click=dialog.close).props("flat")
                                ui.button(
                                    "Delete",
                                    on_click=lambda selected=lab, prompt=dialog: delete_lab(
                                        selected, prompt
                                    ),
                                ).props("unelevated color=negative")
                        ui.button(icon="delete", on_click=dialog.open).props(
                            "flat round dense"
                        ).tooltip("Delete lab")

    with ui.row().classes("w-full flex-wrap items-center gap-2"):
        add_button = ui.button("Add lab", icon="add", on_click=add_lab).props(
            "unelevated"
        ).classes("bg-[#75e6da] text-[#101820]")
        update_button = ui.button(
            "Save changes", icon="save", on_click=update_lab
        ).props("unelevated").classes("bg-[#75e6da] text-[#101820]")
        update_button.set_visibility(False)
        cancel_button = ui.button("Cancel edit", on_click=reset_form).props(
            "outline"
        ).classes("border-[#45616b] text-[#d8e7e8]")
        cancel_button.set_visibility(False)

    ui.label("Existing labs").classes("mt-4 text-lg font-semibold text-white")
    lab_list = ui.column().classes("w-full gap-1")
    refresh_labs()
