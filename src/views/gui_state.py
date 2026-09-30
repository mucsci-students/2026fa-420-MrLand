"""Shared state for the GUI tabs (replaces the CLI's module-level globals).

Import this as `from views.gui_state import state` everywhere, so every tab
shares the same object.
"""

from dataclasses import dataclass, field

from schedule_result import ScheduleResult


@dataclass
class AppState:
    current_config: object | None = None
    config_name: str | None = None
    schedules: list[ScheduleResult] = field(default_factory=list)

    # Schedule Viewer UI state
    selected_schedule: int = 0
    viewer_mode: str = "table"        # "table" | "week"
    week_filter: str | None = None    # "all" | "faculty::<name>" | "place::<room or lab>"


state = AppState()