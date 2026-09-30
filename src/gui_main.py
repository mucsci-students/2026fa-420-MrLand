"""Entry point for the MrLand Scheduler GUI.

Run from the repository root, the same way as the CLI:

    python src/gui_main.py

Running this file puts src/ on the import path, so `services`, `schedule_result`,
`run_scheduler`, and the `views` package all resolve the way they do for navmenu.py.
Set MRLAND_GUI_PORT to use a port other than 8080.
"""

import os

from nicegui import ui

from views.gui import build_app


@ui.page("/")
def index() -> None:
    build_app()


if __name__ in {"__main__", "__mp_main__"}:
    ui.run(
        title="MrLand Scheduler",
        reload=False,
        port=int(os.environ.get("MRLAND_GUI_PORT", "8080")),
    )