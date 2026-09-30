from nicegui import ui


def section_header(eyebrow: str, title: str, description: str) -> None:
    with ui.column().classes("gap-1"):
        ui.label(eyebrow.upper()).classes(
            "text-xs font-bold tracking-[0.2em] text-[#75e6da]"
        )
        ui.label(title).classes("text-3xl font-semibold text-white")
        ui.label(description).classes("max-w-2xl text-sm text-[#9fb2b8]")


def status_card(title: str, value: str, detail: str, icon: str) -> None:
    with ui.card().classes("min-w-[180px] flex-1 border border-[#29404b] bg-[#182630] p-4"):
        with ui.row().classes("w-full items-center justify-between"):
            ui.label(title).classes("text-xs uppercase tracking-wider text-[#9fb2b8]")
            ui.icon(icon).classes("text-[#75e6da]")
        ui.label(value).classes("mt-3 text-2xl font-semibold text-white")
        ui.label(detail).classes("text-xs text-[#9fb2b8]")


def coming_soon(action: str) -> None:
    ui.notify(f"{action} coming soon")