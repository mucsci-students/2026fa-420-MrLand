# File name: schedule_calendar_view.py
# Primary Author: Dylan Groff


"""
Weekly calendar view for browsing a filtered schedule.

The parent schedule viewer owns schedule loading and shared filters. Call
update(filtered_schedule) whenever the schedule or a shared filter changes.
"""

from __future__ import annotations

from collections.abc import Callable
from math import ceil, floor

from nicegui import ui

from src.controllers.schedule_controller import (
    schedule_controller as controller,
)
from src.models.schedule_viewer_model import ScheduleEntry
from src.views.schedule_calendar_details import show_meeting_details
from src.views.schedule_calendar_types import (
    OverlapCluster,
    ScheduleRow,
)
from src.views.schedule_calendar_types import (
    SelectedMeeting as SelectedMeeting,  # noqa: PLC0414
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

    def __init__(
        self,
        entry_provider: Callable[[], ScheduleEntry | None] | None = None,
        compact: bool = False,
    ) -> None:
        # Each calendar can provide its own schedule context for event details.
        self.entry_provider = entry_provider or (lambda: controller.current)

        # Compact mode is used by Schedule Comparison only.
        self.compact = compact

        # initialize the schedule object
        self.filtered_schedule: list[dict] = []
        # Keep the full schedule for stable course colors across filtered views.
        self.color_schedule: list[dict] = []
        self.display_mode = "Entire Schedule"
        # initialize the selected day variable from the day filter
        self.selected_day: str | None = None
        # Optional shared time range used by Schedule Comparison.
        self.time_range: tuple[int, int] | None = None
        # add a variable to track whether the calendar is in full screen mode
        self.fullscreen = False

        # Adds custom CSS for styling the Calendar
        ui.add_head_html(
            """
            <style>
                /* Calendar event colors for dark mode. */
                :root {
                    --calendar-event-text: #d8e7e8;
                    --calendar-event-details: #e0eaec;

                    --calendar-course-1: #21414a;
                    --calendar-course-2: #3b3157;
                    --calendar-course-3: #4a3828;
                    --calendar-course-4: #293e59;
                    --calendar-course-5: #49313b;
                    --calendar-course-6: #304936;
                    --calendar-course-7: #563c26;
                    --calendar-course-8: #264653;
                    --calendar-course-9: #5a2a27;
                    --calendar-course-10: #3d405b;
                    --calendar-course-11: #344e41;
                    --calendar-course-12: #533747;
                }

                /* Lighter event colors for light mode. */
                html[data-theme="light"] {
                    --calendar-event-text: #17324f;
                    --calendar-event-details: #354c63;

                    --calendar-course-1: #d4e8ed;
                    --calendar-course-2: #e4dcf5;
                    --calendar-course-3: #f3e3d0;
                    --calendar-course-4: #d9e7f7;
                    --calendar-course-5: #f3dce5;
                    --calendar-course-6: #dcebdc;
                    --calendar-course-7: #f5e2c9;
                    --calendar-course-8: #d3e9e8;
                    --calendar-course-9: #f3d9d6;
                    --calendar-course-10: #e2e3f2;
                    --calendar-course-11: #dce8df;
                    --calendar-course-12: #eeddf2;
                }
                #schedule-calendar-fullscreen:fullscreen {
                    width: 100%;
                    height: 100%;
                    max-height: 100%;
                    box-sizing: border-box;
                    overflow: auto;
                    padding: 12px;
                    background: var(--app-background);
                }

                #schedule-calendar-fullscreen:fullscreen .schedule-calendar-scroll {
                    height: calc(100dvh - 90px);
                    overflow: hidden;
                }

                #schedule-calendar-fullscreen:fullscreen .schedule-calendar-grid {
                    min-width: 0;
                    height: 100%;
                }
                .schedule-calendar-scroll {
                    width: 100%;
                    overflow-x: auto;
                    border: 1px solid var(--border-color);
                    border-radius: 8px;
                }
                .schedule-calendar-grid {
                    display: grid;
                    grid-template-columns: 76px repeat(5, minmax(150px, 1fr));
                    min-width: 850px;
                    background: var(--app-background);
                }
                .schedule-calendar-heading {
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
                }
                .schedule-calendar-time {
                    box-sizing: border-box;
                    padding: 4px 8px 0 0;
                    text-align: right;
                    color: var(--text-muted);
                    font-size: 12px;
                    border-right: 1px solid var(--border-color);
                }
                .schedule-calendar-day {
                    position: relative;
                    border-right: 1px solid var(--border-color);
                    background-image: repeating-linear-gradient(
                        to bottom,
                        transparent 0,
                        transparent 59px,
                        var(--border-color) 59px,
                        var(--border-color) 60px
                    );
                }
                
                .schedule-calendar-event {
                    position: absolute;
                    top: 0;
                    box-sizing: border-box;
                    overflow: hidden;
                    padding: 5px 7px;
                    border-left: 4px solid;
                    border-radius: 4px;
                    color: var(--calendar-event-text);
                    font-size: 12px;
                    line-height: 1.3;
                    cursor: pointer;
                    min-width: 0;
                }
                .schedule-calendar-event:hover {
                    filter: brightness(1.2);
                    z-index: 1;
                }
                body.body--light .schedule-calendar-event:hover {
                    filter: brightness(0.96);
                }
                .schedule-calendar-event-title {
                    font-weight: 700;
                    overflow-wrap: anywhere;
                    word-break: break-word;
                }
                .schedule-calendar-event-details {
                    color: var(--calendar-event-details);
                    overflow-wrap: anywhere;
                    word-break: break-word;
                }
                .schedule-calendar-empty {
                    padding: 24px;
                    color: var(--text-muted);
                    text-align: center;
                }

                /* Compact calendar styling for Schedule Comparison */
                .schedule-calendar-compact {
                    min-width: 0;
                    width: 100%;
                }

                .schedule-calendar-compact .schedule-calendar-scroll {
                    min-width: 0;
                    overflow-x: hidden;
                }

                .schedule-calendar-compact .schedule-calendar-grid {
                    min-width: 0;
                }

                .schedule-calendar-compact .schedule-calendar-heading {
                    padding: 8px 3px;
                    font-size: 11px;
                }

                .schedule-calendar-compact .schedule-calendar-time {
                    padding-right: 4px;
                    font-size: 10px;
                }

                .schedule-calendar-compact .schedule-calendar-event {
                    padding: 3px 4px;
                    border-left-width: 3px;
                    font-size: 10px;
                    line-height: 1.2;
                }

                .schedule-calendar-compact .schedule-calendar-event-title {
                    font-size: 10px;
                }

                .schedule-calendar-compact .schedule-calendar-event-details {
                    font-size: 9px;
                }
            </style>
            """
        )

        # add calendar container and content area
        # Normal calendar and toolbar
        self.container = (
            ui.column()
            .classes("w-full gap-2")
            .props('id="schedule-calendar-fullscreen"')
        )

        # updates container if is a compact calendar
        if self.compact:
            self.container.classes("schedule-calendar-compact min-w-0")

        with self.container:
            if not self.compact:
                with ui.row().classes("w-full items-center justify-end gap-2"):
                    ui.button(
                        "Fullscreen",
                        icon="fullscreen",
                        on_click=self._open_fullscreen,
                    ).props("outline")

            self.calendar_content = ui.column().classes("w-full min-w-0 gap-0")

        # Fullscreen pop-up
        # Fullscreen calendar content uses the same calendar container.
        self.popup_calendar_content = self.calendar_content

    # ---------------------------------------------------------
    # Fullscreen Calendar Methods
    # ---------------------------------------------------------

    # Expand the calendar to the browser viewport, or return to normal
    def _open_fullscreen(self) -> None:
        ui.run_javascript(
            """
            const calendar = document.getElementById(
                'schedule-calendar-fullscreen'
            );

            if (!calendar) {
                return;
            }

            if (document.fullscreenElement === calendar) {
                document.exitFullscreen();
            } else if (!document.fullscreenElement) {
                calendar.requestFullscreen();
            }
            """
        )

    # ---------------------------------------------------------
    # Update Calendar
    # ---------------------------------------------------------

    # Replace the calendar contents with the parent's filtered rows.
    def update(
        self,
        filtered_schedule: list[dict],
        selected_day: str | None = None,
        *,
        display_mode: str = "Entire Schedule",
        color_schedule: list[dict] | None = None,
        time_range: tuple[int, int] | None = None,
    ) -> None:
        """Replace the calendar contents with the parent's filtered rows and day."""
        self.filtered_schedule = [row.copy() for row in filtered_schedule]
        self.color_schedule = [
            row.copy()
            for row in (
                color_schedule
                if color_schedule is not None
                else filtered_schedule
            )
        ]
        self.display_mode = display_mode
        self.selected_day = selected_day
        self.time_range = time_range
        self._render()

    # ---------------------------------------------------------
    # Create Calendar Layout
    # ---------------------------------------------------------
    def _render(self) -> None:
        self._render_calendar(self.calendar_content, popup=False)

    def _render_calendar(self, target, popup: bool) -> None:
        target.clear()

        # find the days to display based on the selected day filter
        visible_days = (
            [day for day in DAYS if day[0] == self.selected_day] if self.selected_day else DAYS
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

        # Use a shared time range when provided by Schedule Comparison.
        # Otherwise, calculate the range from this calendar's valid meetings.
        if self.time_range is not None:
            range_start, range_end = self.time_range

            first_hour = max(0, floor(range_start / 60))
            last_hour = min(24, ceil(range_end / 60))

        elif valid_rows:
            first_hour = max(
                0,
                floor(min(start for _, start, _ in valid_rows) / 60),
            )
            last_hour = min(
                24,
                ceil(max(end for _, _, end in valid_rows) / 60),
            )

        else:
            with target:
                message = (
                    "No schedule entries match the current filters."
                    if not self.filtered_schedule
                    else "No entries with valid start and end times."
                )
                ui.label(message).classes(
                    "schedule-calendar-empty w-full"
                )
            return

        if last_hour <= first_hour:
            last_hour = min(24, first_hour + 1)

        range_start = first_hour * 60
        range_end = last_hour * 60
        calendar_height = range_end - range_start
        hour_count = last_hour - first_hour

        # add fullscreen styles to the calendar grid and scroll container if the calendar is in fullscreen mode
        # Compact calendars use a smaller time axis and flexible weekday columns.
        time_column_width = 48 if self.compact else 76
        minimum_day_width = "0" if self.compact or popup else "150px"

        grid_style = (
            f"grid-template-columns: {time_column_width}px repeat("
            f"{len(visible_days)}, minmax({minimum_day_width}, 1fr));"
        )

        if popup:
            grid_style += f"grid-template-rows: 44px repeat({hour_count}, minmax(0, 1fr));"
            scroll_style = "width: 100%; overflow: auto;"
        elif self.compact:
            scroll_style = "width: 100%; overflow-x: hidden;"
        else:
            scroll_style = ""

        # Creates the calendar grid with day headings, time labels, and event blocks for each course
        with (
            target,
            ui.element("div").classes("schedule-calendar-scroll").style(scroll_style),
            ui.element("div")
            .classes("schedule-calendar-grid")
            .style(
                # changes number of columns based on the number of visible days
                grid_style
            ),
        ):
            ui.element("div").classes("schedule-calendar-heading").style(
                "grid-column: 1; grid-row: 1;"
            ).props("aria-label='Time'")

            # Creates the day headings for the calendar grid
            for column, (_, day_name) in enumerate(visible_days, start=2):
                ui.label(day_name).classes("schedule-calendar-heading").style(
                    f"grid-column: {column}; grid-row: 1;"
                )

            # Creates the time labels for the calendar grid
            for hour in range(first_hour, last_hour):
                row_number = hour - first_hour + 2
                ui.label(self._format_time(hour * 60)).classes("schedule-calendar-time").style(
                    f"grid-column: 1; grid-row: {row_number}; height: 60px;"
                )

            # Creates the day columns and positions events within them
            for column, (day_code, _) in enumerate(visible_days, start=2):
                with (
                    ui.element("div")
                    .classes("schedule-calendar-day")
                    .style(
                        f"grid-column: {column}; "
                        f"grid-row: 2 / span {hour_count}; "
                        f"height: {calendar_height}px;"
                    )
                ):
                    day_rows = [
                        (row, start, end)
                        for row, start, end in valid_rows
                        if row.get("day") == day_code
                    ]
                    day_rows.sort(key=lambda item: item[1])

                    # Create event blocks for each course and place them in the correct position based on start and end times

                    # Create event blocks for each course and place them in the correct position.
                    # Compact comparison calendars display at most two event columns.
                    layout = self._layout_day_events(
                        day_rows,
                        max_lanes=2 if self.compact else None,
                    )

                    for row, start, end, lane, lane_count, cluster in layout:
                        # Calculate the event's vertical position
                        top = start - range_start
                        height = max(end - start, 36)

                        # Calculate the event's horizontal position.
                        width = 100 / lane_count
                        left = lane * width

                        course = self._display_value(row.get("course"))
                        background, border_color = self._course_color(course)

                        faculty = self._display_value(row.get("faculty"))
                        resource = self._display_value(row.get("resource"))

                        with (
                            ui.element("div")
                            .classes("schedule-calendar-event cursor-pointer")
                            .style(
                                f"top: {top}px; "
                                f"height: {height}px; "
                                f"left: calc({left}% + 2px); "
                                f"width: calc({width}% - 4px); "
                                "right: auto;"
                                f"background: {background}; "
                                f"border-left-color: {border_color};"
                                + ("text-align: center;" if self.selected_day else "")
                            ) as event
                        ):
                            ui.label(course).classes("schedule-calendar-event-title")
                            ui.label(
                                f"{self._format_time(start)}–{self._format_time(end)}"
                            ).classes("schedule-calendar-event-details")

                            if not self.compact:
                                details_values = (resource,) if self.display_mode == "Faculty" else (
                                    resource,
                                    faculty,
                                )
                                details = " • ".join(
                                    value for value in details_values if value != "—"
                                )
                                if details:
                                    ui.label(details).classes("schedule-calendar-event-details")

                        # Add a click event to the event block that shows the details of the
                        # selected meeting and its overlapping group
                        event.on(
                            "click",
                            lambda r=row, s=start, e=end, c=cluster: self._show_details(
                                r, s, e, c, self.entry_provider()
                            ),
                        )

    # ---------------------------------------------------------
    # Calendar Overlap Helpers
    # ---------------------------------------------------------

    # Side-by-side layout of overlapping meetings.
    # Each meeting gets the first available lane. If a meeting overlaps the meeting
    # currently occupying a lane, it gets another lane. When a meeting ends, its lane can be reused.
    @staticmethod
    def _layout_day_events(
        day_rows: list[tuple[dict, int, int]],
        max_lanes: int | None = None,
    ) -> list[tuple]:
        """Assign meetings to horizontal lanes, respecting an optional lane limit."""
        day_rows = sorted(day_rows, key=lambda item: (item[1], item[2]))
        clusters = []
        current_cluster = []
        cluster_end = -1

        # Group meetings whose time ranges overlap.
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

        # Assign each meeting to a lane.
        for cluster in clusters:
            lane_ends = []
            assigned = []

            for row, start, end in cluster:
                lane = next(
                    (index for index, lane_end in enumerate(lane_ends) if lane_end <= start),
                    None,
                )

                if lane is None:
                    if max_lanes is not None and len(lane_ends) >= max_lanes:
                        # Reuse the final lane when the compact lane limit is reached.
                        lane = max_lanes - 1
                        lane_ends[lane] = max(lane_ends[lane], end)
                    else:
                        lane = len(lane_ends)
                        lane_ends.append(end)
                else:
                    lane_ends[lane] = end

                assigned.append((row, start, end, lane))

            lane_count = max(1, len(lane_ends))

            for row, start, end, lane in assigned:
                layout.append((row, start, end, lane, lane_count, cluster))

        return layout

    # Keep rendering and meeting-details dialogs in separate view modules.
    def _show_details(
        self,
        row: ScheduleRow,
        start: int,
        end: int,
        cluster: OverlapCluster,
        entry: ScheduleEntry | None = None,
    ) -> None:
        show_meeting_details(self, controller, row, start, end, cluster, entry)

        # Return a background and border color for a course.
    def _course_color(self, course: str) -> tuple[str, str]:
        # Use the full schedule so a course keeps its color in every view.
        palette = [
            ("var(--calendar-course-1)", "#75e6da"),
            ("var(--calendar-course-2)", "#b8a4ff"),
            ("var(--calendar-course-3)", "#f0bd82"),
            ("var(--calendar-course-4)", "#8fc5ff"),
            ("var(--calendar-course-5)", "#f2a3bd"),
            ("var(--calendar-course-6)", "#a6dfa9"),
            ("var(--calendar-course-7)", "#ffc078"),
            ("var(--calendar-course-8)", "#2a9d8f"),
            ("var(--calendar-course-9)", "#ff8a80"),
            ("var(--calendar-course-10)", "#f2cc8f"),
            ("var(--calendar-course-11)", "#a3b18a"),
            ("var(--calendar-course-12)", "#e0aaff"),
        ]

        # Use the full schedule so a course keeps its color in every view.
        courses = sorted({str(row.get("course", "")) for row in self.color_schedule})

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
def schedule_calendar_view(
    entry_provider: Callable[[], ScheduleEntry | None] | None = None,
    compact: bool = False,
) -> ScheduleCalendarView:
    """Create and return a calendar view instance."""
    return ScheduleCalendarView(entry_provider=entry_provider, compact=compact)
