"""NiceGUI page for browsing, filtering, and exporting schedules.

Used by: GUI."""

# File name: schedule_viewer.py
# Primary author: Dylan Groff
# Secondary Author: Micah Schafer
# Tertiary Author: Renee Watts

from collections.abc import Callable

from nicegui import ui

from src.controllers.schedule_controller import (
    schedule_controller as controller,
)

# Renee: export only the selected faculty member's or room/lab's classes
# (Export by faculty, Export by room or lab)
from src.controllers.schedule_filtered_export_controller import (
    default_filtered_file_name,
    export_extension,
    export_faculty_schedule,
    export_room_schedule,
)
from src.controllers.schedule_filters_controller import (
    filter_by_course,
    filter_by_faculty,
    filter_by_resource,
)
from src.controllers.schedule_print_export_controller import (
    ALL_GROUPS,
    export_print_schedule,
    print_group_options,
)
from src.models.schedule_viewer_model import ScheduleEntry
from src.views.schedule_calendar_view import schedule_calendar_view
from src.views.schedule_table_view import schedule_table_view

# set the background and accent colors for the schedule viewer
BACKGROUND = "#101820"
ACCENT = "#75e6da"


async def read_upload(event) -> tuple[str, bytes]:
    """Return (file name, bytes) from a ui.upload event (NiceGUI 2.x and 3.x)."""
    if hasattr(event, "file"):  # NiceGUI 3.x
        return event.file.name, await event.file.read()
    return event.name, event.content.read()  # NiceGUI 2.x


def schedule_viewer() -> Callable[[], None]:
    print_entry: ScheduleEntry | None = None

    # adds custom CSS to the web elements to style the schedule viewer
    ui.add_head_html(
        f"""
        <style>
            body {{
                background: var(--app-background) !important;
            }}

            .q-page {{
                background: var(--app-background) !important;
            }}

            /* Dropdowns */
            .schedule-dropdown .q-field__control:before {{
                border-color: var(--border-strong) !important;
            }}

            .schedule-dropdown .q-field__control:hover:before {{
                border-color: {ACCENT} !important;
            }}

            .schedule-dropdown .q-field--focused .q-field__control:after {{
                border-color: {ACCENT} !important;
                border-color: var(--accent-color) !important;
            }}

            .schedule-dropdown .q-field--focused .q-field__control:after {{
                border-color: var(--accent-color) !important;
            }}

            .schedule-dropdown .q-field__native,
            .schedule-dropdown .q-field__input,
            .schedule-dropdown .q-field__label,
            .schedule-dropdown .q-select__dropdown-icon {{
                color: var(--app-foreground) !important;
            }}

            /* Table */
            .q-table__container,
            .q-table__middle,
            .q-table {{
                background: var(--app-background) !important;
            }}

            .q-table thead tr {{
                background: var(--surface-raised) !important;
            }}

            .q-table tbody tr {{
                background: var(--app-background) !important;
            }}

            .q-table tbody tr:hover {{
                background: var(--surface-hover) !important;
            }}

            .q-table th,
            .q-table td {{
                color: var(--app-foreground) !important;
            }}

            /* Table pagination */
            .q-table__bottom {{
                background: var(--app-background) !important;
                color: var(--app-foreground) !important;
                border-top: 1px solid var(--border-color) !important;
            }}

            .q-table__bottom .q-field__native,
            .q-table__bottom .q-field__input,
            .q-table__bottom .q-field__label,
            .q-table__bottom .q-select__dropdown-icon {{
                color: var(--app-foreground) !important;
            }}

            .q-table__bottom .q-btn {{
                color: var(--app-foreground) !important;
            }}
        </style>
        """
    )

    ui.colors(primary=ACCENT, dark=BACKGROUND)

    # rows for the schedule currently selected in the dropdown
    schedule: list[dict] = []

    # set while the code itself changes the dropdown, so it doesn't re-trigger
    syncing = False
    load_generation = 0

    with (
        ui.column()
        .classes("w-full min-h-screen px-6 py-8")
        .style("background-color: var(--app-background);")
    ):
        # ---------------------------------------------------------
        # Title
        # ---------------------------------------------------------

        with ui.row().classes("w-full items-center gap-3 mb-6"):
            ui.icon("calendar_view_week", size="30px").style("color: var(--accent-color);")

            ui.label("Schedule Viewer").classes("text-2xl font-semibold text-white")

        # ---------------------------------------------------------
        # Load dialog
        # ---------------------------------------------------------

        with (
            ui.dialog() as load_dialog,
            ui.card().classes("bg-[#101820] border border-[#29404b] w-[480px] gap-3"),
        ):
            ui.label("Load Schedule").classes("text-lg font-semibold text-white")

            load_status = ui.label("").classes("text-sm text-red-400")

            ui.label("Upload a CSV or JSON schedule from your computer.").classes(
                "text-sm text-gray-400"
            )

            upload = (
                ui.upload(
                    label="Choose configuration file",
                    auto_upload=True,
                    max_files=1,
                )
                .props("accept=.csv,.json dark flat bordered")
                .classes("w-full schedule-load-upload")
            )

            with ui.row().classes("w-full justify-end"):
                ui.button(
                    "Cancel",
                    on_click=lambda: cancel_load(),
                ).props("flat")

        # ---------------------------------------------------------
        # Export dialog
        # ---------------------------------------------------------

        with (
            ui.dialog() as export_dialog,
            ui.card().classes("bg-[#101820] border border-[#29404b] w-[480px] gap-3"),
        ):
            ui.label("Export Schedule").classes("text-lg font-semibold text-white")
            export_description = ui.label("").classes("text-sm text-gray-400")

            export_format = (
                ui.select(
                    {"csv": "CSV", "json": "JSON"},
                    value="csv",
                    label="File Format",
                )
                .props("outlined dark")
                .classes("schedule-dropdown w-full")
            )

            export_name = (
                ui.input(
                    label="File Name",
                )
                .props("outlined dark")
                .classes("schedule-dropdown w-full")
            )

            export_status = ui.label("").classes("text-sm text-red-400")

            with ui.row().classes("w-full justify-end gap-2"):
                ui.button("Cancel", on_click=export_dialog.close).props("flat")
                export_button = ui.button("Export", icon="download")

        with (
            ui.dialog() as export_all_dialog,
            ui.card().classes("bg-[#101820] border border-[#29404b] w-[480px] gap-3"),
        ):
            ui.label("Export All Generated Schedules").classes("text-lg font-semibold text-white")
            ui.label("Download every generated schedule together in one ZIP archive.").classes(
                "text-sm text-gray-400"
            )
            export_all_format = (
                ui.select(
                    {"csv": "CSV", "json": "JSON"},
                    value="csv",
                    label="Schedule File Format",
                )
                .props("outlined dark")
                .classes("schedule-dropdown w-full")
            )
            export_all_status = ui.label("").classes("text-sm text-red-400")
            with ui.row().classes("w-full justify-end gap-2"):
                ui.button("Cancel", on_click=export_all_dialog.close).props("flat")
                export_all_button = ui.button("Export All", icon="folder_zip")

        with (
            ui.dialog() as print_export_dialog,
            ui.card().classes("bg-[#101820] border border-[#29404b] w-[520px] gap-3"),
        ):
            ui.label("Print / Export PDF").classes("text-lg font-semibold text-white")
            print_schedule_description = ui.label("").classes("text-sm text-gray-400")
            print_orientation = (
                ui.select(
                    {"resource": "Room / lab", "faculty": "Faculty"},
                    value="resource",
                    label="Group by",
                )
                .props("outlined dark")
                .classes("schedule-dropdown w-full")
            )
            print_group = (
                ui.select(
                    {ALL_GROUPS: "All rooms, labs, and online/unassigned meetings"},
                    value=ALL_GROUPS,
                    label="Resource or faculty",
                )
                .props("outlined dark")
                .classes("schedule-dropdown w-full")
            )
            ui.label(
                "Downloads a Letter-size print layout. Open it in your browser, "
                "choose Print, then Save as PDF to select the destination."
            ).classes("text-sm text-gray-400")
            print_export_status = ui.label("").classes("text-sm text-red-400")
            with ui.row().classes("w-full justify-end gap-2"):
                ui.button("Cancel", on_click=print_export_dialog.close).props("flat")
                print_export_button = ui.button("Prepare print layout", icon="picture_as_pdf")

        # ---------------------------------------------------------
        # Schedule controls
        # ---------------------------------------------------------

        with ui.row().classes("w-full items-center gap-3 mb-4 flex-wrap"):
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

            print_export_open_button = ui.button(
                "Print / Export PDF",
                icon="picture_as_pdf",
                on_click=lambda: open_print_export_dialog(),
            ).props("outline")

            export_all_open_button = ui.button(
                "Export All Generated",
                icon="folder_zip",
                on_click=lambda: open_export_all_dialog(),
            ).props("outline")

            clear_generated_button = ui.button(
                "Clear Generated Results",
                icon="delete_sweep",
                on_click=lambda: clear_generated_results(),
            ).props("outline")

            # helper to reset filter values to default
            def reset_filters():
                filter_select.set_value("None")
                filter_value_select.set_value(None)
                day_filter_select.set_value(None)

                update_filter_values()
                update_table()

            # Button to reset all filters to their default values
            reset_filters_button = ui.button(
                "Reset Filters",
                icon="filter_alt_off",
                on_click=reset_filters,
            ).props("outline")

        with (
            ui.row()
            .classes(
                "schedule-navigation w-full items-center justify-center gap-2 mb-6 flex-nowrap"
            )
            .style("width: calc(100% + 3rem); margin-left: -1.5rem; margin-right: -1.5rem;")
        ):
            previous_button = ui.button(
                icon="chevron_left",
                on_click=lambda: step_schedule(-1),
            ).props("flat")

            schedule_select = (
                ui.select(
                    {},
                    value=None,
                    label="Schedule",
                )
                .props("outlined dark")
                .classes("schedule-dropdown min-w-0 flex-1 max-w-md")
                .style("min-width: 0;")
            )

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
            # drop down to select the type of filter to apply to the schedule table
            filter_select = (
                ui.select(
                    ["None", "Course", "Faculty", "Room / Lab"],
                    value="None",
                    label="Filter By",
                )
                .props("outlined")
                .classes("schedule-dropdown")
                .style("width: 180px;")
            )

            # drop down to select the value of the filter to apply to the schedule table
            filter_value_select = (
                ui.select(
                    [],
                    value=None,
                    label="Filter Value",
                )
                .props("outlined")
                .classes("schedule-dropdown")
                .style("width: 200px;")
            )

            # drop down to select the day of the week to filter the schedule table
            day_filter_select = (
                ui.select(
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
                )
                .props("outlined")
                .classes("schedule-dropdown")
                .style("width: 180px;")
            )

        # ---------------------------------------------------------
        # Calendar and Table tabs
        # ---------------------------------------------------------
        with ui.tabs() as view_tabs:
            calendar_tab = ui.tab("Calendar")
            table_tab = ui.tab("Table")

        with ui.tab_panels(view_tabs, value=calendar_tab).classes("w-full"):
            with ui.tab_panel(calendar_tab):
                calendar_view = schedule_calendar_view()

            with ui.tab_panel(table_tab):
                table_view = schedule_table_view()

        # ---------------------------------------------------------
        # Update filter values
        # ---------------------------------------------------------

        # updates possible filter values for the user to choose from
        def update_filter_values():
            filter_type = filter_select.value

            if filter_type == "Course":
                values = sorted({course["course"] for course in schedule})

            elif filter_type == "Faculty":
                values = sorted({course["faculty"] for course in schedule})

            elif filter_type == "Room / Lab":
                values = sorted({course["resource"] for course in schedule})

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
                    row for row in updated_schedule if row.get("day") == selected_day
                ]

            # Send the filtered rows to the table.
            # The table handles its own sorting and time formatting.
            table_view.update(updated_schedule)
            calendar_view.update(updated_schedule, selected_day)

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
            print_export_open_button.set_enabled(has_schedules)
            export_all_open_button.set_enabled(controller.has_generated_schedules)
            clear_generated_button.set_enabled(controller.has_generated_schedules)
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

        def clear_generated_results():
            if not controller.clear_generated_schedules():
                ui.notify(
                    "Cannot clear generated results while generation is in progress.",
                    type="negative",
                )
                return
            controller.sync_generated()
            show_selected_schedule()
            ui.notify("Generated results cleared.", type="positive")

        def check_for_generated_schedules():
            # The generator runs in the background; pick up its results
            # whenever a run finishes.
            if controller.sync_generated():
                show_selected_schedule()

        def refresh_viewer() -> None:
            controller.sync_generated()
            show_selected_schedule()

        # ---------------------------------------------------------
        # Loading
        # ---------------------------------------------------------

        def open_load_dialog():
            nonlocal load_generation
            load_generation += 1
            upload.reset()
            load_dialog.open()

        def cancel_load():
            nonlocal load_generation
            load_generation += 1
            upload.reset()
            load_dialog.close()

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

        async def on_upload(event):
            generation = load_generation
            if not load_dialog.value:
                return
            file_name, content = await read_upload(event)
            if generation != load_generation or not load_dialog.value:
                return
            upload.reset()
            finish_load(*controller.load_uploaded_file(file_name, content))

        upload.on_upload(on_upload)

        # ---------------------------------------------------------
        # Exporting
        # ---------------------------------------------------------

        def selected_export_filter() -> tuple[str, str] | None:
            """Return what the user is filtering by, for the Export button.

            Returns ("Faculty", "<name>") or ("Room / Lab", "<room>"), or None
            when not filtering by faculty or room/lab, which means Export
            should use the normal full-schedule export.
            (Filtering by Course doesn't change the export.)
            """
            filter_type = filter_select.value
            filter_value = filter_value_select.value
            if filter_type in ("Faculty", "Room / Lab") and filter_value:
                return filter_type, filter_value
            return None

        def open_export_dialog():
            entry = controller.current
            if entry is None:
                return
            export_status.text = ""
            export_filter = selected_export_filter()

            # Reset the format choices each time the dialog opens.
            # PDF is only offered when filtering by faculty or room/lab; it uses
            # Sohil's print layout for just that one person or room. (The full
            # schedule has its own "Print / Export PDF" button.)
            if export_filter:
                export_format.set_options(
                    {"csv": "CSV", "json": "JSON", "pdf": "PDF (print layout)"}, value="csv"
                )
            else:
                export_format.set_options({"csv": "CSV", "json": "JSON"}, value="csv")

            if export_filter:
                # Filtering: explain that only those classes are exported and
                # suggest a file name that includes the faculty member or room.
                filter_type, filter_value = export_filter
                if filter_type == "Faculty":
                    export_description.text = (
                        f"Export only {filter_value}'s classes from '{entry.label}'."
                    )
                else:
                    export_description.text = (
                        f"Export only the classes that meet in {filter_value} from '{entry.label}'."
                    )
                export_name.value = default_filtered_file_name(entry, filter_value, "csv")
            else:
                # No faculty filter: normal export of the whole schedule.
                export_description.text = (
                    f"Download '{entry.label}' to your browser's default location. "
                    f"Check your browser settings to manually choose the save location."
                )
                try:
                    export_name.value = controller.default_export_file_name("csv")
                except OSError as error:
                    export_status.text = str(error)
            export_dialog.open()

        def open_export_all_dialog():
            if not controller.has_generated_schedules:
                return
            export_all_status.text = ""
            export_all_dialog.open()

        def update_print_group_options():
            try:
                options = print_group_options(print_entry, print_orientation.value)
            except ValueError as error:
                print_export_status.text = str(error)
                return
            current_value = print_group.value
            print_group.set_options(
                options,
                value=current_value if current_value in options else ALL_GROUPS,
            )

        def open_print_export_dialog():
            nonlocal print_entry
            entry = controller.current
            if entry is None:
                return
            print_entry = entry
            print_export_status.text = ""
            print_schedule_description.text = f"Selected schedule: {print_entry.label}"
            print_orientation.value = "resource"
            update_print_group_options()
            print_export_dialog.open()

        def on_print_export():
            export, error = export_print_schedule(
                print_entry,
                print_orientation.value,
                print_group.value,
            )
            if error or export is None:
                print_export_status.text = error or "Could not prepare the print layout."
                return
            content, file_name, media_type = export
            ui.download(content, filename=file_name, media_type=media_type)
            print_export_dialog.close()
            ui.notify(
                f"Downloaded {file_name}. Open it in a browser and choose Print > Save as PDF.",
                type="positive",
            )

        # Give the calendar fullscreen toolbar access to the existing export dialog.
        calendar_view.set_export_callback(open_export_dialog)

        def on_export_format_changed(event):
            name = (export_name.value or "").strip()
            known_extensions = (".csv", ".json", ".html")
            stem = name.rsplit(".", 1)[0] if name.lower().endswith(known_extensions) else name
            if stem:
                # "pdf" downloads as a .html print layout, so use the right extension
                export_name.value = f"{stem}.{export_extension(event.value)}"
                return
            # Name box is empty: suggest a default name.
            # Use the faculty/room-specific name when filtering.
            export_filter = selected_export_filter()
            if export_filter and controller.current:
                export_name.value = default_filtered_file_name(
                    controller.current, export_filter[1], event.value
                )
                return
            try:
                export_name.value = controller.default_export_file_name(event.value)
                export_status.text = ""
            except OSError as error:
                export_status.text = str(error)

        def on_export():
            # If the user is filtering by faculty or room/lab, export just those
            # classes. Otherwise export the whole schedule like before.
            # All of these functions return (export, error) in the same shape.
            export_filter = selected_export_filter()
            if export_filter and export_filter[0] == "Faculty":
                export, error = export_faculty_schedule(
                    controller.current,
                    export_filter[1],
                    export_format.value,
                    export_name.value or "",
                )
            elif export_filter:
                export, error = export_room_schedule(
                    controller.current,
                    export_filter[1],
                    export_format.value,
                    export_name.value or "",
                )
            else:
                export, error = controller.export_current(
                    export_format.value,
                    export_name.value or "",
                )
            if error:
                export_status.text = error
                return
            if export is None:
                export_status.text = "No schedule export is available."
                return
            content, file_name, media_type = export
            ui.download(content, filename=file_name, media_type=media_type)
            export_dialog.close()
            if export_format.value == "pdf":
                # Same instructions Sohil's print export shows
                ui.notify(
                    f"Downloaded {file_name}. Open it in a browser and choose Print > Save as PDF.",
                    type="positive",
                )
            else:
                ui.notify(f"Exporting {file_name}.", type="positive")

        def on_export_all():
            export, error = controller.export_all_generated(export_all_format.value)
            if error or export is None:
                export_all_status.text = error or "Could not export generated schedules."
                return
            content, file_name, media_type = export
            ui.download(content, filename=file_name, media_type=media_type)
            export_all_dialog.close()
            ui.notify(
                f"Exporting all generated schedules as {file_name}.",
                type="positive",
            )

        export_format.on_value_change(on_export_format_changed)
        export_button.on_click(on_export)
        export_all_button.on_click(on_export_all)
        print_orientation.on_value_change(lambda _: update_print_group_options())
        print_export_button.on_click(on_print_export)

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
        filter_value_select.on_value_change(lambda _: update_table())

        # updates when a new day filter is selected
        day_filter_select.on_value_change(lambda _: update_table())

        # resets all filters to their default values when the reset button is clicked
        reset_filters_button.on_click(lambda _: reset_filters())

        # ---------------------------------------------------------
        # Initial state
        # ---------------------------------------------------------

        controller.sync_generated()
        show_selected_schedule()
        ui.timer(1.0, check_for_generated_schedules)

    return refresh_viewer
