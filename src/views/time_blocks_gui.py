from nicegui import ui

from src.services.time_block_service import (
    add_time_block_from_values,
    delete_time_block_from_values,
    update_time_block_from_values,
)

DAYS = ("MON", "TUE", "WED", "THU", "FRI")


def time_blocks_gui(times: dict) -> None:
    ui.label("Time blocks").classes("text-xl font-semibold text-white")
    ui.label("Define the available scheduling window for each weekday.").classes(
        "text-sm text-[#9fb2b8]"
    )
    ui.label("Existing time blocks").classes(
        "mt-4 text-lg font-semibold text-white"
    )
    block_list = ui.column().classes("w-full gap-1")

    with ui.row().classes("w-full flex-wrap items-center gap-2"):
        add_button = ui.button("Add new time block", icon="add", on_click=lambda: show_form()).props(
            "unelevated"
        ).classes("bg-[#75e6da] text-[#101820]")

    with ui.column().classes("w-full gap-4 mt-6") as form_container:
        form_container.set_visibility(False)
        form_heading = ui.label("Add New Time Block").classes("text-lg font-semibold text-white")

        with ui.row().classes("w-full flex-wrap gap-4"):
            day = ui.select(list(DAYS), value="MON", label="Day").classes("min-w-40")
            start = ui.input("Start time").props("type=time").classes("w-40")
            spacing = ui.number("Spacing (minutes)", value=30, min=1, step=1).classes(
                "w-48"
            )
            end = ui.input("End time").props("type=time").classes("w-40")

        editing_block = {"day": None, "block": None}

        def form_values():
            spacing_value = spacing.value
            if spacing_value is None or not float(spacing_value).is_integer():
                raise ValueError("Spacing must be a whole number of minutes.")
            return day.value, start.value or "", int(spacing_value), end.value or ""

        def show_form() -> None:
            editing_block["day"] = None
            editing_block["block"] = None
            form_heading.set_text("Add New Time Block")
            day.value = "MON"
            start.value = ""
            spacing.value = 30
            end.value = ""
            form_container.set_visibility(True)
            add_submit_button.set_visibility(True)
            update_button.set_visibility(False)
            cancel_button.set_visibility(True)

        def reset_form() -> None:
            editing_block["day"] = None
            editing_block["block"] = None
            form_heading.set_text("Add New Time Block")
            day.value = "MON"
            start.value = ""
            spacing.value = 30
            end.value = ""
            form_container.set_visibility(False)
            add_submit_button.set_visibility(True)
            update_button.set_visibility(False)
            cancel_button.set_visibility(False)

        def add_block() -> None:
            try:
                add_time_block_from_values(times, *form_values())
            except (TypeError, ValueError) as exc:
                ui.notify(str(exc), type="negative")
                return
            reset_form()
            refresh_blocks()
            ui.notify("Time block added.", type="positive")

        def update_block() -> None:
            try:
                update_time_block_from_values(
                    times,
                    editing_block["day"],
                    editing_block["block"],
                    *form_values(),
                )
            except (TypeError, ValueError) as exc:
                ui.notify(str(exc), type="negative")
                return
            reset_form()
            refresh_blocks()
            ui.notify("Time block updated.", type="positive")

        def begin_edit(block_day, block) -> None:
            editing_block["day"] = block_day
            editing_block["block"] = block
            form_heading.set_text("Modifying Time Block")
            day.value = block_day
            start.value = block.start
            spacing.value = block.spacing
            end.value = block.end
            form_container.set_visibility(True)
            add_submit_button.set_visibility(False)
            update_button.set_visibility(True)
            cancel_button.set_visibility(True)

        def delete_block(block_day, block, dialog) -> None:
            try:
                delete_time_block_from_values(times, block_day, block)
            except ValueError as exc:
                ui.notify(str(exc), type="negative")
                dialog.close()
                return
            if editing_block["block"] is block:
                reset_form()
            ui.notify("Time block deleted.", type="positive")
            dialog.close()
            refresh_blocks()

        with ui.row().classes("w-full flex-wrap items-center gap-2"):
            add_submit_button = ui.button("Create time block", icon="add", on_click=add_block).props(
                "unelevated"
            ).classes("bg-[#75e6da] text-[#101820]")
            cancel_button = ui.button("Cancel", on_click=reset_form).props(
                "outline"
            ).classes("border-[#45616b] text-[#d8e7e8]")
            cancel_button.set_visibility(False)
            update_button = ui.button(
                "Save changes", icon="save", on_click=update_block
            ).props("unelevated").classes("bg-[#75e6da] text-[#101820]")
            update_button.set_visibility(False)

    def refresh_blocks() -> None:
        block_list.clear()
        with block_list:
            has_blocks = any(times.get(weekday) for weekday in DAYS)
            if not has_blocks:
                ui.label("No time blocks added yet.").classes(
                    "text-sm text-[#9fb2b8]"
                )
                return
            for weekday in DAYS:
                for index, block in enumerate(times.get(weekday, []), start=1):
                    with ui.row().classes(
                        "w-full items-center justify-between gap-4 border-b border-[#29404b] py-3"
                    ):
                        with ui.column().classes("min-w-0 gap-1"):
                            ui.label(
                                f"{weekday}  |  {block.start}-{block.end}"
                            ).classes("font-semibold text-white")
                            ui.label(
                                f"Spacing: {block.spacing} minutes  |  Block {index}"
                            ).classes("break-words text-sm text-[#9fb2b8]")
                        with ui.row().classes("shrink-0 items-center gap-1"):
                            ui.button(
                                icon="edit",
                                on_click=lambda selected_day=weekday, selected=block: begin_edit(
                                    selected_day, selected
                                ),
                            ).props("flat round dense").tooltip("Edit time block")
                            with ui.dialog() as dialog, ui.card().classes(
                                "border border-[#29404b] bg-[#182630]"
                            ):
                                ui.label(
                                    f"Delete {weekday} {block.start}-{block.end}?"
                                ).classes("text-lg font-semibold text-white")
                                ui.label("This cannot be undone.").classes(
                                    "text-sm text-[#9fb2b8]"
                                )
                                with ui.row().classes(
                                    "mt-4 w-full justify-end gap-2"
                                ):
                                    ui.button("Cancel", on_click=dialog.close).props(
                                        "flat"
                                    )
                                    ui.button(
                                        "Delete",
                                        on_click=lambda selected_day=weekday, selected=block, prompt=dialog: delete_block(
                                            selected_day, selected, prompt
                                        ),
                                    ).props("unelevated color=negative")
                            ui.button(icon="delete", on_click=dialog.open).props(
                                "flat round dense"
                            ).tooltip("Delete time block")

    refresh_blocks()
