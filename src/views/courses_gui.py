from nicegui import ui

from src.services.course_service import (
    add_course_from_values,
    delete_course_from_values,
    update_course_from_values,
)

MODALITIES = ("in_person", "online", "hybrid")


def _csv_values(value, label):
    if not value or not value.strip():
        return []
    values = [item.strip() for item in value.split(",")]
    if any(not item for item in values):
        raise ValueError(f"{label} cannot contain empty entries.")
    if len(values) != len(set(values)):
        raise ValueError(f"Duplicate {label.lower()} are not allowed.")
    return values


def courses_gui(course_members: list) -> None:
    ui.label("Courses").classes("text-xl font-semibold text-white")
    ui.label("Add a course section and its scheduling requirements.").classes(
        "text-sm text-[#9fb2b8]"
    )
    ui.label("Existing courses").classes("mt-4 text-lg font-semibold text-white")
    course_list = ui.column().classes("w-full gap-1")

    with ui.row().classes("w-full flex-wrap items-center gap-2"):
        add_button = ui.button("Add new course", icon="add", on_click=lambda: show_form()).props(
            "unelevated"
        ).classes("bg-[#75e6da] text-[#101820]")

    with ui.column().classes("w-full gap-4 mt-6 rounded-lg border border-[#45616b] bg-[#17232b] p-4") as form_container:
        form_container.set_visibility(False)
        form_heading = ui.label("Add New Course").classes(
            "text-lg font-semibold text-white"
        )

        with ui.row().classes("w-full flex-wrap gap-4"):
            course_id = ui.input("Course ID").classes("min-w-48 flex-1")
            section_id = ui.input("Section ID", placeholder="Optional").classes(
                "min-w-40 flex-1"
            )
            credits = ui.number("Credits", value=3, min=1, step=1).classes("w-36")
            capacity = ui.number("Capacity", value=30, min=1, step=1).classes("w-36")
            modality = ui.select(
                list(MODALITIES), value="in_person", label="Modality"
            ).classes("min-w-40 flex-1")

        resource_fields = []
        with ui.column().classes("w-full gap-3") as resource_section:
            with ui.row().classes("w-full flex-wrap gap-4"):
                rooms = ui.input(
                    "Available rooms", placeholder="Room 101, Room 202"
                ).classes("min-w-56 flex-1")
                labs = ui.input(
                    "Available labs", placeholder="Lab 101, Lab 202"
                ).classes("min-w-56 flex-1")
            with ui.row().classes("w-full flex-wrap gap-4"):
                required_room_features = ui.input(
                    "Required room features", placeholder="Projector, accessible"
                ).classes("min-w-56 flex-1")
                required_lab_features = ui.input(
                    "Required lab features", placeholder="GPU, specialized software"
                ).classes("min-w-56 flex-1")
            reserve_room = ui.checkbox("Reserve the room during lab meetings", value=True)
        resource_fields.extend([rooms, labs, required_room_features, required_lab_features, reserve_room])

        with ui.row().classes("w-full flex-wrap gap-4"):
            conflicts = ui.input(
                "Conflicting course IDs", placeholder="CS 101, MATH 205"
            ).classes("min-w-56 flex-1")
            faculty_names = ui.input(
                "Faculty candidates", placeholder="Dr. Smith, Dr. Jones"
            ).classes("min-w-56 flex-1")

        derive_faculty = ui.checkbox(
            "Derive faculty candidates from course preferences", value=True
        ).classes("text-[#d8e7e8]")

        def set_resource_fields_enabled(enabled: bool) -> None:
            for field in resource_fields:
                field.set_enabled(enabled)

        def apply_modality(selected_modality: str) -> None:
            resource_section.set_visibility(selected_modality != "online")
            set_resource_fields_enabled(selected_modality != "online")

        def modality_changed(event) -> None:
            apply_modality(event.value)

        modality.on_value_change(modality_changed)

        editing_course = {"course": None}

        def integer_value(field, label):
            value = field.value
            if value is None or not float(value).is_integer() or value <= 0:
                raise ValueError(f"{label} must be a positive integer.")
            return int(value)

        def form_values():
            selected_modality = modality.value
            if selected_modality not in MODALITIES:
                raise ValueError("Select a valid course modality.")

            if selected_modality == "online":
                selected_rooms = []
                selected_labs = []
                room_features = []
                lab_features = []
                reserve_room_during_lab = False
            else:
                selected_rooms = _csv_values(rooms.value, "Rooms")
                selected_labs = _csv_values(labs.value, "Labs")
                room_features = _csv_values(
                    required_room_features.value, "Required room features"
                )
                lab_features = _csv_values(
                    required_lab_features.value, "Required lab features"
                )
                reserve_room_during_lab = bool(reserve_room.value)
            selected_conflicts = _csv_values(conflicts.value, "Conflicts")
            selected_faculty = (
                None
                if derive_faculty.value
                else _csv_values(faculty_names.value, "Faculty candidates")
            )
            if selected_faculty == []:
                raise ValueError("Enter faculty candidates or select derive mode.")

            return (
                course_id.value or "",
                section_id.value,
                integer_value(credits, "Credits"),
                integer_value(capacity, "Capacity"),
                selected_modality,
                selected_rooms,
                selected_labs,
                room_features,
                lab_features,
                reserve_room_during_lab,
                selected_conflicts,
                selected_faculty,
            )

        def show_form() -> None:
            editing_course["course"] = None
            form_heading.set_text("Add New Course")
            course_id.value = ""
            section_id.value = ""
            credits.value = 3
            capacity.value = 30
            modality.value = "in_person"
            apply_modality("in_person")
            rooms.value = ""
            labs.value = ""
            required_room_features.value = ""
            required_lab_features.value = ""
            reserve_room.value = True
            conflicts.value = ""
            faculty_names.value = ""
            derive_faculty.value = True
            form_container.set_visibility(True)
            add_submit_button.set_visibility(True)
            update_button.set_visibility(False)
            cancel_button.set_visibility(True)

        def reset_form() -> None:
            editing_course["course"] = None
            form_heading.set_text("Add New Course")
            course_id.value = ""
            section_id.value = ""
            credits.value = 3
            capacity.value = 30
            modality.value = "in_person"
            apply_modality("in_person")
            rooms.value = ""
            labs.value = ""
            required_room_features.value = ""
            required_lab_features.value = ""
            reserve_room.value = True
            conflicts.value = ""
            faculty_names.value = ""
            derive_faculty.value = True
            form_container.set_visibility(False)
            add_submit_button.set_visibility(True)
            update_button.set_visibility(False)
            cancel_button.set_visibility(False)

        def add_course() -> None:
            try:
                add_course_from_values(course_members, *form_values())
            except (TypeError, ValueError) as exc:
                ui.notify(str(exc), type="negative")
                return
            reset_form()
            refresh_courses()
            ui.notify("Course added.", type="positive")

        def update_course() -> None:
            try:
                update_course_from_values(
                    course_members, editing_course["course"], *form_values()
                )
            except (TypeError, ValueError) as exc:
                ui.notify(str(exc), type="negative")
                return
            reset_form()
            refresh_courses()
            ui.notify("Course updated.", type="positive")

        def begin_edit(course) -> None:
            editing_course["course"] = course
            form_heading.set_text("Modifying Course")
            course_id.value = course.course_id
            section_id.value = course.section_id or ""
            credits.value = course.credits
            capacity.value = course.capacity
            modality.value = course.modality
            apply_modality(course.modality)
            rooms.value = ", ".join(course.room)
            labs.value = ", ".join(course.lab)
            required_room_features.value = ", ".join(
                sorted(course.required_room_features)
            )
            required_lab_features.value = ", ".join(
                sorted(course.required_lab_features)
            )
            reserve_room.value = course.reserve_room_during_lab
            conflicts.value = ", ".join(course.conflicts)
            derive_faculty.value = course.faculty is None
            faculty_names.value = ", ".join(course.faculty or [])
            form_container.set_visibility(True)
            add_submit_button.set_visibility(False)
            update_button.set_visibility(True)
            cancel_button.set_visibility(True)

        def delete_course(course, dialog) -> None:
            try:
                delete_course_from_values(course_members, course)
            except ValueError as exc:
                ui.notify(str(exc), type="negative")
                dialog.close()
                return
            if editing_course["course"] is course:
                reset_form()
            ui.notify("Course deleted.", type="positive")
            dialog.close()
            refresh_courses()

        with ui.row().classes("w-full flex-wrap items-center gap-2"):
            add_submit_button = ui.button("Create course", icon="add", on_click=add_course).props(
                "unelevated"
            ).classes("bg-[#75e6da] text-[#101820]")
            update_button = ui.button(
                "Save changes", icon="save", on_click=update_course
            ).props("unelevated").classes("bg-[#75e6da] text-[#101820]")
            update_button.set_visibility(False)
            cancel_button = ui.button("Cancel", on_click=reset_form).props(
                "outline"
            ).classes("border-[#45616b] text-[#d8e7e8]")
            cancel_button.set_visibility(False)

    def refresh_courses() -> None:
        course_list.clear()
        with course_list:
            if not course_members:
                ui.label("No courses added yet.").classes("text-sm text-[#9fb2b8]")
                return
            for course in course_members:
                section = f"Section {course.section_id}" if course.section_id else "No section"
                with ui.row().classes(
                    "w-full items-center justify-between gap-4 border-b border-[#29404b] py-3"
                ):
                    with ui.column().classes("min-w-0 gap-1"):
                        ui.label(f"{course.course_id}  |  {section}").classes(
                            "font-semibold text-white"
                        )
                        details = (
                            f"{course.credits} credits  |  Capacity: {course.capacity}  |  "
                            f"{course.modality}  |  Rooms: {', '.join(course.room) or 'None'}"
                        )
                        ui.label(details).classes("break-words text-sm text-[#9fb2b8]")
                    with ui.row().classes("shrink-0 items-center gap-1"):
                        ui.button(
                            icon="edit",
                            on_click=lambda selected=course: begin_edit(selected),
                        ).props("flat round dense").tooltip("Edit course")
                        with ui.dialog() as dialog, ui.card().classes(
                            "border border-[#29404b] bg-[#182630]"
                        ):
                            ui.label(f"Delete {course.course_id}?").classes(
                                "text-lg font-semibold text-white"
                            )
                            ui.label("This cannot be undone.").classes(
                                "text-sm text-[#9fb2b8]"
                            )
                            with ui.row().classes("mt-4 w-full justify-end gap-2"):
                                ui.button("Cancel", on_click=dialog.close).props("flat")
                                ui.button(
                                    "Delete",
                                    on_click=lambda selected=course, prompt=dialog: delete_course(
                                        selected, prompt
                                    ),
                                ).props("unelevated color=negative")
                        ui.button(icon="delete", on_click=dialog.open).props(
                            "flat round dense"
                        ).tooltip("Delete course")

    refresh_courses()
