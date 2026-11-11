
"""Schedule Comparison tab."""

from nicegui import ui

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


def build_comparison_tab() -> None:
    """Build the Schedule Comparison tab layout."""

    # Schedule selectors
    with ui.grid(columns=2).classes("w-full gap-4"):
        schedule_one_select = ui.select(
            {},
            label="First Schedule",
        ).classes("w-full").props("outlined")

        schedule_two_select = ui.select(
            {},
            label="Second Schedule",
        ).classes("w-full").props("outlined")

    # Comparison filters
    with surface_card(
        "Comparison Filters",
        "Apply the same filters to both schedules.",
    ):
        with ui.row().classes("w-full items-center flex-wrap gap-3"):
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

    # Nested comparison tabs
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
        with ui.tab_panel(calendar_tab):
            with ui.grid(columns=2).classes("w-full gap-4"):
                with surface_card("First Schedule"):
                    placeholder(
                        "First schedule calendar will appear here."
                    )

                with surface_card("Second Schedule"):
                    placeholder(
                        "Second schedule calendar will appear here."
                    )

        # Statistics comparison
        with ui.tab_panel(statistics_tab):
            with surface_card(
                "Statistics Comparison",
                "Compare important metrics between the two schedules.",
            ):
                placeholder(
                    "Schedule comparison statistics will appear here."
                )
