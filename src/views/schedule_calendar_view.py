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


BACKGROUND = "#101820"
PANEL = "#17252d"
TEXT = "#d8e7e8"
ACCENT = "#75e6da"

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

        # Adds custom CSS for styling the Calendar
        ui.add_head_html(
            f"""
            <style>
                .schedule-calendar-scroll {{
                    width: 100%;
                    overflow-x: auto;
                    border: 1px solid #29404b;
                    border-radius: 8px;
                }}
                .schedule-calendar-grid {{
                    display: grid;
                    grid-template-columns: 76px repeat(5, minmax(150px, 1fr));
                    min-width: 850px;
                    background: {BACKGROUND};
                }}
                .schedule-calendar-heading {{
                    position: sticky;
                    top: 0;
                    z-index: 2;
                    padding: 12px 8px;
                    text-align: center;
                    font-weight: 600;
                    color: {TEXT};
                    background: {PANEL};
                    border-bottom: 1px solid #29404b;
                    border-right: 1px solid #29404b;
                }}
                .schedule-calendar-time {{
                    box-sizing: border-box;
                    padding: 4px 8px 0 0;
                    text-align: right;
                    color: #a9c0c4;
                    font-size: 12px;
                    border-right: 1px solid #29404b;
                }}
                .schedule-calendar-day {{
                    position: relative;
                    border-right: 1px solid #29404b;
                    background-image: repeating-linear-gradient(
                        to bottom,
                        transparent 0,
                        transparent 59px,
                        #29404b 59px,
                        #29404b 60px
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
                    color: #a9c0c4;
                    text-align: center;
                }}
            </style>
            """
        )

        # add calendar container and content area
        self.container = ui.column().classes("w-full gap-2")
        with self.container:
            self.calendar_content = ui.column().classes("w-full gap-0")

    # ---------------------------------------------------------
    # Update Calendar
    # ---------------------------------------------------------

    def update(self, filtered_schedule: list[dict]) -> None:
        """Replace the calendar contents with the parent's filtered rows."""
        self.filtered_schedule = [row.copy() for row in filtered_schedule]
        self._render()

    # ---------------------------------------------------------
    # Create Calendar Layout
    # ---------------------------------------------------------
    def _render(self) -> None:
        self.calendar_content.clear()

        if not self.filtered_schedule:
            with self.calendar_content:
                ui.label("No schedule entries match the current filters.").classes(
                    "schedule-calendar-empty w-full"
                )
            return

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
            with self.calendar_content:
                ui.label("No entries with valid start and end times.").classes(
                    "schedule-calendar-empty w-full"
                )
            return

        first_hour = max(0, floor(min(start for _, start, _ in valid_rows) / 60))
        last_hour = min(24, ceil(max(end for _, _, end in valid_rows) / 60))
        if last_hour <= first_hour:
            last_hour = min(24, first_hour + 1)

        range_start = first_hour * 60
        range_end = last_hour * 60
        calendar_height = range_end - range_start
        hour_count = last_hour - first_hour

        with self.calendar_content:
            with ui.element("div").classes("schedule-calendar-scroll"):
                with ui.element("div").classes("schedule-calendar-grid"):
                    ui.element("div").classes("schedule-calendar-heading").style(
                        "grid-column: 1; grid-row: 1;"
                    ).props("aria-label='Time'")

                    # Creates the day headings for the calendar grid
                    for column, (_, day_name) in enumerate(DAYS, start=2):
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
                    for column, (day_code, _) in enumerate(DAYS, start=2):
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
    # Creates a pop-up to show all the details of a selected meeting 
    # and the other meetings that overlap with it when the lanes become too clustered together
    def _show_details(self, row: dict, start: int, end: int, cluster: list[tuple[dict, int, int]]) -> None:
        # creates pop-up dialog
        with ui.dialog() as dialog, ui.card().classes("min-w-72"):
            # Gets meeting details and displays them in the pop-up dialog
            ui.label(
                self._display_value(row.get("course"))
            ).classes("text-h6")

            ui.label(
                f"Day: {self._display_value(row.get('day'))}"
            )
            ui.label(
                f"Time: {self._format_time(start)}–"
                f"{self._format_time(end)}"
            )
            ui.label(
                f"Faculty: {self._display_value(row.get('faculty'))}"
            )
            ui.label(
                f"Room / Lab: {self._display_value(row.get('resource'))}"
            )

            ui.separator()
            ui.label(
                f"Meetings in this overlap group ({len(cluster)})"
            ).classes("font-bold")

            # List all meetings in the overlap group with their details
            for other_row, other_start, other_end in cluster:
                other_course = self._display_value(
                    other_row.get("course")
                )

                ui.button(
                    f"{other_course} — "
                    f"{self._format_time(other_start)}–"
                    f"{self._format_time(other_end)}",
                    on_click=lambda r=other_row, s=other_start, e=other_end:
                        self._show_details(r, s, e, cluster),
                ).props("outline").classes("w-full")

            ui.button("Close", on_click=dialog.close)

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


def schedule_calendar_view() -> ScheduleCalendarView:
    """Create and return a calendar view instance."""
    return ScheduleCalendarView()
