"""Shared NiceGUI helpers for applying configuration changes."""

from collections.abc import Callable
from contextlib import contextmanager
from typing import Any, Iterator

from nicegui import ui
from nicegui.element import Element
from nicegui.elements.mixins.value_element import ValueElement

ConfigurationChangeHandler = Callable[[Callable[[], object]], bool]
PendingChangeHandler = Callable[[bool], None]


class PendingFormChanges:
    """Track edited form values that have not yet been applied."""

    def __init__(
        self,
        form: Element,
        on_change: PendingChangeHandler | None,
    ) -> None:
        self._form = form
        self._on_change = on_change
        self._pending = False
        self._suspended = False

    def watch(self, *fields: ValueElement[Any]) -> None:
        for field in fields:
            field.on_value_change(self._value_changed)

    def mark_pending(self) -> None:
        self._set_pending(True)

    def clear(self) -> None:
        self._set_pending(False)

    @contextmanager
    def suspend(self) -> Iterator[None]:
        previous = self._suspended
        self._suspended = True
        try:
            yield
        finally:
            self._suspended = previous

    def _value_changed(self, event) -> None:
        if (
            self._suspended
            or not self._form.visible
            or event.value == event.previous_value
        ):
            return
        self.mark_pending()

    def _set_pending(self, pending: bool) -> None:
        if self._pending == pending:
            return
        self._pending = pending
        if self._on_change is not None:
            self._on_change(pending)


def run_configuration_change(
    on_change: ConfigurationChangeHandler | None,
    mutation: Callable[[], object],
) -> bool:
    
    """Route edits through the editor's validation callback when one is provided."""
    if on_change is None:
        mutation()
        return True
    
    return on_change(mutation)


def run_crud_mutation(
    on_change: ConfigurationChangeHandler | None,
    mutation: Callable[[], object],
    *,
    handled_errors: tuple[type[Exception], ...] = (TypeError, ValueError),
) -> bool:
    
    """Apply one GUI CRUD mutation and report validation errors consistently."""

    try:
        return run_configuration_change(on_change, mutation)
    
    except handled_errors as exc:
        ui.notify(str(exc), type="negative")
        return False


def parse_whole_number(value: object, error_message: str) -> int:
    """Parse a numeric form value as an integer with a page-specific error."""
    try:
        number = float(value)

    except (TypeError, ValueError) as exc:
        raise ValueError(error_message) from exc
    
    if not number.is_integer():
        raise ValueError(error_message)
    
    return int(number)


def section_header(eyebrow: str, title: str, description: str) -> None:
    """Render a shared section heading with a label, title, and description."""

    with ui.column().classes("gap-1"):
        ui.label(eyebrow.upper()).classes("text-xs font-bold tracking-[0.2em] text-[#75e6da]")
        ui.label(title).classes("text-3xl font-semibold text-white")
        ui.label(description).classes("max-w-2xl text-sm text-[#9fb2b8]")


def status_card(title: str, value: str, detail: str, icon: str) -> None:
    """Render a compact card summarizing a value and its supporting detail."""
    
    with ui.card().classes("min-w-[180px] flex-1 border border-[#29404b] bg-[#182630] p-4"):
        with ui.row().classes("w-full items-center justify-between"):
            ui.label(title).classes("text-xs uppercase tracking-wider text-[#9fb2b8]")
            ui.icon(icon).classes("text-[#75e6da]")
        ui.label(value).classes("mt-3 text-2xl font-semibold text-white")
        ui.label(detail).classes("text-xs text-[#9fb2b8]")


def coming_soon(action: str) -> None:
    """Notify the user that the selected editor action is not yet available."""

    ui.notify(f"{action} coming soon")
