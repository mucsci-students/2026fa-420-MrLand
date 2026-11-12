"""Meeting-details dialog for the weekly schedule calendar."""

from typing import Protocol

from nicegui import ui
from scheduler.config import FacultyConfig, LabConfig, RoomConfig
from scheduler.models.course import Course

from src.controllers.schedule_controller import ScheduleController
from src.controllers.schedule_inspection_controller import (
    get_course_details,
    get_faculty_details,
    get_lab_details,
    get_room_details,
)
from src.views.schedule_calendar_types import OverlapCluster, ScheduleRow, SelectedMeeting


class CalendarDetailsHost(Protocol):
    def _format_time(self, minutes: int) -> str: ...

    def _display_value(self, value: object) -> str: ...


def show_meeting_details(
    view: CalendarDetailsHost,
    schedule_controller: ScheduleController,
    row: ScheduleRow,
    start: int,
    end: int,
    cluster: OverlapCluster,
) -> None:
    selected: SelectedMeeting = {
        "row": row,
        "start": start,
        "end": end,
        "cluster": cluster,
    }
    active_section = {"value": "Overview"}

    # create and format pop-up dialog
    with (
        ui.dialog() as dialog,
        ui.card().classes("w-[min(900px,95vw)] max-w-none bg-[#101820] text-[#d8e7e8]"),
    ):
        heading = ui.label().classes("text-xl font-bold")
        with ui.row().classes("w-full items-stretch gap-4"):
            navigation = ui.column().classes("w-44 shrink-0 gap-2 border-r border-[#29404b] pr-3")
            content = ui.column().classes("min-w-0 flex-1 gap-3")

        with ui.row().classes("w-full justify-end"):
            ui.button("Close", on_click=dialog.close).props("outline")

    # Return available course/faculty/resource details for the selected meeting.
    def configuration_details() -> tuple[
        Course | None,
        FacultyConfig | None,
        RoomConfig | LabConfig | None,
        str | None,
    ]:
        current = schedule_controller.current
        if current is None or current.config is None:
            return None, None, None, None

        config = current.config
        faculty_name = selected["row"].get("faculty")
        resource_name = selected["row"].get("resource")
        course_id = selected["row"].get("course")

        # gets the course details if the course ID is empty or a placeholder
        course = (
            get_course_details(current.schedule, course_id)
            if course_id and str(course_id).strip() not in ("", "—")
            else None
        )

        # gets the faculty details if the faculty name is not empty or a placeholder
        faculty = (
            get_faculty_details(config, faculty_name)
            if faculty_name and str(faculty_name).strip() not in ("", "—")
            else None
        )

        # gets the resource details if the resource name is not empty or a placeholder
        resource = None
        resource_type = None
        if resource_name and str(resource_name).strip() not in ("", "—"):
            lab = get_lab_details(config, resource_name)
            if lab is not None:
                resource = lab
                resource_type = "Lab"
            else:
                room = get_room_details(config, resource_name)
                if room is not None:
                    resource = room
                    resource_type = "Room"

        return course, faculty, resource, resource_type

    # Refresh the right-side content without creating another dialog.
    def show_section(section: str) -> None:
        active_section["value"] = section
        rebuild_navigation()
        content.clear()

        current_row = selected["row"]
        current_start = selected["start"]
        current_end = selected["end"]
        current_cluster = selected["cluster"]
        course, faculty, resource, resource_type = configuration_details()

        if section == "Overview":
            with content:
                ui.label("Overview").classes("text-lg font-semibold")
                ui.label(f"Course: {view._display_value(current_row.get('course'))}")
                ui.label(f"Day: {view._display_value(current_row.get('day'))}")
                ui.label(
                    f"Time: {view._format_time(current_start)}–{view._format_time(current_end)}"
                )
                ui.label(f"Faculty: {view._display_value(current_row.get('faculty'))}")
                ui.label(f"Room / Lab: {view._display_value(current_row.get('resource'))}")
                ui.separator()

                # Exclude the selected meeting from the overlap list.
                overlapping_meetings = [
                    (other_row, other_start, other_end)
                    for other_row, other_start, other_end in current_cluster
                    if not (
                        other_row is current_row
                        and other_start == current_start
                        and other_end == current_end
                    )
                ]

                ui.label(
                    f"Other meetings in this overlap group ({len(overlapping_meetings)})"
                ).classes("font-bold")

                if not overlapping_meetings:
                    ui.label("No other meetings overlap this meeting.").classes(
                        "text-sm text-gray-400"
                    )

                # Keep the overlap list available in Overview. Selecting an item
                # updates this dialog's contents instead of opening another dialog.
                for other_row, other_start, other_end in overlapping_meetings:
                    other_course = view._display_value(other_row.get("course"))
                    ui.button(
                        f"{other_course} — "
                        f"{view._format_time(other_start)}–"
                        f"{view._format_time(other_end)}",
                        on_click=lambda r=other_row, s=other_start, e=other_end: select_meeting(
                            r, s, e, current_cluster
                        ),
                    ).props("outline no-caps").classes("w-full")

        elif section == "Time Assignment":
            with content:
                ui.label("Time Assignment").classes("text-lg font-semibold")
                ui.label(f"Course: {view._display_value(current_row.get('course'))}")
                ui.label(f"Faculty: {view._display_value(current_row.get('faculty'))}")
                ui.label(f"Day: {view._display_value(current_row.get('day'))}")
                ui.label(f"Start: {view._format_time(current_start)}")
                ui.label(f"End: {view._format_time(current_end)}")

        elif section == "Course" and course is not None:
            modality_names = {
                "in_person": "In Person",
                "online": "Online",
                "hybrid": "Hybrid",
            }
            modality = modality_names.get(str(course.modality), str(course.modality))
            conflicts = (
                ", ".join(str(conflict) for conflict in course.conflicts)
                if course.conflicts
                else "None"
            )
            with content:
                ui.label("Course Details").classes("text-lg font-semibold")
                ui.label(f"Course ID: {course.course_id}")
                ui.label(f"Section: {course.section_id}")
                ui.label(f"Credits: {course.credits}")
                ui.label(f"Capacity: {course.capacity}")
                ui.label(f"Modality: {modality}")
                ui.label(f"Conflicts: {conflicts}")

        elif section == "Faculty" and faculty is not None:
            with content:
                ui.label("Faculty Details").classes("text-lg font-semibold")
                ui.label(f"Name: {faculty.name}")
                ui.label(f"Minimum Credits: {faculty.minimum_credits}")
                ui.label(f"Maximum Credits: {faculty.maximum_credits}")
                ui.label(f"Maximum Days: {faculty.maximum_days}")
                ui.label(f"Unique Course Limit: {faculty.unique_course_limit}")

        elif section == "Resource" and resource is not None:
            with content:
                ui.label(f"{resource_type} Details").classes("text-lg font-semibold")
                ui.label(f"Name: {resource.name}")
                ui.label(f"Capacity: {resource.capacity}")
                features = (
                    ", ".join(str(feature) for feature in resource.features)
                    if resource.features
                    else "None"
                )
                ui.label(f"Features: {features}")

    # Change the selected meeting inside the existing dialog.
    def select_meeting(
        new_row: ScheduleRow,
        new_start: int,
        new_end: int,
        new_cluster: OverlapCluster,
    ) -> None:
        selected["row"] = new_row
        selected["start"] = new_start
        selected["end"] = new_end
        selected["cluster"] = new_cluster
        active_section["value"] = "Overview"
        rebuild_navigation()
        show_section("Overview")

    # Show only navigation options that have details for this meeting.
    def rebuild_navigation() -> None:
        navigation.clear()
        course, faculty, resource, _ = configuration_details()
        heading.set_text(view._display_value(selected["row"].get("course")))

        sections = ["Overview", "Time Assignment"]
        if course is not None:
            sections.append("Course")
        if faculty is not None:
            sections.append("Faculty")
        if resource is not None:
            sections.append("Resource")

        with navigation:
            for section in sections:
                ui.button(
                    section,
                    on_click=lambda name=section: show_section(name),
                ).props("flat no-caps align=left").classes(
                    "w-full justify-start "
                    + (
                        "bg-[#21414a] text-[#75e6da]"
                        if section == active_section["value"]
                        else "text-[#d8e7e8]"
                    )
                )

    # run the initial setup for the dialog
    rebuild_navigation()
    show_section("Overview")
    dialog.open()
