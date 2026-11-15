"""Schedule Comparison tab."""

from collections.abc import Callable

from nicegui import ui

from src.controllers.schedule_controller import schedule_controller
from src.views.schedule_analysis.analysis_components import surface_card
from src.views.schedule_calendar_view import schedule_calendar_view

DAYS = {
    None: "All Days",
    "MON": "Monday",
    "TUE": "Tuesday",
    "WED": "Wednesday",
    "THU": "Thursday",
    "FRI": "Friday",
}

FILTER_FIELDS = {
    "Course": "course",
    "Faculty": "faculty",
    "Room / Lab": "resource",
}


def build_comparison_tab(
    on_load_schedule: Callable[[object], None],
) -> Callable[[], None]:
    """Build the schedule comparison workspace and return its refresh callback."""

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
    # Shared comparison filters
    # ---------------------------------------------------------

    with (
        surface_card(
            "Comparison Filters",
            "Apply the same filters to both schedules.",
        ),
        ui.row().classes("w-full items-end gap-3 flex-wrap"),
    ):
        filter_type_select = (
            ui.select(
                list(FILTER_FIELDS),
                value=None,
                label="Filter By",
            )
            .props("outlined")
            .classes("min-w-[160px] flex-1")
        )

        filter_value_select = (
            ui.select(
                [],
                value=None,
                label="Filter Value",
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
            "Clear Filters",
            icon="filter_alt_off",
            on_click=lambda: clear_filters(),
        ).props("outline")

    # ---------------------------------------------------------
    # Schedule helpers
    # ---------------------------------------------------------

    def selected_index(select) -> int | None:
        """Return a selector's value as an integer index."""
        try:
            return int(select.value) if select.value is not None else None
        except (TypeError, ValueError):
            return None

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

    # ---------------------------------------------------------
    # Filter handling
    # ---------------------------------------------------------

    def update_filter_values() -> None:
        """Build filter choices from the two selected schedules."""
        field = FILTER_FIELDS.get(filter_type_select.value)

        if field is None:
            filter_value_select.options = []
            filter_value_select.value = None
            filter_value_select.update()
            return

        rows = selected_rows(first_schedule_select)
        rows.extend(selected_rows(second_schedule_select))

        values = sorted(
            {str(row.get(field, "")) for row in rows if row.get(field) not in (None, "")}
        )

        previous_value = filter_value_select.value
        filter_value_select.options = values
        filter_value_select.value = previous_value if previous_value in values else None
        filter_value_select.update()

    def apply_filters(rows: list[dict]) -> list[dict]:
        """Apply the shared comparison filters to one schedule."""
        field = FILTER_FIELDS.get(filter_type_select.value)
        value = filter_value_select.value
        selected_day = day_filter_select.value

        if field is not None and value is not None:
            rows = [row for row in rows if str(row.get(field, "")) == str(value)]

        if selected_day is not None:
            rows = [row for row in rows if row.get("day") == selected_day]

        return rows

    def update_calendars() -> None:
        """Refresh both calendars using their own selected schedules."""
        first_rows = apply_filters(selected_rows(first_schedule_select))
        second_rows = apply_filters(selected_rows(second_schedule_select))

        selected_day = day_filter_select.value

        first_calendar.update(first_rows, selected_day)
        second_calendar.update(second_rows, selected_day)

    def refresh_comparison() -> None:
        """Update selections, filter choices, and both calendars."""
        validate_selections()
        update_filter_values()
        update_calendars()

    def clear_filters() -> None:
        """Reset all shared comparison filters."""
        filter_type_select.value = None
        filter_value_select.value = None
        day_filter_select.value = None

        update_filter_values()
        update_calendars()

    # ---------------------------------------------------------
    # Calendar display
    # ---------------------------------------------------------

    with ui.element("div").classes("grid grid-cols-1 md:grid-cols-2 gap-4 w-full min-w-0"):
        with surface_card("First Schedule Calendar"):
            first_calendar = schedule_calendar_view(
                entry_provider=lambda: selected_entry(first_schedule_select),
                compact=True,
            )

        with surface_card("Second Schedule Calendar"):
            second_calendar = schedule_calendar_view(
                entry_provider=lambda: selected_entry(second_schedule_select),
                compact=True,
            )

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
        refresh_comparison()

    first_schedule_select.on_value_change(lambda _: refresh_comparison())
    second_schedule_select.on_value_change(lambda _: refresh_comparison())

    filter_type_select.on_value_change(lambda _: refresh_comparison())
    filter_value_select.on_value_change(lambda _: update_calendars())
    day_filter_select.on_value_change(lambda _: update_calendars())

    # ---------------------------------------------------------
    # External refresh
    # ---------------------------------------------------------

    def refresh() -> None:
        """Refresh schedule choices after schedules are loaded or generated."""
        nonlocal options

        options = schedule_controller.schedule_options()

        first_current = selected_index(first_schedule_select)
        second_current = selected_index(second_schedule_select)

        if first_current not in options:
            first_current = (
                schedule_controller.selected_index if schedule_controller.has_schedules else None
            )

        if second_current not in options:
            second_current = None

        # Keep the selectors distinct when schedules are added or removed.
        if first_current is not None and first_current == second_current:
            second_current = None

        # Automatically populate the second selector when another
        # schedule becomes available.
        if second_current is None and len(options) > 1:
            second_current = next(
                (index for index in options if index != first_current),
                None,
            )

        # A single schedule cannot be compared against itself.
        if len(options) <= 1:
            second_current = None

        first_schedule_select.options = options
        second_schedule_select.options = options

        first_schedule_select.value = first_current
        second_schedule_select.value = second_current

        first_schedule_select.update()
        second_schedule_select.update()

        # These are intentional external changes, not user selections.
        previous_selections["first"] = first_current
        previous_selections["second"] = second_current

        refresh_comparison()

    # Initial render
    refresh_comparison()

    return refresh
