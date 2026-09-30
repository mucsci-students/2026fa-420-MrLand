from nicegui import ui

from src.services.class_pattern_service import (
    add_class_pattern_from_values,
    delete_class_pattern_from_values,
    update_class_pattern_from_values,
)

DAYS = ("MON", "TUE", "WED", "THU", "FRI")
DELIVERY_MODES = ("in_person", "online")


def class_patterns_gui(patterns: list) -> None:
    ui.label("Class patterns").classes("text-xl font-semibold text-white")
    ui.label("Define meeting patterns for each course credit value.").classes(
        "text-sm text-[#9fb2b8]"
    )

    with ui.row().classes("w-full flex-wrap gap-4"):
        credits = ui.number("Credits", value=3, min=1, step=1).classes("w-36")
        start_time = ui.input("Default start time").props("type=time").classes("w-48")
        disabled = ui.checkbox("Disabled pattern").classes("text-[#d8e7e8]")

    ui.label("Meetings").classes("mt-2 font-semibold text-white")
    with ui.row().classes("w-full flex-wrap items-end gap-3"):
        meeting_day = ui.select(list(DAYS), value="MON", label="Day").classes("min-w-36")
        meeting_start = ui.input("Start time override").props("type=time").classes("w-48")
        meeting_duration = ui.number(
            "Duration (minutes)", value=75, min=1, step=1
        ).classes("w-48")
        meeting_lab = ui.checkbox("Lab meeting").classes("text-[#d8e7e8]")
        meeting_delivery = ui.select(
            list(DELIVERY_MODES), value="in_person", label="Delivery"
        ).classes("min-w-40")

    meeting_drafts = []
    draft_list = ui.column().classes("w-full gap-1")
    editing_pattern = {"pattern": None}

    def integer_value(field, label):
        value = field.value
        if value is None or not float(value).is_integer() or value <= 0:
            raise ValueError(f"{label} must be a positive integer.")
        return int(value)

    def refresh_drafts() -> None:
        draft_list.clear()
        with draft_list:
            if not meeting_drafts:
                ui.label("No meetings added to this pattern yet.").classes(
                    "text-sm text-[#9fb2b8]"
                )
                return
            for index, meeting in enumerate(meeting_drafts):
                with ui.row().classes(
                    "w-full items-center justify-between border-b border-[#29404b] py-2"
                ):
                    details = (
                        f"{meeting['day']}  |  {meeting['start_time'] or 'Pattern start'}  |  "
                        f"{meeting['duration']} min  |  "
                        f"{'Lab' if meeting['lab'] else 'Lecture'}  |  "
                        f"{meeting['delivery']}"
                    )
                    ui.label(details).classes("break-words text-sm text-[#d8e7e8]")
                    ui.button(
                        icon="delete",
                        on_click=lambda selected=index: remove_draft(selected),
                    ).props("flat round dense").tooltip("Remove meeting")

    def remove_draft(index: int) -> None:
        meeting_drafts.pop(index)
        refresh_drafts()

    def add_meeting_draft() -> None:
        try:
            draft = {
                "day": meeting_day.value,
                "start_time": meeting_start.value or None,
                "duration": integer_value(meeting_duration, "Meeting duration"),
                "lab": bool(meeting_lab.value),
                "delivery": meeting_delivery.value,
            }
            meeting_drafts.append(draft)
        except (TypeError, ValueError) as exc:
            ui.notify(str(exc), type="negative")
            return
        meeting_start.value = ""
        meeting_lab.value = False
        refresh_drafts()

    ui.button("Add meeting", icon="add", on_click=add_meeting_draft).props(
        "outline"
    ).classes("border-[#45616b] text-[#d8e7e8]")
    refresh_drafts()

    def pattern_values():
        return (
            integer_value(credits, "Credits"),
            list(meeting_drafts),
            bool(disabled.value),
            start_time.value or None,
        )

    def reset_form() -> None:
        editing_pattern["pattern"] = None
        credits.value = 3
        start_time.value = ""
        disabled.value = False
        meeting_drafts.clear()
        meeting_day.value = "MON"
        meeting_start.value = ""
        meeting_duration.value = 75
        meeting_lab.value = False
        meeting_delivery.value = "in_person"
        add_button.set_visibility(True)
        update_button.set_visibility(False)
        cancel_button.set_visibility(False)
        refresh_drafts()

    def add_pattern() -> None:
        try:
            add_class_pattern_from_values(patterns, *pattern_values())
        except (TypeError, ValueError) as exc:
            ui.notify(str(exc), type="negative")
            return
        reset_form()
        refresh_patterns()
        ui.notify("Class pattern added.", type="positive")

    def update_pattern() -> None:
        try:
            update_class_pattern_from_values(
                patterns, editing_pattern["pattern"], *pattern_values()
            )
        except (TypeError, ValueError) as exc:
            ui.notify(str(exc), type="negative")
            return
        reset_form()
        refresh_patterns()
        ui.notify("Class pattern updated.", type="positive")

    def begin_edit(pattern) -> None:
        editing_pattern["pattern"] = pattern
        credits.value = pattern.credits
        start_time.value = pattern.start_time or ""
        disabled.value = pattern.disabled
        meeting_drafts[:] = [
            {
                "day": meeting.day,
                "start_time": meeting.start_time,
                "duration": meeting.duration,
                "lab": meeting.lab,
                "delivery": meeting.delivery.value,
            }
            for meeting in pattern.meetings
        ]
        add_button.set_visibility(False)
        update_button.set_visibility(True)
        cancel_button.set_visibility(True)
        refresh_drafts()

    def delete_pattern(pattern, dialog) -> None:
        try:
            delete_class_pattern_from_values(patterns, pattern)
        except ValueError as exc:
            ui.notify(str(exc), type="negative")
            dialog.close()
            return
        if editing_pattern["pattern"] is pattern:
            reset_form()
        ui.notify("Class pattern deleted.", type="positive")
        dialog.close()
        refresh_patterns()

    def refresh_patterns() -> None:
        pattern_list.clear()
        with pattern_list:
            if not patterns:
                ui.label("No class patterns added yet.").classes(
                    "text-sm text-[#9fb2b8]"
                )
                return
            for pattern in patterns:
                status = "Disabled" if pattern.disabled else "Enabled"
                meeting_summary = "; ".join(
                    f"{meeting.day} {meeting.start_time or pattern.start_time or 'No fixed start'} "
                    f"({meeting.duration} min, "
                    f"{'lab' if meeting.lab else 'lecture'}, {meeting.delivery.value})"
                    for meeting in pattern.meetings
                )
                with ui.row().classes(
                    "w-full items-center justify-between gap-4 border-b border-[#29404b] py-3"
                ):
                    with ui.column().classes("min-w-0 gap-1"):
                        ui.label(f"{pattern.credits} credits  |  {status}").classes(
                            "font-semibold text-white"
                        )
                        ui.label(
                            f"Default start: {pattern.start_time or 'None'}  |  {meeting_summary}"
                        ).classes("break-words text-sm text-[#9fb2b8]")
                    with ui.row().classes("shrink-0 items-center gap-1"):
                        ui.button(
                            icon="edit",
                            on_click=lambda selected=pattern: begin_edit(selected),
                        ).props("flat round dense").tooltip("Edit class pattern")
                        with ui.dialog() as dialog, ui.card().classes(
                            "border border-[#29404b] bg-[#182630]"
                        ):
                            ui.label(f"Delete {pattern.credits}-credit pattern?").classes(
                                "text-lg font-semibold text-white"
                            )
                            ui.label("This cannot be undone.").classes(
                                "text-sm text-[#9fb2b8]"
                            )
                            with ui.row().classes("mt-4 w-full justify-end gap-2"):
                                ui.button("Cancel", on_click=dialog.close).props("flat")
                                ui.button(
                                    "Delete",
                                    on_click=lambda selected=pattern, prompt=dialog: delete_pattern(
                                        selected, prompt
                                    ),
                                ).props("unelevated color=negative")
                        ui.button(icon="delete", on_click=dialog.open).props(
                            "flat round dense"
                        ).tooltip("Delete class pattern")

    with ui.row().classes("w-full flex-wrap items-center gap-2"):
        add_button = ui.button(
            "Add class pattern", icon="add", on_click=add_pattern
        ).props("unelevated").classes("bg-[#75e6da] text-[#101820]")
        update_button = ui.button(
            "Save changes", icon="save", on_click=update_pattern
        ).props("unelevated").classes("bg-[#75e6da] text-[#101820]")
        update_button.set_visibility(False)
        cancel_button = ui.button("Cancel edit", on_click=reset_form).props(
            "outline"
        ).classes("border-[#45616b] text-[#d8e7e8]")
        cancel_button.set_visibility(False)

    ui.label("Existing class patterns").classes(
        "mt-4 text-lg font-semibold text-white"
    )
    pattern_list = ui.column().classes("w-full gap-1")
    refresh_patterns()
