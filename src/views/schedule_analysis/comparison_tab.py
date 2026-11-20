"""Schedule Comparison tab."""

from collections.abc import Callable
from typing import Protocol

from nicegui import ui

from src.controllers.schedule_controller import schedule_controller
from src.views.schedule_analysis.analysis_components import surface_card
from src.views.schedule_analysis.statistics_tab import (
    build_statistics_comparison_panel,
)
from src.views.schedule_calendar_view import schedule_calendar_view

DAYS = {
    None: "All Days",
    "MON": "Monday",
    "TUE": "Tuesday",
    "WED": "Wednesday",
    "THU": "Thursday",
    "FRI": "Friday",
}

VIEW_FIELDS = {
    "Faculty": "faculty",
    "Room / Lab": "resource",
    "Entire Schedule": None,
}


class ComparisonRefresh(Protocol):
    """Callable used to refresh the comparison tab."""

    def __call__(
        self,
        changed_select: object | None = None,
        selected_index_override: int | None = None,
    ) -> None: ...


def build_comparison_tab(
    on_load_schedule: Callable[[object], None],
) -> ComparisonRefresh:
    """Build the schedule comparison workspace and return its refresh callback."""

    def toggle_comparison_fullscreen() -> None:
        """Toggle fullscreen mode for the complete comparison view."""
        ui.run_javascript(
            """
            const comparison = document.getElementById(
                'schedule-comparison-fullscreen'
            );

            if (!comparison) {
                return;
            }

            if (document.fullscreenElement === comparison) {
                document.exitFullscreen();
            } else if (!document.fullscreenElement) {
                comparison.requestFullscreen();
            }
            """
        )

    # css styling for fullscreen comparison
    ui.add_head_html(
        """
        <style>
            #schedule-comparison-fullscreen:fullscreen {
                width: 100%;
                height: 100%;
                max-height: 100%;
                box-sizing: border-box;
                overflow-y: auto;
                overflow-x: hidden;
                padding: 16px;
                background: var(--app-background);
            }
        </style>
        """
    )

    options = schedule_controller.schedule_options()
    first_value = schedule_controller.selected_index if schedule_controller.has_schedules else None

    second_value = None
    if len(options) > 1:
        second_value = next(index for index in options if index != first_value)

    # ---------------------------------------------------------
    # Schedule selection
    # ---------------------------------------------------------

    with ui.element("div").classes("grid grid-cols-1 md:grid-cols-2 gap-4 w-full min-w-0"):
        with surface_card("First Schedule"):
            first_schedule_select = (
                ui.select(
                    options,
                    value=first_value,
                    label="First Schedule",
                )
                .classes("w-full")
                .props("outlined")
            )

            ui.button(
                "Load Schedule",
                icon="upload_file",
                on_click=lambda: on_load_schedule(first_schedule_select),
            ).props("outline")

        with surface_card("Second Schedule"):
            second_schedule_select = (
                ui.select(
                    options,
                    value=second_value,
                    label="Second Schedule",
                )
                .classes("w-full")
                .props("outlined")
            )

            ui.button(
                "Load Schedule",
                icon="upload_file",
                on_click=lambda: on_load_schedule(second_schedule_select),
            ).props("outline")

    # ---------------------------------------------------------
    # View and Stat tab creation
    # ---------------------------------------------------------

    with ui.tabs().classes("w-full") as comparison_tabs:
        view_tab = ui.tab("View", icon="calendar_month")
        statistics_tab = ui.tab("Statistics", icon="analytics")

    with ui.tab_panels(comparison_tabs, value=view_tab).classes("w-full"):
        with (
            ui.tab_panel(view_tab),
            ui.element("div")
            .props('id="schedule-comparison-fullscreen"')
            .classes("w-full min-w-0"),
            ui.column().classes("w-full min-w-0 gap-4"),
        ):
            # ---------------------------------------------------------
            # Shared View By controls
            # ---------------------------------------------------------
            with (
                surface_card(
                    "View By",
                    "Apply the same view settings to both schedules.",
                ),
                ui.row().classes("w-full items-end gap-3 flex-wrap"),
            ):
                view_by_select = (
                    ui.select(
                        list(VIEW_FIELDS),
                        value="Faculty",
                        label="View By",
                    )
                    .props("outlined")
                    .classes("min-w-[160px] flex-1")
                )

                filter_value_select = (
                    ui.select(
                        [],
                        value=None,
                        label="Faculty / Room/Lab Value",
                    )
                    .props("outlined")
                    .classes("min-w-[180px] flex-1")
                )

                day_filter_select = (
                    ui.select(
                        DAYS,
                        value=None,
                        label="Day",
                    )
                    .props("outlined")
                    .classes("min-w-[150px] flex-1")
                )

                ui.button(
                    "Fullscreen",
                    icon="fullscreen",
                    on_click=toggle_comparison_fullscreen,
                ).props("outline").classes("h-14")

            # ---------------------------------------------------------
            # Calendar display
            # ---------------------------------------------------------
            with ui.element("div").classes("grid grid-cols-1 md:grid-cols-2 gap-4 w-full min-w-0"):
                with surface_card("First Schedule Calendar"):
                    first_view_title = ui.label("No Schedule Selected").classes(
                        "text-lg font-semibold"
                    )

                    first_calendar = schedule_calendar_view(
                        entry_provider=lambda: selected_entry(first_schedule_select),
                        compact=True,
                    )

                with surface_card("Second Schedule Calendar"):
                    second_view_title = ui.label("No Schedule Selected").classes(
                        "text-lg font-semibold"
                    )

                    second_calendar = schedule_calendar_view(
                        entry_provider=lambda: selected_entry(second_schedule_select),
                        compact=True,
                    )

        with (
            ui.tab_panel(statistics_tab),
            ui.element("div").classes("grid grid-cols-1 lg:grid-cols-2 gap-4 w-full min-w-0"),
        ):
            first_statistics_refresh, first_statistics_title = build_statistics_comparison_panel(
                "No Schedule Selected"
            )

            second_statistics_refresh, second_statistics_title = build_statistics_comparison_panel(
                "No Schedule Selected"
            )

    # ---------------------------------------------------------
    # Schedule helpers
    # ---------------------------------------------------------

    def selected_index(select) -> int | None:
        """Return a selector's value as an integer index."""
        try:
            return int(select.value) if select.value is not None else None
        except (TypeError, ValueError):
            return None

    def update_selector_options() -> None:
        """Hide the schedule selected in one dropdown from the other dropdown."""
        first = selected_index(first_schedule_select)
        second = selected_index(second_schedule_select)

        first_schedule_select.options = {
            index: label for index, label in options.items() if index != second
        }

        second_schedule_select.options = {
            index: label for index, label in options.items() if index != first
        }

        first_schedule_select.update()
        second_schedule_select.update()

    def selected_entry(select):
        """Get the entry associated with one comparison selector."""
        index = selected_index(select)
        return schedule_controller.entry_at(index) if index is not None else None

    def selected_rows(select) -> list[dict]:
        """Get the meeting rows for one comparison selector."""
        index = selected_index(select)
        return schedule_controller.rows_for(index) if index is not None else []

    # Track the previous selections so a duplicate selection can move
    # the other selector to a different schedule.
    previous_selections = {
        "first": first_value,
        "second": second_value,
    }

    def validate_selections() -> bool:
        """Reject duplicate schedule selections and restore the previous value."""
        first = selected_index(first_schedule_select)
        second = selected_index(second_schedule_select)

        if first is not None and first == second:
            first_changed = first != previous_selections["first"]
            second_changed = second != previous_selections["second"]

            # Restore whichever selector was changed.
            if first_changed and not second_changed:
                first_schedule_select.value = previous_selections["first"]
                first_schedule_select.update()
            else:
                second_schedule_select.value = previous_selections["second"]
                second_schedule_select.update()

            ui.notify(
                "You cannot compare a schedule against itself. "
                "Please select two different schedules.",
                type="warning",
            )
            return False

        previous_selections["first"] = first
        previous_selections["second"] = second
        return True

    def update_statistics() -> None:
        """Refresh statistics for both selected schedules."""
        first_statistics_refresh(selected_entry(first_schedule_select))
        second_statistics_refresh(selected_entry(second_schedule_select))

    def update_schedule_names() -> None:
        """Update statistics and calendar headings using selected schedule names."""
        first_entry = selected_entry(first_schedule_select)
        second_entry = selected_entry(second_schedule_select)

        first_name = first_entry.label if first_entry else "No Schedule Selected"
        second_name = second_entry.label if second_entry else "No Schedule Selected"

        first_view_title.text = first_name
        second_view_title.text = second_name

        first_view_title.update()
        second_view_title.update()

        first_statistics_title(first_name)
        second_statistics_title(second_name)

    # ---------------------------------------------------------
    # View By handling
    # ---------------------------------------------------------

    def shared_time_range() -> tuple[int, int] | None:
        """Calculate one time range using both complete schedules."""
        rows = selected_rows(first_schedule_select) + selected_rows(second_schedule_select)

        valid_times = []

        for row in rows:
            try:
                start = first_calendar._to_minutes(row["start"])
                end = first_calendar._to_minutes(row["end"])

                if end > start:
                    valid_times.append((start, end))

            except (KeyError, TypeError, ValueError):
                continue

        if not valid_times:
            return None

        earliest_start = min(start for start, _ in valid_times)
        latest_end = max(end for _, end in valid_times)

        # Round the shared range to whole hours.
        first_hour = earliest_start // 60
        last_hour = (latest_end + 59) // 60

        return first_hour * 60, last_hour * 60

    def update_filter_values() -> None:
        """Build faculty or room/lab choices from the two selected schedules."""
        field = VIEW_FIELDS.get(view_by_select.value)

        # Entire Schedule does not need a faculty or room/lab selection.
        if field is None:
            filter_value_select.options = []
            filter_value_select.value = None
            filter_value_select.disable()
            filter_value_select.update()
            return

        rows = selected_rows(first_schedule_select) + selected_rows(second_schedule_select)

        if field == "resource":
            resource_values = {
                str(row.get("resource"))
                for row in rows
                if row.get("resource") not in (None, "", "Online", "Unassigned")
            }

            for select in (first_schedule_select, second_schedule_select):
                entry = selected_entry(select)

                if entry is None:
                    continue

                for record in entry.records:
                    for resource in (record.get("room"), record.get("lab")):
                        if resource and resource not in {"Online", "Unassigned"}:
                            resource_values.add(str(resource))

            values = sorted(resource_values)
        else:
            values = sorted(
                {str(row.get(field, "")) for row in rows if row.get(field) not in (None, "")}
            )

        previous_value = filter_value_select.value
        filter_value_select.options = values

        # Keep the previous selection when possible.
        # Otherwise, select the first available option by default.
        if previous_value in values:
            filter_value_select.value = previous_value
        else:
            filter_value_select.value = values[0] if values else None

        if values:
            filter_value_select.enable()
        else:
            filter_value_select.disable()

        filter_value_select.update()

    def apply_filters(rows: list[dict], select) -> list[dict]:
        """Apply the shared comparison view settings to one schedule."""
        field = VIEW_FIELDS.get(view_by_select.value)
        value = filter_value_select.value
        selected_day = day_filter_select.value

        if field == "resource" and value is not None:
            entry = selected_entry(select)
            records = entry.records if entry is not None else []

            # Find courses connected to the selected room or lab.
            matching_courses = {
                record.get("course")
                for record in records
                if value in (record.get("room"), record.get("lab")) and record.get("course")
            }

            if matching_courses:
                rows = [row for row in rows if row.get("course") in matching_courses]
            else:
                rows = [row for row in rows if str(row.get("resource", "")) == str(value)]

        elif field is not None and value is not None:
            rows = [row for row in rows if str(row.get(field, "")) == str(value)]

        if selected_day is not None:
            rows = [row for row in rows if row.get("day") == selected_day]

        return rows

    def update_calendars() -> None:
        """Refresh both calendars using their own schedules and shared time axis."""
        first_rows = apply_filters(
            selected_rows(first_schedule_select),
            first_schedule_select,
        )
        second_rows = apply_filters(
            selected_rows(second_schedule_select),
            second_schedule_select,
        )

        selected_day = day_filter_select.value
        time_range = shared_time_range()

        first_calendar.update(
            first_rows,
            selected_day,
            time_range=time_range,
            color_schedule=selected_rows(first_schedule_select),
        )

        second_calendar.update(
            second_rows,
            selected_day,
            time_range=time_range,
            color_schedule=selected_rows(second_schedule_select),
        )

    def refresh_comparison(changed_select=None) -> None:
        """Refresh the affected comparison column and shared view controls."""
        if not validate_selections():
            return

        update_filter_values()

        # Both calendars must refresh because their time axis is shared.
        update_calendars()

        # A full refresh updates both columns.
        if changed_select is None:
            update_schedule_names()
            update_statistics()
            return

        # A targeted refresh updates only the selected column's heading
        # and statistics. Both calendars have already been refreshed above.
        if changed_select is first_schedule_select:
            first_entry = selected_entry(first_schedule_select)
            first_name = first_entry.label if first_entry else "No Schedule Selected"

            first_view_title.text = first_name
            first_view_title.update()

            first_statistics_title(first_name)
            first_statistics_refresh(first_entry)

        elif changed_select is second_schedule_select:
            second_entry = selected_entry(second_schedule_select)
            second_name = second_entry.label if second_entry else "No Schedule Selected"

            second_view_title.text = second_name
            second_view_title.update()

            second_statistics_title(second_name)
            second_statistics_refresh(second_entry)

    # ---------------------------------------------------------
    # Selector events
    # ---------------------------------------------------------

    def handle_schedule_change(changed: str) -> None:
        """Reject duplicate selections and refresh the comparison."""
        first = selected_index(first_schedule_select)
        second = selected_index(second_schedule_select)

        if first is not None and first == second:
            if changed == "first":
                first_schedule_select.value = previous_selections["first"]
                first_schedule_select.update()
            else:
                second_schedule_select.value = previous_selections["second"]
                second_schedule_select.update()

            ui.notify(
                "You cannot compare a schedule against itself. "
                "Please select two different schedules.",
                type="warning",
            )
            return

        previous_selections["first"] = first
        previous_selections["second"] = second

        update_selector_options()
        refresh_comparison()

    first_schedule_select.on_value_change(lambda _: handle_schedule_change("first"))
    second_schedule_select.on_value_change(lambda _: handle_schedule_change("second"))

    view_by_select.on_value_change(lambda _: refresh_comparison())
    filter_value_select.on_value_change(lambda _: update_calendars())
    day_filter_select.on_value_change(lambda _: update_calendars())

    # ---------------------------------------------------------
    # External refresh
    # ---------------------------------------------------------

    def refresh(changed_select=None, selected_index_override=None) -> None:
        """Refresh schedule choices while preserving independent selections."""
        nonlocal options

        options = schedule_controller.schedule_options()

        first_current = selected_index(first_schedule_select)
        second_current = selected_index(second_schedule_select)

        # Apply an uploaded schedule to only the requested selector.
        if changed_select is first_schedule_select:
            first_current = selected_index_override

        elif changed_select is second_schedule_select:
            second_current = selected_index_override

        if first_current not in options:
            first_current = None

        if second_current not in options:
            second_current = None

        if first_current is not None and first_current == second_current:
            if changed_select is first_schedule_select:
                second_current = None
            else:
                first_current = None

        first_schedule_select.options = options
        second_schedule_select.options = options

        first_schedule_select.value = first_current
        second_schedule_select.value = second_current

        update_selector_options()

        previous_selections["first"] = first_current
        previous_selections["second"] = second_current

        refresh_comparison(changed_select)

    # Initial render
    refresh_comparison()

    return refresh
