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

# Renee: start the Print / Export PDF dialog on the viewer's faculty or
# room/lab filter (Export by faculty, Export by room or lab)
from src.controllers.schedule_filtered_export_controller import print_defaults_for_filter
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
            ui.label("Downloads a Letter-size PDF.").classes("text-sm text-gray-400")
            print_export_status = ui.label("").classes("text-sm text-red-400")
            with ui.row().classes("w-full justify-end gap-2"):
                ui.button("Cancel", on_click=print_export_dialog.close).props("flat")
                print_export_button = ui.button("Download PDF", icon="picture_as_pdf")

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
                calendar_view_select.set_value("Faculty")
                calendar_filter_select.set_value("None")
                calendar_day_filter_select.set_value(None)
                table_filter_select.set_value("None")
                table_day_filter_select.set_value(None)
                update_calendar_filter_values()
                update_calendar_filter_value_values()
                update_table_filter_values()
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
        # Calendar and Table tabs
        # ---------------------------------------------------------
        with ui.tabs() as view_tabs:
            calendar_tab = ui.tab("Calendar")
            table_tab = ui.tab("Table")

        with ui.tab_panels(view_tabs, value=calendar_tab).classes("w-full"):
            with ui.tab_panel(calendar_tab):
                with ui.row().classes("w-full items-center gap-4 mb-4 flex-wrap"):
                    calendar_view_select = (
                        ui.select(
                            ["Faculty", "Room / Lab", "Entire Schedule"],
                            value="Faculty",
                            label="View By",
                        )
                        .props("outlined")
                        .classes("schedule-dropdown")
                        .style("width: 200px;")
                    )
                    calendar_value_select = (
                        ui.select(
                            [],
                            value=None,
                            label="Faculty Member",
                        )
                        .props("outlined")
                        .classes("schedule-dropdown")
                        .style("width: 220px;")
                    )
                    calendar_filter_select = (
                        ui.select(
                            ["None", "Course", "Faculty", "Room / Lab"],
                            value="None",
                            label="Filter",
                        )
                        .props("outlined")
                        .classes("schedule-dropdown")
                        .style("width: 180px;")
                    )
                    calendar_filter_value_select = (
                        ui.select(
                            [],
                            value=None,
                            label="Filter Value",
                        )
                        .props("outlined")
                        .classes("schedule-dropdown")
                        .style("width: 220px;")
                    )
                    calendar_day_filter_select = (
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
                        .style("width: 160px;")
                    )
                calendar_view = schedule_calendar_view()

            with ui.tab_panel(table_tab):
                with ui.row().classes("w-full items-center gap-4 mb-4 flex-wrap"):
                    table_filter_select = (
                        ui.select(
                            ["None", "Course", "Faculty", "Room / Lab"],
                            value="None",
                            label="Filter",
                        )
                        .props("outlined")
                        .classes("schedule-dropdown")
                        .style("width: 180px;")
                    )
                    table_filter_value_select = (
                        ui.select(
                            [],
                            value=None,
                            label="Filter Value",
                        )
                        .props("outlined")
                        .classes("schedule-dropdown")
                        .style("width: 220px;")
                    )
                    table_day_filter_select = (
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
                        .style("width: 160px;")
                    )
                table_view = schedule_table_view()

        # ---------------------------------------------------------
        # Update filter values
        # ---------------------------------------------------------

        def configured_names(attribute: str) -> list[str]:
            """Return configured names for faculty, rooms, or labs."""
            entry = controller.current
            config = entry.config if entry is not None else None
            config_data = getattr(config, "config", config)
            items = getattr(config_data, attribute, []) if config_data is not None else []
            names = []
            for item in items:
                if isinstance(item, str):
                    name = item
                elif isinstance(item, dict):
                    name = item.get("name")
                else:
                    name = getattr(item, "name", None)
                if name:
                    names.append(str(name))
            return names

        def update_calendar_filter_values():
            """Populate the selection dropdown for Faculty or Room / Lab views."""
            view = calendar_view_select.value
            current_value = calendar_value_select.value

            show_entire_schedule_filters = view == "Entire Schedule"
            calendar_filter_select.visible = show_entire_schedule_filters
            calendar_filter_value_select.visible = show_entire_schedule_filters

            if view == "Faculty":
                values = configured_names("faculty") or sorted(
                    {row["faculty"] for row in schedule if row.get("faculty")}
                )
                calendar_value_select.props('label="Faculty Member"')
                calendar_value_select.enable()
                calendar_value_select.visible = True
            elif view == "Room / Lab":
                entry = controller.current
                records = entry.records if entry is not None else []
                values = configured_names("rooms") + configured_names("labs")
                if not values:
                    values = sorted(
                        {
                            resource
                            for record in records
                            for resource in (record.get("room"), record.get("lab"))
                            if resource and resource not in {"Online", "Unassigned"}
                        }
                    )
                if not values:
                    values = sorted(
                        {
                            row["resource"]
                            for row in schedule
                            if row.get("resource") not in {None, "", "Online", "Unassigned"}
                        }
                    )
                calendar_value_select.props('label="Room / Lab"')
                calendar_value_select.enable()
                calendar_value_select.visible = True
            else:
                values = []
                calendar_value_select.visible = False

            calendar_value_select.options = values
            calendar_value_select.value = (
                current_value if current_value in values else (values[0] if values else None)
            )
            calendar_value_select.update()

        def update_calendar_filter_value_values():
            """Populate the optional filter value for Entire Schedule view."""
            filter_type = calendar_filter_select.value
            if filter_type == "Course":
                values = sorted({row["course"] for row in schedule if row.get("course")})
            elif filter_type == "Faculty":
                values = configured_names("faculty") or sorted(
                    {row["faculty"] for row in schedule if row.get("faculty")}
                )
            elif filter_type == "Room / Lab":
                values = configured_names("rooms") + configured_names("labs")
                if not values:
                    values = sorted(
                        {row["resource"] for row in schedule if row.get("resource")}
                    )
            else:
                values = []

            current_value = calendar_filter_value_select.value
            calendar_filter_value_select.options = values
            calendar_filter_value_select.value = (
                current_value if current_value in values else (values[0] if values else None)
            )
            calendar_filter_value_select.set_enabled(filter_type != "None" and bool(values))
            calendar_filter_value_select.update()

        def update_table_filter_values():
            filter_type = table_filter_select.value
            if filter_type == "Course":
                values = sorted({row["course"] for row in schedule if row.get("course")})
            elif filter_type == "Faculty":
                values = sorted({row["faculty"] for row in schedule if row.get("faculty")})
            elif filter_type == "Room / Lab":
                values = sorted({row["resource"] for row in schedule if row.get("resource")})
            else:
                values = []

            current_value = table_filter_value_select.value
            table_filter_value_select.options = values
            table_filter_value_select.value = (
                current_value if current_value in values else (values[0] if values else None)
            )
            table_filter_value_select.set_enabled(filter_type != "None" and bool(values))
            table_filter_value_select.update()

        # ---------------------------------------------------------
        # Update table and calendar
        # ---------------------------------------------------------

        def update_table():
            # The Table tab owns its own filters and day selection.
            table_schedule = schedule.copy()
            filter_type = table_filter_select.value
            filter_value = table_filter_value_select.value

            if filter_type == "Course" and filter_value:
                table_schedule = filter_by_course(table_schedule, filter_value)
            elif filter_type == "Faculty" and filter_value:
                table_schedule = filter_by_faculty(table_schedule, filter_value)
            elif filter_type == "Room / Lab" and filter_value:
                table_schedule = filter_by_resource(table_schedule, filter_value)

            selected_table_day = table_day_filter_select.value
            if selected_table_day:
                table_schedule = [
                    row for row in table_schedule if row.get("day") == selected_table_day
                ]
            table_view.update(table_schedule)

            # Build the Calendar independently from the Table filters.
            view = calendar_view_select.value
            selected_value = calendar_value_select.value
            calendar_schedule = schedule.copy()

            if view == "Faculty" and selected_value:
                calendar_schedule = filter_by_faculty(calendar_schedule, selected_value)
            elif view == "Room / Lab" and selected_value:
                entry = controller.current
                records = entry.records if entry is not None else []

                # Find every course that uses the selected room or lab.
                matching_courses = {
                    record.get("course")
                    for record in records
                    if selected_value in (record.get("room"), record.get("lab"))
                    and record.get("course")
                }

                if matching_courses:
                    # Show all room and lab assignments connected to those courses.
                    calendar_schedule = [
                        row
                        for row in calendar_schedule
                        if row.get("course") in matching_courses
                    ]
                else:
                    calendar_schedule = [
                        row
                        for row in calendar_schedule
                        if row.get("resource") == selected_value
                    ]
            elif view == "Entire Schedule":
                filter_type = calendar_filter_select.value
                filter_value = calendar_filter_value_select.value
                if filter_type == "Course" and filter_value:
                    calendar_schedule = filter_by_course(calendar_schedule, filter_value)
                elif filter_type == "Faculty" and filter_value:
                    calendar_schedule = filter_by_faculty(calendar_schedule, filter_value)
                elif filter_type == "Room / Lab" and filter_value:
                    calendar_schedule = filter_by_resource(calendar_schedule, filter_value)

            selected_calendar_day = calendar_day_filter_select.value
            if selected_calendar_day:
                calendar_schedule = [
                    row for row in calendar_schedule if row.get("day") == selected_calendar_day
                ]

            calendar_view.update(
                calendar_schedule,
                selected_calendar_day,
                display_mode=view,
                color_schedule=schedule,
            )

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

            update_calendar_filter_values()
            update_calendar_filter_value_values()
            update_table_filter_values()
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

        def open_export_dialog():
            entry = controller.current
            if entry is None:
                return
            export_description.text = (
                f"Download '{entry.label}' to your browser's default location. "
                f"Check your browser settings to manually choose the save location."
            )
            export_status.text = ""
            try:
                export_name.value = controller.default_export_file_name(export_format.value)
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

            # Renee: if the viewer is filtered by a faculty member or a room/lab,
            # open on that one (e.g. Group by Faculty, "Hobbes"). Otherwise this
            # returns the normal default: Group by Room / lab, all rooms.
            # The user can still change both dropdowns before printing.
            if calendar_view_select.value == "Faculty":
                print_filter, print_value = "Faculty", calendar_value_select.value
            elif calendar_view_select.value == "Room / Lab":
                print_filter, print_value = "Room / Lab", calendar_value_select.value
            else:
                print_filter = calendar_filter_select.value
                print_value = calendar_filter_value_select.value
            group_by, group_key = print_defaults_for_filter(
                print_entry, print_filter, print_value
            )
            print_orientation.value = group_by
            update_print_group_options()
            print_group.set_value(group_key)

            print_export_dialog.open()

        def on_print_export():
            export, error = export_print_schedule(
                print_entry,
                print_orientation.value,
                print_group.value,
            )
            if error or export is None:
                print_export_status.text = error or "Could not prepare the PDF."
                return
            content, file_name, media_type = export
            ui.download(content, filename=file_name, media_type=media_type)
            print_export_dialog.close()
            ui.notify(f"Downloaded {file_name}.", type="positive")


        def on_export_format_changed(event):
            name = (export_name.value or "").strip()
            stem = name.rsplit(".", 1)[0] if name.lower().endswith((".csv", ".json")) else name
            if stem:
                export_name.value = f"{stem}.{event.value}"
                return
            try:
                export_name.value = controller.default_export_file_name(event.value)
                export_status.text = ""
            except OSError as error:
                export_status.text = str(error)

        def on_export():
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
            ui.notify(
                f"Exporting {file_name};",
                type="positive",
            )

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

        schedule_select.on_value_change(on_schedule_selected)

        def on_calendar_view_changed(_):
            update_calendar_filter_values()
            update_calendar_filter_value_values()
            update_table()

        calendar_view_select.on_value_change(on_calendar_view_changed)
        calendar_value_select.on_value_change(lambda _: update_table())
        calendar_filter_select.on_value_change(
            lambda _: (update_calendar_filter_value_values(), update_table())
        )
        calendar_filter_value_select.on_value_change(lambda _: update_table())
        calendar_day_filter_select.on_value_change(lambda _: update_table())

        table_filter_select.on_value_change(
            lambda _: (update_table_filter_values(), update_table())
        )
        table_filter_value_select.on_value_change(lambda _: update_table())
        table_day_filter_select.on_value_change(lambda _: update_table())

        reset_filters_button.on_click(lambda _: reset_filters())

        # ---------------------------------------------------------
        # Initial state
        # ---------------------------------------------------------

        controller.sync_generated()
        show_selected_schedule()
        ui.timer(1.0, check_for_generated_schedules)

    return refresh_viewer
