# File name: schedule_viewer.py
# Primary author: Dylan Groff
# Secondary Author: Micah Schafer


from nicegui import ui
from src.controllers.schedule_controller import (
    schedule_controller as controller,
)
from src.controllers.schedule_filters_controller import (
    sort_schedule,
    filter_by_resource,
    filter_by_faculty,
    filter_by_course,
)
from src.controllers.schedule_inspection_controller import (
    get_course_details,
    get_faculty_details,
    get_room_details,
    get_lab_details,
)

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
                border-color: #75e6da !important;
            }}

            .schedule-dropdown .q-field--focused .q-field__control:after {{
                border-color: #75e6da !important;
            }}

            .schedule-dropdown .q-field__native,
            .schedule-dropdown .q-field__input,
            .schedule-dropdown .q-field__label,
            .schedule-dropdown .q-select__dropdown-icon {{
                color: #d8e7e8 !important;
            }}

            /* Table */
            .q-table__container,
            .q-table__middle,
            .q-table {{
                background: {BACKGROUND} !important;
            }}

            .q-table thead tr {{
                background: #17252d !important;
            }}

            .q-table tbody tr {{
                background: {BACKGROUND} !important;
            }}

            .q-table tbody tr:hover {{
                background: #1c3039 !important;
            }}

            .q-table th,
            .q-table td {{
                color: #d8e7e8 !important;
            }}

            /* Table pagination */
            .q-table__bottom {{
                background: {BACKGROUND} !important;
                color: #d8e7e8 !important;
                border-top: 1px solid #29404b !important;
            }}

            .q-table__bottom .q-field__native,
            .q-table__bottom .q-field__input,
            .q-table__bottom .q-field__label,
            .q-table__bottom .q-select__dropdown-icon {{
                color: #d8e7e8 !important;
            }}

            .q-table__bottom .q-btn {{
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
        # Save dialog
        # ---------------------------------------------------------

        with ui.dialog() as save_dialog:
            with ui.card().classes("bg-[#101820] border border-[#29404b] w-[480px] gap-3"):
                ui.label("Save Schedule").classes("text-lg font-semibold text-white")
                save_description = ui.label("").classes("text-sm text-gray-400")

                save_format = ui.select(
                    {"csv": "CSV", "json": "JSON"},
                    value="csv",
                    label="File Format",
                ).props("outlined dark").classes("schedule-dropdown w-full")

                save_name = ui.input(
                    label="File Name",
                ).props("outlined dark").classes("schedule-dropdown w-full")

                overwrite_checkbox = ui.checkbox(
                    "Overwrite if the file already exists"
                ).props("dark").classes("text-gray-300")

                save_status = ui.label("").classes("text-sm text-red-400")

                with ui.row().classes("w-full justify-end gap-2"):
                    ui.button("Cancel", on_click=save_dialog.close).props("flat")
                    download_button = ui.button(
                        "Download", icon="download"
                    ).props("outline")
                    save_button = ui.button("Save", icon="save")

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

            # Save button
            save_open_button = ui.button(
                "Save",
                icon="save",
                on_click=lambda: open_save_dialog(),
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

            sort_select = ui.select(
                [
                    "Day",
                    "Start Time",
                    "Course",
                    "Faculty",
                    "Room / Lab",
                ],
                value="Day",
                label="Sort",
            ).props("outlined").classes("schedule-dropdown").style(
                "width: 180px;"
            )

            filter_select = ui.select(
                [
                    "None",
                    "Course",
                    "Faculty",
                    "Room / Lab",
                ],
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

            order_select = ui.select(
                [
                    "Ascending",
                    "Descending",
                ],
                value="Ascending",
                label="Order",
            ).props("outlined").classes("schedule-dropdown").style(
                "width: 180px;"
            )

        # ---------------------------------------------------------
        # Table columns
        # ---------------------------------------------------------

        # create the columns the table will use
        columns = [
            {
                "name": "course",
                "label": "Course",
                "field": "course",
                "align": "left",
                "sortable": True,
            },
            {
                "name": "faculty",
                "label": "Faculty",
                "field": "faculty",
                "align": "left",
                "sortable": True,
            },
            {
                "name": "resource",
                "label": "Room / Lab",
                "field": "resource",
                "align": "left",
                "sortable": True,
            },
            {
                "name": "day",
                "label": "Day",
                "field": "day",
                "align": "left",
                "sortable": True,
            },
            {
                "name": "start",
                "label": "Start",
                "field": "start",
                "align": "left",
                "sortable": True,
            },
            {
                "name": "end",
                "label": "End",
                "field": "end",
                "align": "left",
                "sortable": True,
            },
        ]

        # create table object
        table = ui.table(
            columns=columns,
            rows=[],
            row_key="id",
            pagination=10,
        ).props("flat bordered").classes("w-full")

        # ---------------------------------------------------------
        # Add clickable cells to table
        # ---------------------------------------------------------

        table.add_slot(
            "body-cell-course",
            """
            <q-td :props="props">
                <q-btn
                    flat
                    dense
                    no-caps
                    :label="props.value"
                    @click="$parent.$emit('inspect-course', props.value)"
                />
            </q-td>
            """
        )

        table.on(
            "inspect-course",
            lambda event: inspect_course(event.args)
        )

        table.add_slot(
            "body-cell-faculty",
            """
            <q-td :props="props">
                <q-btn
                    flat
                    dense
                    no-caps
                    :label="props.value"
                    @click="$parent.$emit('inspect-faculty', props.value)"
                />
            </q-td>
            """
        )

        table.on(
            "inspect-faculty",
            lambda event: inspect_faculty(event.args)\
        )

        table.add_slot(
            "body-cell-resource",
            """
            <q-td :props="props">
                <q-btn
                    flat
                    dense
                    no-caps
                    :label="props.value"
                    @click="$parent.$emit('inspect-resource', props.row)"
                />
            </q-td>
            """
        )

        table.on(
            "inspect-resource",
            lambda event: inspect_resource(event.args)
        )

        table.add_slot(
            "body-cell-day",
            """
            <q-td :props="props">
                <q-btn
                    flat
                    dense
                    no-caps
                    :label="props.value"
                    @click="$parent.$emit('inspect-time', props.row)"
                />
            </q-td>
            """
        )

        table.on(
            "inspect-time",
            lambda event: inspect_time(event.args)
        )


        # ---------------------------------------------------------
        # Inspect Elements Methods
        # ---------------------------------------------------------
        def inspect_course(course_id):
            if controller.current is None or controller.current.config is None:
                ui.notify(
                    "Configuration details are unavailable for this schedule.",
                    type="warning",
                )
                return
            
            course = get_course_details(controller.current.config, course_id)

            if controller.current is None:
                ui.notify("No schedule selected", type="negative")
                return

            if course is None:
                ui.notify("Course details not found", type="negative")
                return

            with ui.dialog() as dialog:
                with ui.card():
                    ui.label("Course Details").classes("text-xl font-bold")

                    ui.label(f"Course ID: {course.course_id}")
                    ui.label(f"Section: {course.section_id}")
                    ui.label(f"Credits: {course.credits}")
                    ui.label(f"Capacity: {course.capacity}")
                    ui.label(f"Modality: {course.modality}")

                    ui.button("Close", on_click=dialog.close)

            dialog.open()

        def inspect_faculty(faculty_name):
            if controller.current is None or controller.current.config is None:
                ui.notify(
                    "Configuration details are unavailable for this schedule.",
                    type="warning",
                )
                return

            faculty = get_faculty_details(controller.current.config, faculty_name)

            if faculty is None:
                ui.notify("Faculty details not found", type="negative")
                return

            with ui.dialog() as dialog:
                with ui.card():
                    ui.label("Faculty Details").classes("text-xl font-bold")

                    ui.label(f"Name: {faculty.name}")
                    ui.label(f"Minimum Credits: {faculty.minimum_credits}")
                    ui.label(f"Maximum Credits: {faculty.maximum_credits}")
                    ui.label(f"Maximum Days: {faculty.maximum_days}")
                    ui.label(f"Unique Course Limit: {faculty.unique_course_limit}")

                    ui.button("Close", on_click=dialog.close)

            dialog.open()

        def inspect_room(room_name):
            if controller.current is None or controller.current.config is None:
                ui.notify(
                    "Configuration details are unavailable for this schedule.",
                    type="warning",
                )
                return

            room = get_room_details(controller.current.config, room_name)

            if room is None:
                ui.notify("Room details not found", type="negative")
                return

            with ui.dialog() as dialog:
                with ui.card():
                    ui.label("Room Details").classes("text-xl font-bold")

                    ui.label(f"Name: {room.name}")
                    ui.label(f"Capacity: {room.capacity}")
                    ui.label(f"Features: {', '.join(room.features)}")

                    ui.button("Close", on_click=dialog.close)

            dialog.open()

        def inspect_lab(lab_name):
            if controller.current is None or controller.current.config is None:
                ui.notify(
                    "Configuration details are unavailable for this schedule.",
                    type="warning",
                )
                return

            lab = get_lab_details(controller.current.config, lab_name)

            if lab is None:
                ui.notify("Lab details not found", type="negative")
                return

            with ui.dialog() as dialog:
                with ui.card():
                    ui.label("Lab Details").classes("text-xl font-bold")

                    ui.label(f"Name: {lab.name}")
                    ui.label(f"Capacity: {lab.capacity}")
                    ui.label(f"Features: {', '.join(lab.features)}")

                    ui.button("Close", on_click=dialog.close)

            dialog.open()

        def inspect_resource(row):
            resource = row["resource"]

            if not resource:
                ui.notify("This course has no room or lab assignment.", type="info")
                return

            # Lab meetings have a lab resource.
            # The resource itself doesn't tell us whether it is a lab,
            # so check the configuration.
            if get_lab_details(controller.current.config, resource) is not None:
                inspect_lab(resource)
            else:
                inspect_room(resource)


        def inspect_time(row):
            with ui.dialog() as dialog:
                with ui.card():
                    ui.label("Time Assignment").classes("text-xl font-bold")

                    ui.label(f"Course: {row['course']}")
                    ui.label(f"Faculty: {row['faculty']}")
                    ui.label(f"Day: {row['day']}")
                    ui.label(f"Start: {row['start']}")
                    ui.label(f"End: {row['end']}")

                    ui.button("Close", on_click=dialog.close)

            dialog.open()
            

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
            # ALWAYS start with the original schedule.
            # This prevents filters and sorting from stacking.
            updated_schedule = schedule.copy()

            # -----------------------------
            # Apply filter
            # -----------------------------

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

            # -----------------------------
            # Apply sort
            # -----------------------------

            sort_type = sort_select.value

            descending = order_select.value == "Descending"

            if sort_type == "Day":
                # Default chronological schedule:
                # Day -> Start Time
                updated_schedule = sort_schedule(
                    updated_schedule,
                    descending=descending,
                )

            elif sort_type == "Start Time":
                updated_schedule = sort_schedule(
                    updated_schedule,
                    "start",
                    descending=descending,
                )

            elif sort_type == "Course":
                updated_schedule = sort_schedule(
                    updated_schedule,
                    "course",
                    descending=descending,
                )

            elif sort_type == "Faculty":
                updated_schedule = sort_schedule(
                    updated_schedule,
                    "faculty",
                    descending=descending,
                )

            elif sort_type == "Room / Lab":
                updated_schedule = sort_schedule(
                    updated_schedule,
                    "resource",
                    descending=descending,
                )

            # -----------------------------
            # Update table
            # -----------------------------

            table.rows = updated_schedule
            table.update()

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
            save_open_button.set_enabled(has_schedules)
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
        # Saving
        # ---------------------------------------------------------

        def open_save_dialog():
            entry = controller.current
            if entry is None:
                return
            save_description.text = (
                f"Save '{entry.label}' to the schedules folder, "
                "or download it to your computer."
            )
            save_name.value = controller.default_file_name(save_format.value)
            overwrite_checkbox.value = False
            save_status.text = ""
            save_dialog.open()

        def on_format_changed(event):
            # keep the file name's extension in step with the format
            name = (save_name.value or "").strip()
            stem = name.rsplit(".", 1)[0] if name.lower().endswith((".csv", ".json")) else name
            save_name.value = (
                f"{stem}.{event.value}" if stem else controller.default_file_name(event.value)
            )

        def on_save():
            path, error = controller.save_current(
                save_format.value,
                save_name.value or "",
                overwrite=overwrite_checkbox.value,
            )
            if error:
                save_status.text = error
                return
            save_dialog.close()
            ui.notify(f"Saved {path.name} to the schedules folder", type="positive")

        def on_download():
            export, error = controller.export_current(
                save_format.value,
                save_name.value or "",
            )
            if error:
                save_status.text = error
                return
            content, file_name, media_type = export
            ui.download(content, filename=file_name, media_type=media_type)
            save_dialog.close()

        save_format.on_value_change(on_format_changed)
        save_button.on_click(on_save)
        download_button.on_click(on_download)

        # ---------------------------------------------------------
        # Dropdown events
        # ---------------------------------------------------------

        # updates when a different schedule is selected
        schedule_select.on_value_change(on_schedule_selected)

        # updates when a new sort is selected
        sort_select.on_value_change(
            lambda _: update_table()
        )

        # updates when a new order is selected
        order_select.on_value_change(
            lambda _: update_table()
        )

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

        # ---------------------------------------------------------
        # Initial state
        # ---------------------------------------------------------

        controller.sync_generated()
        show_selected_schedule()
        ui.timer(1.0, check_for_generated_schedules)
