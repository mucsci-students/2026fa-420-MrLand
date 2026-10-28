"""NiceGUI page for managing class patterns and meetings."""

from nicegui import ui

from src.controllers.class_pattern_controller import ClassPatternController
from src.views.common import (
    ConfigurationChangeHandler,
    PendingChangeHandler,
    PendingFormChanges,
    parse_whole_number,
    run_crud_mutation,
)

controller = ClassPatternController()

DAYS = ("MON", "TUE", "WED", "THU", "FRI")
DELIVERY_MODES = ("in_person", "online")


def class_patterns_gui(
    patterns: list,
    on_change: ConfigurationChangeHandler | None = None,
    on_pending_change: PendingChangeHandler | None = None,
) -> None:
    """Build the class-pattern editor, including nested meeting management."""

    ui.label("Class patterns").classes("text-xl font-semibold text-white")
    ui.label("Define meeting patterns for each course credit value.").classes(
        "text-sm text-[#9fb2b8]"
    )
    ui.label("Existing class patterns").classes(
        "mt-4 text-lg font-semibold text-white"
    )
    pattern_list = ui.column().classes("w-full gap-1")

    with ui.row().classes("w-full flex-wrap items-center gap-2"):
        add_button = ui.button("Add new class pattern", icon="add", on_click=lambda: show_form()).props(
            "unelevated"
        ).classes("bg-[#75e6da] text-[#101820]")

    # Pattern fields and a draft editor for the pattern's individual meetings.
    with ui.column().classes("w-full gap-4 mt-6 rounded-lg border border-[#45616b] bg-[#17232b] p-4") as form_container:
        form_container.set_visibility(False)
        form_heading = ui.label("Add New Class Pattern").classes("text-lg font-semibold text-white")

        with ui.row().classes("w-full flex-wrap gap-4"):
            credits = ui.number("Credits", value=3, min=1, step=1).classes("w-36")
            start_time = ui.input("Default start time").props("type=time").classes("w-48")
            disabled = ui.checkbox("Disabled pattern").classes("text-[#d8e7e8]")

        with ui.row().classes("mt-2 w-full items-center gap-2"):
            ui.label("Meetings").classes("font-semibold text-white")
            meetings_header_status = ui.label("").classes("text-sm font-medium text-[#75e6da]")
            meetings_header_status.set_visibility(False)
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
        editing_pattern = {"pattern": None}
        editing_meeting = {"index": None}
        pending_changes = PendingFormChanges(form_container, on_pending_change)
        pending_changes.watch(
            credits,
            start_time,
            disabled,
            meeting_day,
            meeting_start,
            meeting_duration,
            meeting_lab,
            meeting_delivery,
        )
        with ui.column().classes("w-full gap-2"):
            meeting_section_header = ui.row().classes("w-full items-center gap-2")
            with meeting_section_header:
                ui.label("Meeting details").classes("text-sm font-semibold text-white")
            draft_list = ui.column().classes("w-full gap-1")

        def integer_value(field, label):
            '''Ensure numeric fields contain positive whole numbers.'''

            message = f"{label} must be a positive integer."
            value = parse_whole_number(field.value, message)
            if value <= 0:
                raise ValueError(message)
            return value

        # Show whether the meeting controls are adding or editing a draft.
        def update_meeting_status() -> None:
            if editing_meeting["index"] is None:
                meetings_header_status.set_text("Adding a new meeting to this pattern.")
                meetings_header_status.set_visibility(False)
                return
            
            meeting_number = editing_meeting["index"] + 1
            meetings_header_status.set_text(f"Editing meeting #{meeting_number} in this pattern.")
            meetings_header_status.set_visibility(True)

        # Clear the meeting controls and leave meeting-edit mode.
        def reset_meeting_form() -> None:
            editing_meeting["index"] = None
            with pending_changes.suspend():
                meeting_day.value = "MON"
                meeting_start.value = ""
                meeting_duration.value = 75
                meeting_lab.value = False
                meeting_delivery.value = "in_person"
            add_meeting_button.set_text("Add meeting")
            cancel_meeting_edit_button.set_visibility(False)
            update_meeting_status()

        # Render the current meeting drafts with edit and remove actions.
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
                        with ui.row().classes("items-center gap-1"):
                            ui.button(
                                icon="edit",
                                on_click=lambda selected=index: begin_edit_meeting(selected),
                            ).props("flat round dense").tooltip("Edit meeting")
                            ui.button(
                                icon="delete",
                                on_click=lambda selected=index: remove_draft(selected),
                            ).props("flat round dense").tooltip("Remove meeting")

        def remove_draft(index: int) -> None:
            '''Remove a meeting draft and reset its form if it was being edited.'''

            if editing_meeting["index"] == index:
                reset_meeting_form()

            meeting_drafts.pop(index)
            pending_changes.mark_pending()
            refresh_drafts()

        def begin_edit_meeting(index: int) -> None:

            '''Load a meeting draft into the meeting controls.'''

            if index < 0 or index >= len(meeting_drafts):
                return
            
            meeting = meeting_drafts[index]
            editing_meeting["index"] = index
            with pending_changes.suspend():
                meeting_day.value = meeting["day"]
                meeting_start.value = meeting["start_time"] or ""
                meeting_duration.value = meeting["duration"]
                meeting_lab.value = bool(meeting["lab"])
                meeting_delivery.value = meeting["delivery"]
            add_meeting_button.set_text("Apply meeting changes")
            cancel_meeting_edit_button.set_visibility(True)
            update_meeting_status()

        def add_meeting_draft() -> None:

            '''Validate the meeting controls and add or replace a draft meeting.'''

            try:
                draft = {
                    "day": meeting_day.value,
                    "start_time": meeting_start.value or None,
                    "duration": integer_value(meeting_duration, "Meeting duration"),
                    "lab": bool(meeting_lab.value),
                    "delivery": meeting_delivery.value,
                }
                if editing_meeting["index"] is not None:
                    meeting_drafts[editing_meeting["index"]] = draft

                else:
                    meeting_drafts.append(draft)

            except (TypeError, ValueError) as exc:
                ui.notify(str(exc), type="negative")
                return

            pending_changes.mark_pending()
            
            reset_meeting_form()
            refresh_drafts()

        with ui.row().classes("w-full items-center gap-2"):
            add_meeting_button = ui.button("Add meeting", icon="add", on_click=add_meeting_draft).props(
                "outline"
            ).classes("border-[#45616b] text-[#d8e7e8]")
            cancel_meeting_edit_button = ui.button(
                "Cancel edit",
                on_click=lambda: (reset_meeting_form(), refresh_drafts()),
            ).props("flat").classes("text-[#d8e7e8]")
            cancel_meeting_edit_button.set_visibility(False)
        refresh_drafts()

        def pattern_values():
            '''Collect the current pattern fields and its meeting drafts.'''
            return (
                integer_value(credits, "Credits"),
                list(meeting_drafts),
                bool(disabled.value),
                start_time.value or None,
            )

        def show_form() -> None:

            '''Reset the pattern and meeting controls for a new pattern.'''

            form_container.set_visibility(False)
            pending_changes.clear()
            editing_pattern["pattern"] = None
            form_heading.set_text("Add New Class Pattern")
            with pending_changes.suspend():
                credits.value = 3
                start_time.value = ""
                disabled.value = False
                meeting_drafts.clear()
                reset_meeting_form()
            refresh_drafts()
            form_container.set_visibility(True)
            add_submit_button.set_visibility(True)
            update_button.set_visibility(False)
            cancel_button.set_visibility(True)

        def reset_form() -> None:

            '''Clear the pattern and meeting drafts, then close the form.'''

            form_container.set_visibility(False)
            editing_pattern["pattern"] = None
            form_heading.set_text("Add New Class Pattern")
            with pending_changes.suspend():
                credits.value = 3
                start_time.value = ""
                disabled.value = False
                meeting_drafts.clear()
                reset_meeting_form()
            pending_changes.clear()
            add_submit_button.set_visibility(True)
            update_button.set_visibility(False)
            cancel_button.set_visibility(False)
            refresh_drafts()

        def add_pattern() -> None:

            '''Add the validated pattern and its meetings to the configuration.'''

            if not run_crud_mutation(
                on_change,
                lambda: controller.add_pattern(patterns, *pattern_values()),
            ):
                return
            
            reset_form()
            refresh_patterns()
            ui.notify("Class pattern added.", type="positive")

        def update_pattern() -> None:

            '''Save changes to the pattern currently being modified.'''

            if not run_crud_mutation(
                on_change,
                lambda: controller.update_pattern(
                    patterns, editing_pattern["pattern"], *pattern_values()
                ),
            ):
                return
            
            reset_form()
            refresh_patterns()
            ui.notify("Class pattern updated.", type="positive")

        def begin_edit(pattern) -> None:
            '''Load a pattern and its meetings into the editor.'''

            form_container.set_visibility(False)
            pending_changes.clear()
            editing_pattern["pattern"] = pattern
            form_heading.set_text("Modifying Class Pattern")
            with pending_changes.suspend():
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
            form_container.set_visibility(True)
            add_submit_button.set_visibility(False)
            update_button.set_visibility(True)
            cancel_button.set_visibility(True)
            refresh_drafts()

        def delete_pattern(pattern, dialog) -> None:

            '''Delete the selected pattern after confirmation.'''

            if not run_crud_mutation(
                on_change,
                lambda: controller.delete_pattern(patterns, pattern),
                handled_errors=(ValueError,),
            ):
                dialog.close()
                return
            
            if editing_pattern["pattern"] is pattern:
                reset_form()

            ui.notify("Class pattern deleted.", type="positive")
            dialog.close()
            refresh_patterns()

        with ui.row().classes("w-full flex-wrap items-center gap-2"):
            add_submit_button = ui.button("Create class pattern", icon="add", on_click=add_pattern).props(
                "unelevated"
            ).classes("bg-[#75e6da] text-[#101820]")
            update_button = ui.button(
                "Apply changes", icon="save", on_click=update_pattern
            ).props("unelevated").classes("bg-[#75e6da] text-[#101820]")
            update_button.set_visibility(False)
            cancel_button = ui.button("Cancel", on_click=reset_form).props(
                "outline"
            ).classes("border-[#45616b] text-[#d8e7e8]")
            cancel_button.set_visibility(False)

    def refresh_patterns() -> None:

        '''Rebuild pattern summaries and their edit/delete controls.'''

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

    refresh_patterns()
