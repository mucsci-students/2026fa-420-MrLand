# File name: schedule_view.py
# Primary author: Dylan Groff


from nicegui import ui
from src.controllers.schedule_filters_controller import (
    sort_schedule,
    filter_by_resource,
    filter_by_faculty,
    filter_by_course,
)

# set the background and accent colors for the schedule viewer
BACKGROUND = "#101820"
ACCENT = "#75e6da"


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
        # Progress dialogs
        # ---------------------------------------------------------
        
        # creates a progress bar pop-up for loading schedules
        with ui.dialog() as load_dialog:
            with ui.card().classes("bg-[#101820]"):
                ui.label("Loading schedule...").classes(
                    "text-lg text-white"
                )

                load_progress = ui.linear_progress(
                    value=0
                ).classes("w-80")


        # creates a progress bar pop-up for exporting schedules
        with ui.dialog() as export_dialog:
            with ui.card().classes("bg-[#101820]"):
                ui.label("Exporting schedule...").classes(
                    "text-lg text-white"
                )

                export_progress = ui.linear_progress(
                    value=0
                ).classes("w-80")


        # ---------------------------------------------------------
        # Schedule controls
        # ---------------------------------------------------------

        with ui.row().classes("w-full items-center gap-3 mb-6"):


            # place your load function call/logic here
            def on_load():
                load_dialog.open()
                load_progress.value = 0

                # TODO: Call controller here
                # ...

                load_progress.value = 1
                # use this to close the dialog after loading is complete after implementing the load function in the controller
                #load_dialog.close()


            # place your export function call/logic here
            def on_export():
                export_dialog.open()
                export_progress.value = 0

                # TODO: Call controller here
                # ...

                export_progress.value = 1
                # use this to close the dialog after exporting is complete after implementing the export function in the controller
                #export_dialog.close()

            # Load button
            ui.button(
                "Load",
                icon="upload_file",
                on_click=on_load,
            ).props("outline")

            # Export button
            ui.button(
                "Export",
                icon="download",
                on_click=on_export,
            ).props("outline")

            ui.space()

            # button to iterate left through the schedules
            ui.button(
                icon="chevron_left",
            ).props("flat")

            # dropdown to select the schedule to view
            # will need to be populated with the actual available schedules
            ui.select(
                ["Schedule 1", "Schedule 2", "Schedule 3"],
                value="Schedule 1",
            ).props("outlined").classes("schedule-dropdown")

            # button to iterate right through the schedules
            ui.button(
                icon="chevron_right",
            ).props("flat")

        # ---------------------------------------------------------
        # Sample schedule data
        # ---------------------------------------------------------

        # will need to be replaced with actual schedule data from the load function
        # will also need func to format the data from the JSON or CSV file into the format used here
        schedule = [
            {
                "id": 1,
                "course": "CMSC 152.01",
                "faculty": "Hardy",
                "resource": "Roddy 147",
                "day": "MON",
                "start": "09:00",
                "end": "09:50",
            },
            {
                "id": 2,
                "course": "CMSC 162.01",
                "faculty": "Hogg",
                "resource": "Roddy 140",
                "day": "MON",
                "start": "10:00",
                "end": "10:50",
            },
            {
                "id": 3,
                "course": "CMSC 140.01",
                "faculty": "Hardy",
                "resource": "Roddy 147",
                "day": "MON",
                "start": "11:00",
                "end": "12:50",
            },
            {
                "id": 4,
                "course": "CMSC 161.03",
                "faculty": "Wertz",
                "resource": "Roddy 140",
                "day": "TUE",
                "start": "08:00",
                "end": "09:50",
            },
            {
                "id": 5,
                "course": "CMSC 152.01",
                "faculty": "Hardy",
                "resource": "Mac",
                "day": "THU",
                "start": "09:00",
                "end": "10:50",
            },
            {
                "id": 6,
                "course": "CMSC 340.01",
                "faculty": "Yang",
                "resource": "Roddy 136",
                "day": "FRI",
                "start": "14:00",
                "end": "14:50",
            },
        ]

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

        table = ui.table(
            columns=columns,
            rows=schedule,
            row_key="id",
            pagination=10,
        ).props("flat bordered").classes("w-full")

        # ---------------------------------------------------------
        # Update filter values
        # ---------------------------------------------------------

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

            filter_value_select.options = values

            if values:
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
        # Dropdown events
        # ---------------------------------------------------------

        sort_select.on_value_change(
            lambda _: update_table()
        )

        order_select.on_value_change(
            lambda _: update_table()
        )

        filter_select.on_value_change(
            lambda _: (
                update_filter_values(),
                update_table(),
            )
        )

        filter_value_select.on_value_change(
            lambda _: update_table()
        )

        # ---------------------------------------------------------
        # Initial state
        # ---------------------------------------------------------

        update_table()