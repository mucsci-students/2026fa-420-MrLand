# File name: schedule_calendar_view.py
# Primary Author: Dylan Groff


"""
Weekly calendar view for browsing a filtered schedule.

The parent schedule viewer owns schedule loading and shared filters. Call
update(filtered_schedule) whenever the schedule or a shared filter changes.
"""

from __future__ import annotations

from math import ceil, floor

from nicegui import ui

from src.controllers.schedule_controller import schedule_controller as controller
from src.controllers.schedule_inspection_controller import (
    get_course_details,
    get_faculty_details,
    get_lab_details,
    get_room_details,
)


DAYS = [
    ("MON", "Monday"),
    ("TUE", "Tuesday"),
    ("WED", "Wednesday"),
    ("THU", "Thursday"),
    ("FRI", "Friday"),
]


class ScheduleCalendarView:
    """A simple Monday-Friday calendar with events positioned by time."""

    def __init__(self) -> None:
        # initialize the schedule object
        self.filtered_schedule: list[dict] = []
        # initialize the selected day variable from the day filter
        self.selected_day: str | None = None
        # add a variable to track whether the calendar is in full screen mode
        self.fullscreen = False
        self.export_callback = None

        # Adds custom CSS for styling the Calendar
        ui.add_head_html(
            f"""
            <style>
                .schedule-calendar-fullscreen {{
                    position: fixed !important;
                    inset: 0 !important;
                    z-index: 1000 !important;
                    width: 100vw !important;
                    height: 100dvh !important;
                    max-height: 100dvh !important;
                    overflow: auto !important;
                    padding: 12px !important;
                    box-sizing: border-box !important;
                    background: var(--app-background) !important;
                }}

                .schedule-calendar-fullscreen .schedule-calendar-scroll {{
                    height: calc(100dvh - 90px);
                    overflow: hidden;
                }}

                .schedule-calendar-fullscreen .schedule-calendar-grid {{
                    min-width: 0;
                    height: 100%;
                }}
                .schedule-calendar-scroll {{
                    width: 100%;
                    overflow-x: auto;
                    border: 1px solid var(--border-color);
                    border-radius: 8px;
                }}
                .schedule-calendar-grid {{
                    display: grid;
                    grid-template-columns: 76px repeat(5, minmax(150px, 1fr));
                    min-width: 850px;
                    background: var(--app-background);
                }}
                .schedule-calendar-heading {{
                    position: sticky;
                    top: 0;
                    z-index: 2;
                    padding: 12px 8px;
                    text-align: center;
                    font-weight: 600;
                    color: var(--app-foreground);
                    background: var(--surface-raised);
                    border-bottom: 1px solid var(--border-color);
                    border-right: 1px solid var(--border-color);
                }}
                .schedule-calendar-time {{
                    box-sizing: border-box;
                    padding: 4px 8px 0 0;
                    text-align: right;
                    color: var(--text-muted);
                    font-size: 12px;
                    border-right: 1px solid var(--border-color);
                }}
                .schedule-calendar-day {{
                    position: relative;
                    border-right: 1px solid var(--border-color);
                    background-image: repeating-linear-gradient(
                        to bottom,
                        transparent 0,
                        transparent 59px,
                        var(--border-color) 59px,
                        var(--border-color) 60px
                    );
                }}
                .schedule-calendar-event {{
                    position: absolute;
                    top: 0;
                    box-sizing: border-box;
                    overflow: hidden;
                    padding: 5px 7px;
                    border-left: 4px solid #75e6da;
                    border-radius: 4px;
                    color: #d8e7e8;
                    font-size: 12px;
                    line-height: 1.3;
                    cursor: pointer;
                    min-width: 0;
                }}
                .schedule-calendar-event:hover {{
                    filter: brightness(1.2);
                    z-index: 1;
                }}
                .schedule-calendar-event-title {{
                    font-weight: 700;
                    overflow-wrap: anywhere;
                    word-break: break-word;
                }}
                .schedule-calendar-event-details {{
                    color: #e0eaec;
                    overflow-wrap: anywhere;
                    word-break: break-word;
                }}
                .schedule-calendar-empty {{
                    padding: 24px;
                    color: var(--text-muted);
                    text-align: center;
                }}
            </style>
            """
        )

        # add calendar container and content area
        # Normal calendar and toolbar
        self.container = ui.column().classes("w-full gap-2")

        with self.container:
            with ui.row().classes("w-full items-center justify-end gap-2"):
                ui.button(
                    "Fullscreen",
                    icon="fullscreen",
                    on_click=self._open_fullscreen,
                ).props("outline")

            self.calendar_content = ui.column().classes("w-full gap-0")

        # Fullscreen pop-up
        self.fullscreen_dialog = ui.dialog().props("maximized")

        with self.fullscreen_dialog:
            with ui.card().classes(
                "w-full h-full gap-2"
            ).style("background: var(--app-background); color: var(--app-foreground);"
                    "display: flex; flex-direction: column;"
                    ):
                with ui.row().classes(
                    "w-full items-center justify-end gap-2"
                ):
                    ui.button(
                        "Export",
                        icon="download",
                        on_click=self._open_export,
                    ).props("outline")

                    ui.button(
                        "Exit Fullscreen",
                        icon="close",
                        on_click=self.fullscreen_dialog.close,
                    ).props("outline")

                self.popup_calendar_content = ui.column().classes(
                    "w-full gap-0"
                ).style("flex: 1; min-height: 0; overflow-x: auto; overflow-y: auto;")
    # ---------------------------------------------------------
    # Fullscreen Calendar Methods
    # ---------------------------------------------------------

    # Use the schedule viewer's existing export dialog
    def set_export_callback(self, callback) -> None:
        self.export_callback = callback


    def _open_export(self) -> None:
        if self.export_callback is not None:
            self.export_callback()

    # Expand the calendar to the viewport, or return to normal
    def _open_fullscreen(self) -> None:
        self._render()
        self.fullscreen_dialog.open()

    # ---------------------------------------------------------
    # Update Calendar
    # ---------------------------------------------------------

    # Replace the calendar contents with the parent's filtered rows.
    def update(self, filtered_schedule: list[dict], selected_day: str | None = None) -> None:
        self.filtered_schedule = [row.copy() for row in filtered_schedule]
        self.selected_day = selected_day
        self._render()

    # ---------------------------------------------------------
    # Create Calendar Layout
    # ---------------------------------------------------------
    def _render(self) -> None:
        self._render_calendar(self.calendar_content, popup=False)
        self._render_calendar(self.popup_calendar_content, popup=True)

    def _render_calendar(self, target, popup: bool) -> None:
        target.clear()

        if not self.filtered_schedule:
            with target:
                ui.label("No schedule entries match the current filters.").classes(
                    "schedule-calendar-empty w-full"
                )
            return
        
        # find the days to display based on the selected day filter
        visible_days = ([day for day in DAYS if day[0] == self.selected_day]
            if self.selected_day
            else DAYS
        )

        valid_rows = []
        for row in self.filtered_schedule:
            try:
                start = self._to_minutes(row["start"])
                end = self._to_minutes(row["end"])
            except (KeyError, TypeError, ValueError):
                # Skip malformed entries rather than breaking the whole view.
                continue

            if end <= start:
                continue

            valid_rows.append((row, start, end))

        if not valid_rows:
            with target:
                ui.label("No entries with valid start and end times.").classes(
                    "schedule-calendar-empty w-full"
                )
            return

        # set the first and last hour of the calendar based on the earliest start time and latest end time of the valid rows
        first_hour = max(0, floor(min(start for _, start, _ in valid_rows) / 60))
        last_hour = min(24, ceil(max(end for _, _, end in valid_rows) / 60))
        if last_hour <= first_hour:
            last_hour = min(24, first_hour + 1)

        range_start = first_hour * 60
        range_end = last_hour * 60
        calendar_height = range_end - range_start
        hour_count = last_hour - first_hour

        # add fullscreen styles to the calendar grid and scroll container if the calendar is in fullscreen mode
        if popup:
            grid_style = (
                f"grid-template-columns: 76px repeat("
                f"{len(visible_days)}, minmax(150px, 1fr));"
                f"grid-template-columns: 76px repeat("
                f"{len(visible_days)}, minmax(0, 1fr)); "
                f"grid-template-rows: 44px repeat("
                f"{hour_count}, minmax(0, 1fr));"
            )
            scroll_style = "width: 100%; overflow: auto;"
        else:
            grid_style = (
                f"grid-template-columns: 76px repeat("
                f"{len(visible_days)}, minmax(150px, 1fr));"
            )
            scroll_style = ""

        # Creates the calendar grid with day headings, time labels, and event blocks for each course
        with target:
            with ui.element("div").classes("schedule-calendar-scroll").style(scroll_style):
                with ui.element("div").classes("schedule-calendar-grid").style(
                    # changes number of columns based on the number of visible days
                    grid_style
                    ):
                    ui.element("div").classes("schedule-calendar-heading").style(
                        "grid-column: 1; grid-row: 1;"
                    ).props("aria-label='Time'")

                    # Creates the day headings for the calendar grid
                    for column, (_, day_name) in enumerate(visible_days, start=2):
                        ui.label(day_name).classes(
                            "schedule-calendar-heading"
                        ).style(f"grid-column: {column}; grid-row: 1;")

                    # Creates the time labels for the calendar grid
                    for hour in range(first_hour, last_hour):
                        row_number = hour - first_hour + 2
                        ui.label(self._format_time(hour * 60)).classes(
                            "schedule-calendar-time"
                        ).style(
                            f"grid-column: 1; grid-row: {row_number}; height: 60px;"
                        )

                    # Creates the day columns and positions events within them
                    for column, (day_code, _) in enumerate(visible_days, start=2):
                        with ui.element("div").classes(
                            "schedule-calendar-day"
                        ).style(
                            f"grid-column: {column}; "
                            f"grid-row: 2 / span {hour_count}; "
                            f"height: {calendar_height}px;"
                        ):
                            day_rows = [
                                (row, start, end)
                                for row, start, end in valid_rows
                                if row.get("day") == day_code
                            ]
                            day_rows.sort(key=lambda item: item[1])

                            # Create event blocks for each course and place them in the correct position based on start and end times
                            for (row, start, end, lane, lane_count, cluster,
                            ) in self._layout_day_events(day_rows):
                                top = start - range_start
                                height = max(end - start, 36)

                                # Calculate the event's horizontal position.
                                width = 100 / lane_count
                                left = lane * width

                                course = self._display_value(
                                    row.get("course")
                                )
                                # assigns a color to the course
                                background, border_color = self._course_color(course)

                                faculty = self._display_value(
                                    row.get("faculty")
                                )
                                resource = self._display_value(
                                    row.get("resource")
                                )

                                with ui.element("div").classes("schedule-calendar-event cursor-pointer"
                                    ).style(
                                        f"top: {top}px; "
                                        f"height: {height}px; "
                                        f"left: calc({left}% + 2px); "
                                        f"width: calc({width}% - 4px); "
                                        "right: auto;"
                                        f"background: {background}; "
                                        f"border-left-color: {border_color};"
                                    ) as event:
                                
                                    ui.label(course).classes(
                                        "schedule-calendar-event-title"
                                    )
                                    ui.label(
                                        f"{self._format_time(start)}–"
                                        f"{self._format_time(end)}"
                                    ).classes(
                                        "schedule-calendar-event-details"
                                    )

                                    details = " • ".join(
                                        value
                                        for value in (resource, faculty)
                                        if value != "—"
                                    )
                                    if details:
                                        ui.label(details).classes(
                                            "schedule-calendar-event-details"
                                        )
                                
                                # Add a click event to the event block that shows the details of the 
                                # selected meeting and its overlapping group
                                event.on(
                                    "click",
                                    lambda r=row, s=start, e=end, c=cluster:
                                        self._show_details(r, s, e, c),
                                )

    # ---------------------------------------------------------
    # Calendar Overlap Helpers
    # ---------------------------------------------------------

    # Side-by-side layout of overlapping meetings.
    # Each meeting gets the first available lane. If a meeting overlaps the meeting
    # currently occupying a lane, it gets another lane. When a meeting ends, its lane can be reused.
    @staticmethod
    def _layout_day_events(day_rows: list[tuple[dict, int, int]]) -> list[tuple]:
        """Assign overlapping meetings to separate horizontal lanes."""
        day_rows = sorted(day_rows, key=lambda item: (item[1], item[2]))
        clusters = []
        current_cluster = []
        cluster_end = -1

        # First, group meetings whose time ranges overlap.
        for item in day_rows:
            row, start, end = item

            if current_cluster and start >= cluster_end:
                clusters.append(current_cluster)
                current_cluster = []
                cluster_end = -1

            current_cluster.append(item)
            cluster_end = max(cluster_end, end)

        if current_cluster:
            clusters.append(current_cluster)

        layout = []

        # Assign each meeting in a cluster to a lane.
        for cluster in clusters:
            lane_ends = []
            assigned = []

            for row, start, end in cluster:
                lane = next(
                    (
                        index
                        for index, lane_end in enumerate(lane_ends)
                        if lane_end <= start
                    ),
                    None,
                )

                if lane is None:
                    lane = len(lane_ends)
                    lane_ends.append(end)
                else:
                    lane_ends[lane] = end

                assigned.append((row, start, end, lane))

            lane_count = len(lane_ends)

            for row, start, end, lane in assigned:
                layout.append(
                    (row, start, end, lane, lane_count, cluster)
                )

        return layout
    
    # Show full details for a meeting and its overlapping group.
    # The dialog contains a left-side navigation panel and a right-side content area.
    # Overview and Time Assignment are always available. Faculty and Resource are
    # only shown when matching configuration details exist for the selected meeting.
    def _show_details(
        self,
        row: dict,
        start: int,
        end: int,
        cluster: list[tuple[dict, int, int]],
    ) -> None:
        selected = {"row": row, "start": start, "end": end, "cluster": cluster}
        active_section = {"value": "Overview"}

        # create and format pop-up dialog
        with ui.dialog() as dialog:
            with ui.card().classes("w-[min(900px,95vw)] max-w-none bg-[#101820] text-[#d8e7e8]"):
                heading = ui.label().classes("text-xl font-bold")
                with ui.row().classes("w-full items-stretch gap-4"):
                    navigation = ui.column().classes(
                        "w-44 shrink-0 gap-2 border-r border-[#29404b] pr-3"
                    )
                    content = ui.column().classes("min-w-0 flex-1 gap-3")

                with ui.row().classes("w-full justify-end"):
                    ui.button("Close", on_click=dialog.close).props("outline")

        # Return available course/faculty/resource details for the selected meeting.
        def configuration_details() -> tuple[object | None, object | None, object | None, str | None]:
            current = controller.current
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
                    ui.label(f"Course: {self._display_value(current_row.get('course'))}")
                    ui.label(f"Day: {self._display_value(current_row.get('day'))}")
                    ui.label(
                        f"Time: {self._format_time(current_start)}–"
                        f"{self._format_time(current_end)}"
                    )
                    ui.label(f"Faculty: {self._display_value(current_row.get('faculty'))}")
                    ui.label(f"Room / Lab: {self._display_value(current_row.get('resource'))}")
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
                        f"Other meetings in this overlap group "
                        f"({len(overlapping_meetings)})"
                    ).classes("font-bold")

                    if not overlapping_meetings:
                        ui.label("No other meetings overlap this meeting.").classes("text-sm text-gray-400")

                    # Keep the overlap list available in Overview. Selecting an item
                    # updates this dialog's contents instead of opening another dialog.
                    for other_row, other_start, other_end in overlapping_meetings:
                        other_course = self._display_value(other_row.get("course"))
                        ui.button(
                            f"{other_course} — "
                            f"{self._format_time(other_start)}–"
                            f"{self._format_time(other_end)}",
                            on_click=lambda r=other_row, s=other_start, e=other_end: select_meeting(
                                r, s, e, current_cluster
                            ),
                        ).props("outline no-caps").classes("w-full")

            elif section == "Time Assignment":
                with content:
                    ui.label("Time Assignment").classes("text-lg font-semibold")
                    ui.label(f"Course: {self._display_value(current_row.get('course'))}")
                    ui.label(f"Faculty: {self._display_value(current_row.get('faculty'))}")
                    ui.label(f"Day: {self._display_value(current_row.get('day'))}")
                    ui.label(f"Start: {self._format_time(current_start)}")
                    ui.label(f"End: {self._format_time(current_end)}")

            elif section == "Course" and course is not None:
                modality_names = {
                    "in_person": "In Person",
                    "online": "Online",
                    "hybrid": "Hybrid",
                }
                modality = modality_names.get(
                    str(course.modality), str(course.modality)
                )
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
        def select_meeting(new_row: dict, new_start: int, new_end: int, new_cluster: list[tuple[dict, int, int]]) -> None:
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
            heading.set_text(self._display_value(selected["row"].get("course")))

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
                        + ("bg-[#21414a] text-[#75e6da]" if section == active_section["value"] else "text-[#d8e7e8]")
                    )

        # run the initial setup for the dialog
        rebuild_navigation()
        show_section("Overview")
        dialog.open()

    # Return a background and border color for a course.
    def _course_color(self, course: str) -> tuple[str, str]:
        palette = [
        ("#21414a", "#75e6da"),
        ("#3b3157", "#b8a4ff"),
        ("#4a3828", "#f0bd82"),
        ("#293e59", "#8fc5ff"),
        ("#49313b", "#f2a3bd"),
        ("#304936", "#a6dfa9"),
        ("#563c26", "#ffc078"),
        ("#264653", "#2a9d8f"),
        ("#5a2a27", "#ff8a80"),
        ("#3d405b", "#f2cc8f"),
        ("#344e41", "#a3b18a"),
        ("#533747", "#e0aaff"),
        ]

        # Create a sorted list of unique course names from the filtered schedule
        courses = sorted({
            str(row.get("course", ""))
            for row in self.filtered_schedule
        })

        try:
            index = courses.index(course)
        except ValueError:
            index = 0

        return palette[index % len(palette)]
    
    # ---------------------------------------------------------
    # Value Formatting Helpers
    # ---------------------------------------------------------

    # Convert a 24-hour HH:MM string to minutes after midnight.
    @staticmethod
    def _to_minutes(time_value: str) -> int:
        hour_text, minute_text = str(time_value).split(":", maxsplit=1)
        hour = int(hour_text)
        minute = int(minute_text)
        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            raise ValueError("Time is outside the valid range.")
        return hour * 60 + minute

    # Formats minutes after midnight into a 12-hour time string with AM/PM
    @staticmethod
    def _format_time(minutes: int) -> str:
        hour = (minutes // 60) % 24
        minute = minutes % 60
        suffix = "AM" if hour < 12 else "PM"
        display_hour = hour % 12 or 12
        return f"{display_hour}:{minute:02d} {suffix}"

    # helper to display a value or a placeholder if the value is None or empty
    @staticmethod
    def _display_value(value: object) -> str:
        if value is None or str(value).strip() == "":
            return "—"
        return str(value)

# Create and return a calendar view instance.
def schedule_calendar_view() -> ScheduleCalendarView:
    return ScheduleCalendarView()
