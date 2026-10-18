"""NiceGUI page for browsing, filtering, and exporting schedules.

Used by: GUI."""

# File name: schedule_viewer.py
# Primary author: Dylan Groff
# Secondary Author: Micah Schafer


from nicegui import ui
from src.controllers.schedule_controller import (
    schedule_controller as controller,
)
from src.controllers.schedule_filters_controller import (
    filter_by_resource,
    filter_by_faculty,
    filter_by_course,
)
from src.views.schedule_table_view import schedule_table_view

# set the background and accent colors for the schedule viewer
BACKGROUND = "#101820"
ACCENT = "#75e6da"


async def read_upload(event) -> tuple[str, bytes]:
    """Return (file name, bytes) from a ui.upload event (NiceGUI 2.x and 3.x)."""
    if hasattr(event, "file"):  # NiceGUI 3.x
        return event.file.name, await event.file.read()
    return event.name, event.content.read()  # NiceGUI 2.x


def schedule_viewer() -> None:
    # adds custom CSS to the web elements to style the schedule viewer
    ui.add_head_html(
        f"""
        <style>
            body {{
                background: {BACKGROUND} !important;
            }}

            .q-page {{
                background: {BACKGROUND} !important;
            }}

            /* Dropdowns */
            .schedule-dropdown .q-field__control:before {{
                border-color: #45616b !important;
            }}

            .schedule-dropdown .q-field__control:hover:before {{
                border-color: {ACCENT} !important;
            }}

            .schedule-dropdown .q-field--focused .q-field__control:after {{
                border-color: {ACCENT} !important;
            }}

            .schedule-dropdown .q-field__native,
            .schedule-dropdown .q-field__input,
            .schedule-dropdown .q-field__label,
            .schedule-dropdown .q-select__dropdown-icon {{
                color: #d8e7e8 !important;
            }}
        </style>
        """
    )

    ui.colors(primary=ACCENT, dark=BACKGROUND)

    # rows for the schedule currently selected in the dropdown
    schedule: list[dict] = []

    # set while the code itself changes the dropdown, so it doesn't re-trigger
    syncing = False

    with ui.column().classes("w-full min-h-screen px-6 py-8").style(
        f"background-color: {BACKGROUND};"
    ):

        # ---------------------------------------------------------
        # Title
        # ---------------------------------------------------------

        with ui.row().classes("w-full items-center gap-3 mb-6"):
            ui.icon("calendar_view_week", size="30px").style(
                f"color: {ACCENT};"
            )

            ui.label("Schedule Viewer").classes(
                "text-2xl font-semibold text-white"
            )

        # ---------------------------------------------------------
        # Load dialog
        # ---------------------------------------------------------

        with ui.dialog() as load_dialog:
            with ui.card().classes("bg-[#101820] border border-[#29404b] w-[480px] gap-3"):
                ui.label("Load Schedule").classes("text-lg font-semibold text-white")
                ui.label(
                    "Choose a saved schedule from the schedules folder."
                ).classes("text-sm text-gray-400")

                saved_file_select = ui.select(
                    [],
                    label="Saved schedules",
                    with_input=True,
                ).props("outlined dark").classes("schedule-dropdown w-full")

                load_status = ui.label("").classes("text-sm text-red-400")

                with ui.row().classes("w-full justify-end gap-2"):
                    ui.button("Cancel", on_click=load_dialog.close).props("flat")
                    load_button = ui.button("Load", icon="upload_file")

                ui.separator().classes("bg-[#29404b]")
                ui.label(
                    "Or upload a CSV or JSON schedule from your computer."
                ).classes("text-sm text-gray-400")

                upload = ui.upload(
                    auto_upload=True,
                    max_files=1,
                ).props("accept=.csv,.json dark flat bordered").classes("w-full")

        # ---------------------------------------------------------
        # Export dialog
        # ---------------------------------------------------------

        with ui.dialog() as export_dialog:
            with ui.card().classes("bg-[#101820] border border-[#29404b] w-[480px] gap-3"):
                ui.label("Export Schedule").classes("text-lg font-semibold text-white")
                export_description = ui.label("").classes("text-sm text-gray-400")

                export_format = ui.select(
                    {"csv": "CSV", "json": "JSON"},
                    value="csv",
                    label="File Format",
                ).props("outlined dark").classes("schedule-dropdown w-full")

                export_name = ui.input(
                    label="File Name",
                ).props("outlined dark").classes("schedule-dropdown w-full")

                export_status = ui.label("").classes("text-sm text-red-400")

                with ui.row().classes("w-full justify-end gap-2"):
                    ui.button("Cancel", on_click=export_dialog.close).props("flat")
                    export_button = ui.button("Export", icon="download")

        # ---------------------------------------------------------
        # Schedule controls
        # ---------------------------------------------------------

        with ui.row().classes("w-full items-center gap-3 mb-6"):

            # Load button
            ui.button(
                "Load",
                icon="upload_file",
                on_click=lambda: open_load_dialog(),
            ).props("outline")

            # Export button
            export_open_button = ui.button(
                "Export",
                icon="file_download",
                on_click=lambda: open_export_dialog(),
            ).props("outline")

            ui.space()

            # button to iterate left through the schedules
            previous_button = ui.button(
                icon="chevron_left",
                on_click=lambda: step_schedule(-1),
            ).props("flat")

            # dropdown to select the schedule to view
            schedule_select = ui.select(
                {},
                value=None,
                label="Schedule",
            ).props("outlined").classes("schedule-dropdown").style(
                "min-width: 320px;"
            )

            # button to iterate right through the schedules
            next_button = ui.button(
                icon="chevron_right",
                on_click=lambda: step_schedule(1),
            ).props("flat")

        empty_label = ui.label(
            "No schedules yet. Run the Schedule Generator, or load a saved schedule."
        ).classes("text-gray-400 mb-6")

        # ---------------------------------------------------------
        # Sort and filter controls
        # ---------------------------------------------------------

        with ui.row().classes("w-full items-center gap-4 mb-6 flex-nowrap"):

            filter_select = ui.select(
                ["None", "Course", "Faculty", "Room / Lab"],
                value="None",
                label="Filter By",
            ).props("outlined").classes("schedule-dropdown").style(
                "width: 180px;"
            )

            filter_value_select = ui.select(
                [],
                value=None,
                label="Filter Value",
            ).props("outlined").classes("schedule-dropdown").style(
                "width: 200px;"
            )

            day_filter_select = ui.select(
                {
                    None: "All Days",
                    "MON": "Monday",
                    "TUE": "Tuesday",
                    "WED": "Wednesday",
                    "THU": "Thursday",
                    "FRI": "Friday",
                },
                value=None,
                label="Day",
            ).props("outlined").classes("schedule-dropdown").style(
                "width: 180px;"
            )


        # ---------------------------------------------------------
        # Calendar and Table tabs
        # ---------------------------------------------------------
        with ui.tabs() as view_tabs:
            calendar_tab = ui.tab("Calendar")
            table_tab = ui.tab("Table")

        with ui.tab_panels(view_tabs, value=calendar_tab).classes("w-full"):
            with ui.tab_panel(calendar_tab):
                # place holder text
                ui.label("Calendar view will go here.")

            with ui.tab_panel(table_tab):
                table_view = schedule_table_view()
            

        # ---------------------------------------------------------
        # Update filter values
        # ---------------------------------------------------------

        # updates possible filter values for the user to choose from
        def update_filter_values():
            filter_type = filter_select.value

            if filter_type == "Course":
                values = sorted(
                    set(course["course"] for course in schedule)
                )

            elif filter_type == "Faculty":
                values = sorted(
                    set(course["faculty"] for course in schedule)
                )

            elif filter_type == "Room / Lab":
                values = sorted(
                    set(course["resource"] for course in schedule)
                )

            else:
                values = []

            # keep the current value when switching schedules, so the same
            # faculty member or room can be compared across schedules
            current_value = filter_value_select.value

            filter_value_select.options = values

            if current_value in values:
                filter_value_select.value = current_value
            elif values:
                filter_value_select.value = values[0]
            else:
                filter_value_select.value = None

            filter_value_select.update()

        # ---------------------------------------------------------
        # Update table
        # ---------------------------------------------------------

        def update_table():
            # Always start with the unfiltered schedule.
            updated_schedule = schedule.copy()

            # Apply the shared filter.
            filter_type = filter_select.value
            filter_value = filter_value_select.value

            if filter_type == "Course" and filter_value:
                updated_schedule = filter_by_course(
                    updated_schedule,
                    filter_value,
                )

            elif filter_type == "Faculty" and filter_value:
                updated_schedule = filter_by_faculty(
                    updated_schedule,
                    filter_value,
                )

            elif filter_type == "Room / Lab" and filter_value:
                updated_schedule = filter_by_resource(
                    updated_schedule,
                    filter_value,
                )

            selected_day = day_filter_select.value

            if selected_day:
                updated_schedule = [
                    row for row in updated_schedule
                    if row.get("day") == selected_day
                ]

            # Send the filtered rows to the table.
            # The table handles its own sorting and time formatting.
            table_view.update(updated_schedule)

        # ---------------------------------------------------------
        # Show the selected schedule
        # ---------------------------------------------------------

        def show_selected_schedule():
            """Redraw everything from the controller's current schedule."""
            nonlocal schedule, syncing

            schedule = controller.current_rows()
            has_schedules = controller.has_schedules

            syncing = True
            schedule_select.set_options(
                controller.schedule_options(),
                value=controller.selected_index if has_schedules else None,
            )
            syncing = False

            empty_label.visible = not has_schedules
            schedule_select.set_enabled(has_schedules)
            export_open_button.set_enabled(has_schedules)
            previous_button.set_enabled(controller.can_step(-1))
            next_button.set_enabled(controller.can_step(1))

            update_filter_values()
            update_table()

        def on_schedule_selected(event):
            if syncing or event.value is None:
                return
            controller.select(event.value)
            show_selected_schedule()

        def step_schedule(offset: int):
            controller.step(offset)
            show_selected_schedule()

        def check_for_generated_schedules():
            # The generator runs in the background; pick up its results
            # whenever a run finishes.
            if controller.sync_generated():
                show_selected_schedule()

        # ---------------------------------------------------------
        # Loading
        # ---------------------------------------------------------

        def open_load_dialog():
            saved_files = controller.list_saved_files()
            saved_file_select.set_options(saved_files, value=None)
            load_status.text = (
                "" if saved_files else "No saved schedules found in the schedules folder."
            )
            upload.reset()
            load_dialog.open()

        def finish_load(entry, error):
            if error:
                load_status.text = error
                return
            load_dialog.close()
            show_selected_schedule()
            ui.notify(
                f"Loaded {entry.file_name} ({len(entry.records)} sections)",
                type="positive",
            )

        def on_load_saved_file():
            finish_load(*controller.load_saved_file(saved_file_select.value))

        async def on_upload(event):
            file_name, content = await read_upload(event)
            upload.reset()
            finish_load(*controller.load_uploaded_file(file_name, content))

        load_button.on_click(on_load_saved_file)
        upload.on_upload(on_upload)

        # ---------------------------------------------------------
        # Exporting
        # ---------------------------------------------------------

        def open_export_dialog():
            entry = controller.current
            if entry is None:
                return
            export_description.text = (
                f"Export '{entry.label}' as a file downloaded by your browser."
            )
            export_name.value = controller.default_export_file_name(
                export_format.value
            )
            export_status.text = ""
            export_dialog.open()

        def on_export_format_changed(event):
            name = (export_name.value or "").strip()
            stem = name.rsplit(".", 1)[0] if name.lower().endswith((".csv", ".json")) else name
            export_name.value = (
                f"{stem}.{event.value}"
                if stem
                else controller.default_export_file_name(event.value)
            )

        def on_export():
            export, error = controller.export_current(
                export_format.value,
                export_name.value or "",
            )
            if error:
                export_status.text = error
                return
            content, file_name, media_type = export
            ui.download(content, filename=file_name, media_type=media_type)
            export_dialog.close()
            ui.notify(
                f"Exported {file_name}; your browser will download the file.",
                type="positive",
            )

        export_format.on_value_change(on_export_format_changed)
        export_button.on_click(on_export)

        # ---------------------------------------------------------
        # Dropdown events
        # ---------------------------------------------------------

        # updates when a different schedule is selected
        schedule_select.on_value_change(on_schedule_selected)

        # updates when a new filter type is selected
        filter_select.on_value_change(
            lambda _: (
                update_filter_values(),
                update_table(),
            )
        )

        # updates when a new filter value is selected
        filter_value_select.on_value_change(
            lambda _: update_table()
        )

        # updates when a new day filter is selected
        day_filter_select.on_value_change(
            lambda _: update_table()
        )

        # ---------------------------------------------------------
        # Initial state
        # ---------------------------------------------------------

        controller.sync_generated()
        show_selected_schedule()
        ui.timer(1.0, check_for_generated_schedules)
