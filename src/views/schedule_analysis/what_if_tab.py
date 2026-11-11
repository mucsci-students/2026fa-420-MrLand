"""What-If Analysis tab."""

from nicegui import ui

from src.views.schedule_analysis.analysis_components import (
    placeholder,
    surface_card,
)


def build_what_if_tab() -> None:
    """Build the What-If Analysis tab layout."""

    # Configuration and generation controls
    with ui.grid(columns=2).classes("w-full gap-4"):
        with surface_card(
            "Temporary Configuration",
            "Make temporary changes without modifying your saved configuration.",
        ):
            placeholder("Temporary configuration editor will appear here.")

            ui.button(
                "Edit Configuration",
                icon="edit",
            ).props("outline")

        with surface_card(
            "Generate Alternative Schedule",
            "Generate a schedule using your temporary configuration.",
        ):
            placeholder("Alternative schedule generation controls will appear here.")

            ui.button(
                "Generate Alternative",
                icon="auto_awesome",
            ).props("outline")

    # Alternative results
    with surface_card(
        "Alternative Results",
        "Review the schedule generated from your temporary configuration.",
    ):
        placeholder("Your alternative schedule will appear here.")
