from nicegui import ui

from src.services.faculty_service import (
    add_faculty_from_values,
    delete_faculty_from_values,
    update_faculty_from_values,
)

DAYS = ("MON", "TUE", "WED", "THU", "FRI")


def _parse_preferences(value, label):
    preferences = {}
    for entry in (value or "").split(","):
        entry = entry.strip()
        if not entry:
            continue
        key, separator, score_text = entry.partition("=")
        if not separator or not key.strip():
            raise ValueError(f"Enter {label} as name=score pairs.")
        try:
            score = int(score_text.strip())
        except ValueError as exc:
            raise ValueError(f"{label} scores must be integers from 1 to 10.") from exc
        if not 1 <= score <= 10:
            raise ValueError(f"{label} scores must be from 1 to 10.")
        preferences[key.strip()] = score
    return preferences


def _availability_text(times) -> str:
    if not times:
        return "No availability"
    return "; ".join(
        f"{day}: {', '.join(f'{item.start}-{item.end}' for item in ranges)}"
        for day, ranges in times.items()
    )


def faculty_gui(faculty_members: list) -> None:
    ui.label("Faculty").classes("text-xl font-semibold text-white")
    ui.label("Add a faculty member and teaching constraints.").classes(
        "text-sm text-[#9fb2b8]"
    )
    ui.label("Existing faculty").classes("mt-4 text-lg font-semibold text-white")
    faculty_list = ui.column().classes("w-full gap-1")

    with ui.row().classes("w-full flex-wrap items-center gap-2"):
        add_button = ui.button("Add new faculty member", icon="add", on_click=lambda: show_form()).props(
            "unelevated"
        ).classes("bg-[#75e6da] text-[#101820]")

    with ui.column().classes("w-full gap-4 mt-6") as form_container:
        form_container.set_visibility(False)
        form_heading = ui.label("Add New Faculty Member").classes("text-lg font-semibold text-white")

        with ui.row().classes("w-full flex-wrap gap-4"):
            name = ui.input("Faculty name").classes("min-w-56 flex-1")
            maximum_credits = ui.number(
                "Maximum credits", value=12, min=0, step=1
            ).classes("min-w-40 flex-1")
            minimum_credits = ui.number(
                "Minimum credits", value=3, min=0, step=1
            ).classes("min-w-40 flex-1")
            course_limit = ui.number(
                "Course limit", value=3, min=1, step=1
            ).classes("min-w-40 flex-1")
            maximum_days = ui.number(
                "Maximum teaching days", value=5, min=0, max=5, step=1
            ).classes("min-w-40 flex-1")

        ui.label("Availability").classes("mt-2 font-semibold text-white")
        availability_fields = {}
        with ui.grid(columns=2).classes("w-full gap-3"):
            for day in DAYS:
                availability_fields[day] = ui.input(
                    f"{day} ranges",
                    placeholder="09:00-12:00, 13:00-17:00",
                ).classes("w-full")

        with ui.grid(columns=1).classes("w-full gap-3 md:grid-cols-3"):
            course_preferences = ui.textarea(
                "Course preferences", placeholder="CS 101=8, MATH 110=5"
            ).classes("w-full")
            room_preferences = ui.textarea(
                "Room preferences", placeholder="Room 101=8, Room 202=5"
            ).classes("w-full")
            lab_preferences = ui.textarea(
                "Lab preferences", placeholder="Lab 101=8, Lab 202=5"
            ).classes("w-full")

        mandatory_days = ui.select(
            list(DAYS), multiple=True, label="Mandatory teaching days"
        ).props("use-chips clearable").classes("w-full")

        editing_member = {"member": None}

        def integer_value(field, label, minimum, maximum=None):
            value = field.value
            if value is None or not float(value).is_integer():
                raise ValueError(f"{label} must be a whole number.")
            value = int(value)
            if value < minimum or (maximum is not None and value > maximum):
                if maximum is None:
                    raise ValueError(f"{label} must be at least {minimum}.")
                raise ValueError(f"{label} must be between {minimum} and {maximum}.")
            return value

        def form_values():
            times = {
                day: [value.strip() for value in field.value.split(",") if value.strip()]
                for day, field in availability_fields.items()
                if field.value and field.value.strip()
            }
            return (
                name.value or "",
                integer_value(maximum_credits, "Maximum credits", 0),
                integer_value(minimum_credits, "Minimum credits", 0),
                integer_value(course_limit, "Course limit", 1),
                times,
                integer_value(maximum_days, "Maximum teaching days", 0, 5),
                _parse_preferences(course_preferences.value, "Course preference"),
                _parse_preferences(room_preferences.value, "Room preference"),
                _parse_preferences(lab_preferences.value, "Lab preference"),
                set(mandatory_days.value or []),
            )

        def show_form() -> None:
            editing_member["member"] = None
            form_heading.set_text("Add New Faculty Member")
            name.value = ""
            maximum_credits.value = 12
            minimum_credits.value = 3
            course_limit.value = 3
            maximum_days.value = 5
            for field in availability_fields.values():
                field.value = ""
            course_preferences.value = ""
            room_preferences.value = ""
            lab_preferences.value = ""
            mandatory_days.value = []
            form_container.set_visibility(True)
            add_submit_button.set_visibility(True)
            update_button.set_visibility(False)
            cancel_button.set_visibility(True)

        def reset_form() -> None:
            editing_member["member"] = None
            form_heading.set_text("Add New Faculty Member")
            name.value = ""
            maximum_credits.value = 12
            minimum_credits.value = 3
            course_limit.value = 3
            maximum_days.value = 5
            for field in availability_fields.values():
                field.value = ""
            course_preferences.value = ""
            room_preferences.value = ""
            lab_preferences.value = ""
            mandatory_days.value = []
            form_container.set_visibility(False)
            add_submit_button.set_visibility(True)
            update_button.set_visibility(False)
            cancel_button.set_visibility(False)

        def add_member() -> None:
            try:
                add_faculty_from_values(faculty_members, *form_values())
            except (TypeError, ValueError) as exc:
                ui.notify(str(exc), type="negative")
                return
            reset_form()
            refresh_faculty()
            ui.notify("Faculty member added.", type="positive")

        def update_member() -> None:
            try:
                update_faculty_from_values(
                    faculty_members, editing_member["member"], *form_values()
                )
            except (TypeError, ValueError) as exc:
                ui.notify(str(exc), type="negative")
                return
            reset_form()
            refresh_faculty()
            ui.notify("Faculty member updated.", type="positive")

        def begin_edit(member) -> None:
            editing_member["member"] = member
            form_heading.set_text("Modifying Faculty Member")
            name.value = member.name
            maximum_credits.value = member.maximum_credits
            minimum_credits.value = member.minimum_credits
            course_limit.value = member.unique_course_limit
            maximum_days.value = member.maximum_days
            for day, field in availability_fields.items():
                field.value = ", ".join(
                    f"{item.start}-{item.end}"
                    for item in member.times.get(day, [])
                )
            course_preferences.value = ", ".join(
                f"{key}={score}" for key, score in member.course_preferences.items()
            )
            room_preferences.value = ", ".join(
                f"{key}={score}" for key, score in member.room_preferences.items()
            )
            lab_preferences.value = ", ".join(
                f"{key}={score}" for key, score in member.lab_preferences.items()
            )
            mandatory_days.value = sorted(member.mandatory_days)
            form_container.set_visibility(True)
            add_submit_button.set_visibility(False)
            update_button.set_visibility(True)
            cancel_button.set_visibility(True)

        def delete_member(member, dialog) -> None:
            try:
                delete_faculty_from_values(faculty_members, member)
            except ValueError as exc:
                ui.notify(str(exc), type="negative")
                dialog.close()
                return
            if editing_member["member"] is member:
                reset_form()
            ui.notify("Faculty member deleted.", type="positive")
            dialog.close()
            refresh_faculty()

        with ui.row().classes("w-full flex-wrap items-center gap-2"):
            add_submit_button = ui.button("Create faculty member", icon="add", on_click=add_member).props(
                "unelevated"
            ).classes("bg-[#75e6da] text-[#101820]")
            cancel_button = ui.button("Cancel", on_click=reset_form).props(
                "outline"
            ).classes("border-[#45616b] text-[#d8e7e8]")
            cancel_button.set_visibility(False)
            update_button = ui.button(
                "Save changes", icon="save", on_click=update_member
            ).props("unelevated").classes("bg-[#75e6da] text-[#101820]")
            update_button.set_visibility(False)

    def refresh_faculty() -> None:
        faculty_list.clear()
        with faculty_list:
            if not faculty_members:
                ui.label("No faculty members added yet.").classes(
                    "text-sm text-[#9fb2b8]"
                )
                return
            for member in faculty_members:
                with ui.row().classes(
                    "w-full items-center justify-between gap-4 border-b border-[#29404b] py-3"
                ):
                    with ui.column().classes("min-w-0 gap-1"):
                        ui.label(member.name).classes("font-semibold text-white")
                        details = (
                            f"Credits: {member.minimum_credits}-{member.maximum_credits}  |  "
                            f"Course limit: {member.unique_course_limit}  |  "
                            f"Max days: {member.maximum_days}  |  "
                            f"{_availability_text(member.times)}"
                        )
                        ui.label(details).classes("break-words text-sm text-[#9fb2b8]")
                    with ui.row().classes("shrink-0 items-center gap-1"):
                        ui.button(
                            icon="edit",
                            on_click=lambda selected=member: begin_edit(selected),
                        ).props("flat round dense").tooltip("Edit faculty member")
                        with ui.dialog() as dialog, ui.card().classes(
                            "border border-[#29404b] bg-[#182630]"
                        ):
                            ui.label(f"Delete {member.name}?").classes(
                                "text-lg font-semibold text-white"
                            )
                            ui.label("This cannot be undone.").classes(
                                "text-sm text-[#9fb2b8]"
                            )
                            with ui.row().classes("mt-4 w-full justify-end gap-2"):
                                ui.button("Cancel", on_click=dialog.close).props("flat")
                                ui.button(
                                    "Delete",
                                    on_click=lambda selected=member, prompt=dialog: delete_member(
                                        selected, prompt
                                    ),
                                ).props("unelevated color=negative")
                        ui.button(icon="delete", on_click=dialog.open).props(
                            "flat round dense"
                        ).tooltip("Delete faculty member")

    refresh_faculty()
