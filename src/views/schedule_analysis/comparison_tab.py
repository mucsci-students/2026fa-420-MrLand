
"""Schedule Comparison tab."""

from collections.abc import Callable

from nicegui import ui

from src.controllers.schedule_controller import schedule_controller
from src.views.schedule_analysis.analysis_components import (
    placeholder,
    surface_card,
)

DAYS = {
    None: "All Days",
    "MON": "Monday",
    "TUE": "Tuesday",
    "WED": "Wednesday",
    "THU": "Thursday",
    "FRI": "Friday",
}


def build_comparison_tab(
    on_load_schedule: Callable[[object], None],
) -> Callable[[], None]:
    """Build the Schedule Comparison tab and return its refresh callback."""

    options = schedule_controller.schedule_options()

    initial_value = (
        schedule_controller.selected_index
        if schedule_controller.has_schedules
        else None
    )

    # ---------------------------------------------------------
    # Schedule selectors
    # ---------------------------------------------------------

    with ui.grid(columns=2).classes("w-full gap-4"):

        with surface_card("First Schedule"):
            first_schedule_select = ui.select(
                options,
                value=initial_value,
                label="First Schedule",
            ).classes("w-full").props("outlined")

            ui.button(
                "Load Schedule",
                icon="upload_file",
                on_click=lambda: on_load_schedule(first_schedule_select),
            ).props("outline")

        with surface_card("Second Schedule"):
            second_schedule_select = ui.select(
                options,
                value=initial_value,
                label="Second Schedule",
            ).classes("w-full").props("outlined")

            ui.button(
                "Load Schedule",
                icon="upload_file",
                on_click=lambda: on_load_schedule(second_schedule_select),
            ).props("outline")

    # ---------------------------------------------------------
    # Comparison filters
    # ---------------------------------------------------------

    with surface_card(
        "Comparison Filters",
        "Apply the same filters to both schedules.",
    ), ui.row().classes("w-full items-center flex-wrap gap-3"):

        filter_type_select = (
            ui.select(
                ["Course", "Faculty", "Room / Lab"],
                label="Filter Type",
            )
            .classes("min-w-[170px]")
            .props("outlined clearable")
        )

        filter_value_select = (
            ui.select(
                [],
                label="Filter Value",
            )
            .classes("min-w-[200px]")
            .props("outlined clearable disable")
        )

        day_filter_select = (
            ui.select(
                DAYS,
                value=None,
                label="Day",
            )
            .classes("min-w-[150px]")
            .props("outlined")
        )

        def clear_comparison_filters() -> None:
            """Reset all comparison filters."""
            filter_type_select.value = None
            filter_value_select.value = None
            day_filter_select.value = None

            filter_type_select.update()
            filter_value_select.update()
            day_filter_select.update()

        ui.button(
            "Clear Filters",
            icon="filter_alt_off",
            on_click=clear_comparison_filters,
        ).props("outline color=secondary")

    # ---------------------------------------------------------
    # Nested comparison tabs
    # ---------------------------------------------------------

    with ui.tabs().classes("w-full") as comparison_tabs:
        calendar_tab = ui.tab(
            "Side-by-Side Calendars",
            icon="calendar_month",
        )
        statistics_tab = ui.tab(
            "Statistics",
            icon="bar_chart",
        )

    with ui.tab_panels(
        comparison_tabs,
        value=calendar_tab,
    ).classes("w-full bg-transparent"):

        # Calendar comparison
        with ui.tab_panel(calendar_tab), ui.grid(columns=2).classes(
            "w-full gap-4"
        ):
            with surface_card("First Schedule"):
                placeholder(
                    "First schedule calendar will appear here."
                )

            with surface_card("Second Schedule"):
                placeholder(
                    "Second schedule calendar will appear here."
                )

        # Statistics comparison
        with ui.tab_panel(statistics_tab), surface_card(
            "Statistics Comparison",
            "Compare important metrics between the two schedules.",
        ):
            placeholder(
                "Schedule comparison statistics will appear here."
            )

    # ---------------------------------------------------------
    # Refresh behavior
    # ---------------------------------------------------------

    def refresh() -> None:
        """Update both selectors when schedules are added or refreshed."""
        updated_options = schedule_controller.schedule_options()

        first_value = first_schedule_select.value
        second_value = second_schedule_select.value

        first_schedule_select.options = updated_options
        second_schedule_select.options = updated_options

        # Preserve existing selections when possible.
        if first_value not in updated_options:
            first_value = None

        if second_value not in updated_options:
            second_value = None

        # Give newly available selectors a sensible default.
        if updated_options:
            default_value = schedule_controller.selected_index

            if first_value is None:
                first_value = default_value

            if second_value is None:
                second_value = default_value

        first_schedule_select.value = first_value
        second_schedule_select.value = second_value

        first_schedule_select.update()
        second_schedule_select.update()

    return refresh
