"""Schedule Viewer tab: browse, filter, and export generated schedules.

Each ScheduleResult holds a list of scheduler CourseInstance objects:
  - inst.course     -> Course (str(course) == "CS 101.01", .course_id == "CS 101")
  - inst.faculty    -> str
  - inst.room       -> str | None
  - inst.lab        -> str | None
  - inst.time       -> TimeSlot (str(time) is the compact CLI format)
  - inst.times      -> list[TimeInstance]  (.day, .start, .stop, .duration, .delivery)
  - inst.lab_index  -> index into .times of the lab meeting, or None
"""

import json
import zlib

from nicegui import ui

from schedule_result import ScheduleResult
from views.common import section_header, status_card
from views.gui_state import state

MUTED = "text-[#9fb2b8]"
BORDER = "border-[#29404b]"
PANEL = "bg-[#182630]"

DAYS = ("MON", "TUE", "WED", "THU", "FRI")
DAY_LETTER = {"MON": "M", "TUE": "T", "WED": "W", "THU": "R", "FRI": "F"}
HOUR_PX = 64

# Distinct hues that read well on the dark background; one per course_id.
PALETTE = (
    "#75e6da", "#f4a261", "#a78bfa", "#f472b6",
    "#86efac", "#facc15", "#60a5fa", "#fb7185",
)

FIELDS = ("course", "faculty", "room", "lab", "times")
COLUMNS = [
    {"name": f, "label": f.capitalize(), "field": f, "sortable": f != "times", "align": "left"}
    for f in FIELDS
]


# ---------------------------------------------------------------------------
# Formatting helpers (no UI)
# ---------------------------------------------------------------------------

def _clock(minutes: int) -> str:
    """Minutes since midnight -> '9:05am'."""
    hour, minute = divmod(minutes, 60)
    suffix = "am" if hour < 12 else "pm"
    return f"{(hour - 1) % 12 + 1}:{minute:02d}{suffix}"


def _meetings(inst) -> list[tuple[object, bool]]:
    """(TimeInstance, is_lab) for every meeting of a section, in pattern order."""
    lab_index = inst.lab_index
    return [(t, i == lab_index) for i, t in enumerate(inst.times)]


def _format_meetings(inst) -> str:
    """Group meetings with identical times: 'MWF 9:00am–9:50am, R 1:00pm–2:50pm (lab)'."""
    groups: dict[tuple, list[str]] = {}
    for t, is_lab in _meetings(inst):
        key = (t.start.value, t.stop.value, is_lab, t.delivery)
        groups.setdefault(key, []).append(DAY_LETTER.get(t.day.name, t.day.name))

    parts = []
    for (start, stop, is_lab, delivery), days in groups.items():
        text = f"{''.join(days)} {_clock(start)}–{_clock(stop)}"
        tags = [tag for tag, on in (("lab", is_lab), ("online", delivery == "online")) if on]
        if tags:
            text += f" ({', '.join(tags)})"
        parts.append(text)
    return ", ".join(parts)


def _record(inst) -> dict[str, str]:
    return {
        "course": str(inst.course),
        "faculty": inst.faculty,
        "room": inst.room or "—",
        "lab": inst.lab or "—",
        "times": _format_meetings(inst),
    }


def _color(inst) -> str:
    course_id = getattr(inst.course, "course_id", str(inst.course))
    return PALETTE[zlib.crc32(course_id.encode()) % len(PALETTE)]


def _stems(schedules: list[ScheduleResult]) -> list[str]:
    """File stems numbered per config, matching export_schedules: <config>_schedule<n>."""
    counts: dict[str, int] = {}
    stems = []
    for result in schedules:
        counts[result.config_name] = counts.get(result.config_name, 0) + 1
        stems.append(f"{result.config_name}_schedule{counts[result.config_name]}")
    return stems


def _week_filter_options(result: ScheduleResult) -> dict[str, str]:
    faculty = sorted({inst.faculty for inst in result.schedule})
    places = sorted(
        {inst.room for inst in result.schedule if inst.room}
        | {inst.lab for inst in result.schedule if inst.lab}
    )
    options = {"all": "All sections"}
    options |= {f"faculty::{name}": f"Faculty: {name}" for name in faculty}
    options |= {f"place::{name}": f"Room/Lab: {name}" for name in places}
    return options


def _week_entries(result: ScheduleResult, key: str) -> dict[str, list[dict]]:
    """Meetings to draw on the week grid, grouped by day, with overlap lanes assigned."""
    by_day: dict[str, list[dict]] = {day: [] for day in DAYS}

    for inst in result.schedule:
        for t, is_lab in _meetings(inst):
            online = t.delivery == "online"
            location = None if online else (inst.lab if is_lab else inst.room)

            if key.startswith("faculty::") and inst.faculty != key.removeprefix("faculty::"):
                continue
            if key.startswith("place::"):
                place = key.removeprefix("place::")
                # A lab meeting can also hold the lecture room (reserve_room_during_lab).
                holds_room = is_lab and inst.room == place and inst.reserve_room_during_lab
                if location != place and not holds_room:
                    continue

            if t.day.name in by_day:
                by_day[t.day.name].append({
                    "inst": inst,
                    "start": t.start.value,
                    "stop": t.stop.value,
                    "is_lab": is_lab,
                    "online": online,
                    "location": location,
                })

    for entries in by_day.values():
        _assign_lanes(entries)
    return by_day


def _assign_lanes(entries: list[dict]) -> None:
    """Greedy interval partitioning so overlapping meetings sit side by side."""
    entries.sort(key=lambda e: (e["start"], e["stop"]))
    lane_ends: list[int] = []
    for entry in entries:
        for lane, end in enumerate(lane_ends):
            if end <= entry["start"]:
                lane_ends[lane] = entry["stop"]
                entry["lane"] = lane
                break
        else:
            entry["lane"] = len(lane_ends)
            lane_ends.append(entry["stop"])
    for entry in entries:
        entry["lanes"] = len(lane_ends)


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------

def _download_csv(result: ScheduleResult, stem: str) -> None:
    # Same header and row format as schedule_service.export_schedules.
    lines = ["course,faculty,room,lab,times"] + [inst.as_csv() for inst in result.schedule]
    ui.download.content("\n".join(lines), f"{stem}.csv", "text/csv")


def _download_json(result: ScheduleResult, stem: str) -> None:
    data = [
        {
            "course": str(inst.course),
            "faculty": inst.faculty,
            "room": inst.room,
            "lab": inst.lab,
            "times": str(inst.time) if inst.lab is not None else str(inst.time).replace("^", ""),
        }
        for inst in result.schedule
    ]
    ui.download.content(json.dumps(data, indent=4), f"{stem}.json", "application/json")


# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------

def _set(**changes) -> None:
    for name, value in changes.items():
        setattr(state, name, value)
    show_schedules.refresh()


def _summary(result: ScheduleResult) -> None:
    sections = result.schedule
    faculty = {inst.faculty for inst in sections}
    rooms = {inst.room for inst in sections if inst.room}
    labs = {inst.lab for inst in sections if inst.lab}
    courses = {getattr(inst.course, "course_id", str(inst.course)) for inst in sections}

    with ui.row().classes("w-full gap-4"):
        status_card("Sections", str(len(sections)), f"{len(courses)} distinct courses", "class")
        status_card("Faculty", str(len(faculty)), "assigned to at least one section", "person")
        status_card("Rooms", str(len(rooms)), "lecture rooms in use", "meeting_room")
        status_card("Labs", str(len(labs)), "lab spaces in use", "science")


def _table(result: ScheduleResult) -> None:
    search = (
        ui.input(placeholder="Filter by course, faculty, room, time…")
        .props("outlined dense clearable")
        .classes("w-full max-w-md")
    )
    search.props("prepend-icon=search")

    rows = [{"id": i, **_record(inst)} for i, inst in enumerate(result.schedule)]
    table = (
        ui.table(columns=COLUMNS, rows=rows, row_key="id", pagination=25)
        .props("flat bordered dark")
        .classes(f"w-full {PANEL}")
    )
    search.bind_value_to(table, "filter")


def _week(result: ScheduleResult) -> None:
    options = _week_filter_options(result)
    if state.week_filter not in options:
        # A whole department on one grid is crowded, so start with one person.
        faculty_keys = [k for k in options if k.startswith("faculty::")]
        state.week_filter = faculty_keys[0] if faculty_keys else "all"

    ui.select(
        options,
        value=state.week_filter,
        label="Show",
        with_input=True,
        on_change=lambda e: _set(week_filter=e.value),
    ).props("outlined dense").classes("w-full max-w-md")

    by_day = _week_entries(result, state.week_filter)
    entries = [e for day in by_day.values() for e in day]
    if not entries:
        ui.label("No meetings to show for this selection.").classes(f"{MUTED} py-8")
        return

    first = min(e["start"] for e in entries) // 60 * 60
    last = -(-max(e["stop"] for e in entries) // 60) * 60  # round up to the hour
    height = (last - first) / 60 * HOUR_PX
    hours = range(first, last, 60)

    def y(minutes: int) -> float:
        return (minutes - first) / 60 * HOUR_PX

    with ui.element("div").classes(f"w-full overflow-x-auto rounded-lg border {BORDER} {PANEL}"):
        with ui.element("div").classes("grid min-w-[760px]").style(
            "grid-template-columns: 64px repeat(5, minmax(0, 1fr))"
        ):
            # Header row
            ui.element("div").classes(f"border-b {BORDER}")
            for day in DAYS:
                ui.label(day.title()).classes(
                    f"border-b border-l {BORDER} py-2 text-center text-sm font-semibold text-white"
                )

            # Time gutter
            with ui.element("div").classes("relative").style(f"height: {height}px"):
                for minutes in hours:
                    ui.label(_clock(minutes)).classes(
                        f"absolute right-2 text-[11px] {MUTED}"
                    ).style(f"top: {y(minutes) + 2}px")

            # Day columns
            for day in DAYS:
                with ui.element("div").classes(f"relative border-l {BORDER}").style(f"height: {height}px"):
                    for minutes in hours[1:]:
                        ui.element("div").classes(f"absolute w-full border-t {BORDER}").style(
                            f"top: {y(minutes)}px"
                        )
                    for entry in by_day[day]:
                        _week_block(entry, y)


def _week_block(entry: dict, y) -> None:
    inst = entry["inst"]
    color = _color(inst)
    width = 100 / entry["lanes"]
    left = entry["lane"] * width
    top = y(entry["start"])
    block_height = y(entry["stop"]) - top

    where = "Online" if entry["online"] else (entry["location"] or "No room")
    if entry["is_lab"]:
        where += " · Lab"

    with ui.element("div").classes(
        "absolute overflow-hidden rounded-md px-1.5 py-1 text-[11px] leading-tight text-[#e8f1f2]"
    ).style(
        f"top: {top + 1}px; height: {block_height - 2}px; "
        f"left: calc({left}% + 2px); width: calc({width}% - 4px); "
        f"background: {color}2e; border-left: 3px solid {color};"
    ):
        ui.label(str(inst.course)).classes("font-semibold")
        ui.label(where).classes("truncate")
        if state.week_filter is None or not state.week_filter.startswith("faculty::"):
            ui.label(inst.faculty).classes(f"truncate {MUTED}")
        ui.tooltip(
            f"{inst.course} · {inst.faculty} · {_clock(entry['start'])}–{_clock(entry['stop'])} · {where}"
        )


@ui.refreshable
def show_schedules() -> None:
    schedules = state.schedules

    if not schedules:
        with ui.column().classes(f"w-full items-center gap-2 rounded-lg border {BORDER} py-16 {MUTED}"):
            ui.icon("event_busy", size="48px")
            ui.label("No schedules generated yet.").classes("text-base text-white")
            ui.label("Run the Schedule Generator and results will appear here.").classes("text-sm")
        return

    if state.selected_schedule >= len(schedules):
        state.selected_schedule = 0

    stems = _stems(schedules)
    index = state.selected_schedule
    result = schedules[index]
    stem = stems[index]
    options = {i: s.replace("_schedule", " — schedule ") for i, s in enumerate(stems)}

    with ui.row().classes("w-full items-center gap-4"):
        ui.select(
            options,
            value=index,
            label="Schedule",
            on_change=lambda e: _set(selected_schedule=e.value),
        ).props("outlined dense").classes("min-w-[280px]")

        ui.toggle(
            {"table": "Table", "week": "Week"},
            value=state.viewer_mode,
            on_change=lambda e: _set(viewer_mode=e.value),
        ).props("no-caps toggle-color=primary toggle-text-color=dark text-color=grey-4")

        ui.space()
        ui.button("CSV", icon="download", on_click=lambda: _download_csv(result, stem)).props("outline no-caps")
        ui.button("JSON", icon="data_object", on_click=lambda: _download_json(result, stem)).props("outline no-caps")

    _summary(result)

    if state.viewer_mode == "week":
        _week(result)
    else:
        _table(result)


def schedule_viewer() -> None:
    with ui.column().classes("w-full gap-6"):
        section_header(
            "Results",
            "Schedule Viewer",
            "Browse generated schedules as a table or a weekly calendar, filter by "
            "faculty or room, and export to CSV or JSON.",
        )
        show_schedules()