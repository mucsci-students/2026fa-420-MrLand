# File name: schedule_table_view.py
# Primary Author: Dylan Groff

from nicegui import ui
from scheduler.config import CombinedConfig

from src.controllers.schedule_controller import schedule_controller as controller
from src.controllers.schedule_inspection_controller import (
    get_course_details,
    get_faculty_details,
    get_lab_details,
    get_room_details,
)


class ScheduleTableView:
    """Table view for a schedule.

    The parent schedule viewer owns the Table tab filters. Pass the filtered
    schedule to update() whenever the schedule or a Table filter changes.
    Column sorting is handled directly by the table.
    """

    def __init__(self) -> None:
        # initializes the schedule object
        self.filtered_schedule: list[dict] = []

        # adds custom CSS styling
        ui.add_head_html(
            """
            <style>
                .q-table__container,
                .q-table__middle,
                .q-table {
                    background: var(--app-background) !important;
                }

                .q-table thead tr {
                    background: var(--surface-raised) !important;
                }

                .q-table tbody tr {
                    background: var(--app-background) !important;
                }

                .q-table tbody tr:hover {
                    background: var(--surface-hover) !important;
                }

                .q-table th,
                .q-table td {
                    color: var(--app-foreground) !important;
                }

                /* Tab panel backgrounds */
                .q-tab-panels,
                .q-tab-panel {
                    background: var(--app-background) !important;
                    color: var(--app-foreground) !important;
                }
            </style>
            """
        )

        # ---------------------------------------------------------
        # Table
        # ---------------------------------------------------------
        columns = [
            {
                "name": "course",
                "label": "Course",
                "field": "course",
                "align": "left",
                "sortable": True,
            },
            {
                "name": "faculty",
                "label": "Faculty",
                "field": "faculty",
                "align": "left",
                "sortable": True,
            },
            {
                "name": "resource",
                "label": "Room / Lab",
                "field": "resource",
                "align": "left",
                "sortable": True,
            },
            {
                "name": "day",
                "label": "Day",
                "field": "day",
                "align": "left",
                "sortable": True,
            },
            {
                "name": "start",
                "label": "Start",
                "field": "start",
                "align": "left",
                "sortable": True,
            },
            {
                "name": "end",
                "label": "End",
                "field": "end",
                "align": "left",
                "sortable": True,
            },
        ]

        # create the table object
        self.table = (
            ui.table(
                columns=columns,
                rows=[],
                row_key="id",
            )
            .props("flat bordered")
            .classes("w-full")
        )

        self._add_clickable_cells()

    # ---------------------------------------------------------
    # Update Table
    # ---------------------------------------------------------

    def update(self, filtered_schedule: list[dict]) -> None:
        """Replace the rows using the parent's currently filtered schedule."""
        self.filtered_schedule = [row.copy() for row in filtered_schedule]
        self._render()

    # format the schedule for display in the table
    def _render(self) -> None:
        """Format the filtered schedule and let the table handle column sorting."""
        display_schedule = []
        for row in self.filtered_schedule:
            display_row = row.copy()
            display_row["start"] = self._format_time(row["start"])
            display_row["end"] = self._format_time(row["end"])
            display_schedule.append(display_row)

        self.table.rows = display_schedule
        self.table.update()

    # ---------------------------------------------------------
    # Inspect Element Controls
    # ---------------------------------------------------------

    def _add_clickable_cells(self) -> None:
        """Make selected table cells open their detail dialogs."""

        # creates a clickable cell for the course column that opens a dialog with course details
        self.table.add_slot(
            "body-cell-course",
            """
            <q-td :props="props">
                <q-btn
                    flat dense no-caps
                    :label="props.value"
                    @click="$parent.$emit('inspect-course', props.value)"
                />
            </q-td>
            """,
        )
        self.table.on(
            "inspect-course",
            lambda event: self._inspect_course(event.args),
        )

        # creates a clickable cell for the faculty column that opens a dialog with faculty details
        self.table.add_slot(
            "body-cell-faculty",
            """
            <q-td :props="props">
                <q-btn
                    flat dense no-caps
                    :label="props.value"
                    @click="$parent.$emit('inspect-faculty', props.value)"
                />
            </q-td>
            """,
        )
        self.table.on(
            "inspect-faculty",
            lambda event: self._inspect_faculty(event.args),
        )

        # creates a clickable cell for the resource column that opens a dialog with room or lab details
        self.table.add_slot(
            "body-cell-resource",
            """
            <q-td :props="props">
                <q-btn
                    flat dense no-caps
                    :label="props.value"
                    @click="$parent.$emit('inspect-resource', props.row)"
                />
            </q-td>
            """,
        )
        self.table.on(
            "inspect-resource",
            lambda event: self._inspect_resource(event.args),
        )

        # creates a clickable cell for the day column that opens a dialog with time assignment details
        self.table.add_slot(
            "body-cell-day",
            """
            <q-td :props="props">
                <q-btn
                    flat dense no-caps
                    :label="props.value"
                    @click="$parent.$emit('inspect-time', props.row)"
                />
            </q-td>
            """,
        )
        self.table.on(
            "inspect-time",
            lambda event: self._inspect_time(event.args),
        )

    # handles whether the current schedule has a config object before attempting to inspect details
    def _get_config(self) -> CombinedConfig | None:
        entry = controller.current
        if entry is None or entry.config is None:
            ui.notify(
                "Configuration details are unavailable for this schedule.",
                type="warning",
            )
            return None
        return entry.config

    # ---------------------------------------------------------
    # Element Inspection Getters
    # ---------------------------------------------------------
    def _inspect_course(self, course_id: str) -> None:
        config = self._get_config()
        if config is None:
            return

        entry = controller.current
        course = get_course_details(entry.schedule if entry is not None else None, course_id)
        if course is None:
            ui.notify("Course details not found", type="negative")
            return

        # format the modality and conflicts for more user-friendly display
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

        # create a dialog to display the course details
        with ui.dialog() as dialog, ui.card():
            ui.label("Course Details").classes("text-xl font-bold")
            ui.label(f"Course ID: {course.course_id}")
            ui.label(f"Section: {course.section_id}")
            ui.label(f"Credits: {course.credits}")
            ui.label(f"Capacity: {course.capacity}")
            ui.label(f"Modality: {modality}")
            ui.label(f"Conflicts: {conflicts}")
            ui.button("Close", on_click=dialog.close)
        dialog.open()

    def _inspect_faculty(self, faculty_name: str) -> None:
        config = self._get_config()
        if config is None:
            return

        faculty = get_faculty_details(config, faculty_name)
        if faculty is None:
            ui.notify("Faculty details not found", type="negative")
            return

        # create a dialog to display the faculty details
        with ui.dialog() as dialog, ui.card():
            ui.label("Faculty Details").classes("text-xl font-bold")
            ui.label(f"Name: {faculty.name}")
            ui.label(f"Minimum Credits: {faculty.minimum_credits}")
            ui.label(f"Maximum Credits: {faculty.maximum_credits}")
            ui.label(f"Maximum Days: {faculty.maximum_days}")
            ui.label(f"Unique Course Limit: {faculty.unique_course_limit}")
            ui.button("Close", on_click=dialog.close)
        dialog.open()

    def _inspect_room(self, room_name: str) -> None:
        config = self._get_config()
        if config is None:
            return

        room = get_room_details(config, room_name)
        if room is None:
            ui.notify("Room details not found", type="negative")
            return

        # format the features for more user-friendly display
        features = ", ".join(str(feature) for feature in room.features) if room.features else "None"

        # create a dialog to display the room details
        with ui.dialog() as dialog, ui.card():
            ui.label("Room Details").classes("text-xl font-bold")
            ui.label(f"Name: {room.name}")
            ui.label(f"Capacity: {room.capacity}")
            ui.label(f"Features: {features}")
            ui.button("Close", on_click=dialog.close)
        dialog.open()

    def _inspect_lab(self, lab_name: str) -> None:
        config = self._get_config()
        if config is None:
            return

        lab = get_lab_details(config, lab_name)
        if lab is None:
            ui.notify("Lab details not found", type="negative")
            return

        # format the features for more user-friendly display
        features = ", ".join(str(feature) for feature in lab.features) if lab.features else "None"

        # create a dialog to display the lab details
        with ui.dialog() as dialog, ui.card():
            ui.label("Lab Details").classes("text-xl font-bold")
            ui.label(f"Name: {lab.name}")
            ui.label(f"Capacity: {lab.capacity}")
            ui.label(f"Features: {features}")
            ui.button("Close", on_click=dialog.close)
        dialog.open()

    def _inspect_resource(self, row: dict) -> None:
        config = self._get_config()
        if config is None:
            return

        resource = row.get("resource")
        if not resource:
            ui.notify(
                "This course has no room or lab assignment.",
                type="info",
            )
            return

        # checks if the resource is a lab or a room and calls the appropriate inspection method
        if get_lab_details(config, resource) is not None:
            self._inspect_lab(resource)
        else:
            self._inspect_room(resource)

    def _inspect_time(self, row: dict) -> None:
        # The displayed row already has 12-hour formatted start/end values.
        with ui.dialog() as dialog, ui.card():
            ui.label("Time Assignment").classes("text-xl font-bold")
            ui.label(f"Course: {row['course']}")
            ui.label(f"Faculty: {row['faculty']}")
            ui.label(f"Day: {self._format_day(row['day'])}")
            ui.label(f"Start: {row['start']}")
            ui.label(f"End: {row['end']}")
            ui.button("Close", on_click=dialog.close)
        dialog.open()

    # ---------------------------------------------------------
    # Value Formatting Helpers
    # ---------------------------------------------------------
    # these helpers format values in the table to make data more user-friendly

    @staticmethod
    def _format_day(day: str) -> str:
        days = {
            "MON": "Monday",
            "TUE": "Tuesday",
            "WED": "Wednesday",
            "THU": "Thursday",
            "FRI": "Friday",
        }
        return days.get(day, day)

    @staticmethod
    def _format_time(time_value: str) -> str:
        hour, minute = map(int, time_value.split(":"))
        suffix = "AM" if hour < 12 else "PM"
        display_hour = hour % 12 or 12
        return f"{display_hour}:{minute:02d} {suffix}"


# ---------------------------------------------------------
# Create Table View
# ---------------------------------------------------------
def schedule_table_view() -> ScheduleTableView:
    """Create and return a table view instance for the parent viewer."""
    return ScheduleTableView()
