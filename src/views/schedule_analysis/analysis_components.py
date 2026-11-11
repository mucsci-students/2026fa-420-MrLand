"""Shared UI components for the Schedule Analysis page."""

from collections.abc import Generator
from contextlib import contextmanager

from nicegui import ui


@contextmanager
def surface_card(
    title: str,
    subtitle: str | None = None,
) -> Generator:
    """Create a floating card that follows the active application theme."""
    card = (
        ui.card()
        .classes("w-full min-w-0 gap-3 p-5")
        .style(
            "background: var(--surface); "
            "color: var(--app-foreground); "
            "border: 1px solid var(--border-color); "
            "border-radius: 14px; "
            "box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);"
        )
    )

    with card:
        ui.label(title).classes("text-lg font-semibold").style("color: var(--text-primary)")

        if subtitle:
            ui.label(subtitle).classes("text-sm").style("color: var(--text-muted)")

        yield card


def placeholder(message: str) -> None:
    """Display a placeholder for functionality that will be implemented later."""
    ui.label(message).classes("text-sm").style("color: var(--text-muted)")


def placeholder_table(
    columns: list[str],
    message: str = "No data available yet.",
) -> None:
    """Display a placeholder table."""
    with ui.column().classes("w-full gap-2"):
        ui.label(" | ".join(columns)).classes("font-semibold")
        placeholder(message)
