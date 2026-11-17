"""Calculate summary statistics for a schedule entry."""

import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from itertools import pairwise
from math import exp, log
from statistics import pstdev

from scheduler.config import CombinedConfig, LabConfig, RoomConfig

from src.models.schedule_viewer_model import ScheduleEntry

DAYS = ("MON", "TUE", "WED", "THU", "FRI")
MIN_EMPTY_BLOCK_MINUTES = 30
_MEETING_PATTERN = re.compile(
    r"^(?P<day>MON|TUE|WED|THU|FRI) "
    r"(?P<start>\d{2}):(?P<start_minute>\d{2})-"
    r"(?P<end>\d{2}):(?P<end_minute>\d{2})(?:@online)?\^?$"
)


@dataclass(frozen=True)
class FacultyWorkload:
    """Weekly scheduled workload for one faculty member."""

    faculty: str
    sections: int
    teaching_hours: float
    hours_by_day: dict[str, float]
    longest_daily_span_hours: float
    gap_minutes: int = 0


@dataclass(frozen=True)
class ResourceUsage:
    """Scheduled usage totals for one room or lab."""

    resource: str
    meetings: int
    used_hours: float
    hours_by_day: dict[str, float]
    available_hours: float | None = None

    @property
    def utilization_percent(self) -> float | None:
        if self.available_hours is None or self.available_hours <= 0:
            return None
        return round(self.used_hours / self.available_hours * 100, 1)

    @property
    def unused_hours(self) -> float | None:
        if self.available_hours is None:
            return None
        return round(max(0, self.available_hours - self.used_hours), 2)


@dataclass(frozen=True)
class UnscheduledCourse:
    """A configured course section not present in the selected schedule."""

    course: str
    section: str


@dataclass(frozen=True)
class ScheduleAnalysis:
    """Schedule metrics, with configuration-dependent values when available."""

    schedule_label: str
    scheduled_sections: int
    faculty_assigned: int
    weekday_meetings: dict[str, int]
    faculty_workload: list[FacultyWorkload]
    room_utilization: list[ResourceUsage]
    lab_utilization: list[ResourceUsage]
    unscheduled_courses: list[UnscheduledCourse] | None
    available_empty_blocks: int | None
    early_starts: int
    late_ends: int
    weekday_teaching_hours: dict[str, float] = field(default_factory=dict)

    @property
    def faculty_gap_penalty(self) -> int:
        return sum(workload.gap_minutes**2 for workload in self.faculty_workload)

    @property
    def room_utilization_geomean_percent(self) -> float | None:
        return _resource_utilization_geomean(self.room_utilization)

    @property
    def lab_utilization_geomean_percent(self) -> float | None:
        return _resource_utilization_geomean(self.lab_utilization)

    @property
    def faculty_workload_stddev_hours(self) -> float | None:
        if not self.faculty_workload:
            return None
        return round(pstdev(item.teaching_hours for item in self.faculty_workload), 2)

    @property
    def weekday_teaching_hours_stddev(self) -> float | None:
        if self.scheduled_sections == 0:
            return None
        return round(
            pstdev(self.weekday_teaching_hours.get(day, 0) for day in DAYS),
            2,
        )


def _resource_utilization_geomean(
    resources: list[ResourceUsage],
) -> float | None:
    utilizations = [
        resource.used_hours / resource.available_hours * 100
        for resource in resources
        if resource.available_hours is not None and resource.available_hours > 0
    ]
    if not utilizations:
        return None
    if any(utilization == 0 for utilization in utilizations):
        return 0.0
    return round(exp(sum(log(utilization) for utilization in utilizations) / len(utilizations)), 1)


def _meeting_duration(meeting: str, course: str) -> tuple[str, int, int]:
    """Return a meeting's weekday and start/end minutes, or raise for bad data."""
    match = _MEETING_PATTERN.fullmatch(meeting.strip())
    if match is None:
        raise ValueError(f"Unrecognized meeting time '{meeting.strip()}' for {course}.")

    start_hour = int(match["start"])
    start_minute = int(match["start_minute"])
    end_hour = int(match["end"])
    end_minute = int(match["end_minute"])
    if (
        start_hour > 23
        or end_hour > 23
        or start_minute > 59
        or end_minute > 59
    ):
        raise ValueError(f"Invalid clock time '{meeting.strip()}' for {course}.")

    start = start_hour * 60 + start_minute
    end = end_hour * 60 + end_minute
    if end <= start:
        raise ValueError(f"Meeting end must follow its start for {course}: '{meeting.strip()}'.")

    return match["day"], start, end


def _hours(minutes: int) -> float:
    return round(minutes / 60, 2)


def _minutes(time: str) -> int:
    hour, minute = time.split(":")
    return int(hour) * 60 + int(minute)


def _merged_ranges(ranges: list[tuple[int, int]]) -> list[tuple[int, int]]:
    merged: list[tuple[int, int]] = []
    for start, end in sorted(ranges):
        if merged and start <= merged[-1][1]:
            merged[-1] = merged[-1][0], max(merged[-1][1], end)
        else:
            merged.append((start, end))
    return merged


def _configured_windows(config: CombinedConfig) -> dict[str, list[tuple[int, int]]]:
    return {
        day: _merged_ranges(
            [
                (_minutes(block.start), _minutes(block.end))
                for block in config.time_slot_config.times.get(day, [])
            ]
        )
        for day in DAYS
    }


def _availability_windows(
    availability: dict | None,
    configured_windows: dict[str, list[tuple[int, int]]],
) -> dict[str, list[tuple[int, int]]]:
    if availability is None:
        return configured_windows

    result: dict[str, list[tuple[int, int]]] = {}
    for day in DAYS:
        configured = configured_windows[day]
        available = _merged_ranges(
            [(_minutes(item.start), _minutes(item.end)) for item in availability.get(day, [])]
        )
        if not configured:
            result[day] = available
            continue

        intersections = []
        for available_start, available_end in available:
            for window_start, window_end in configured:
                start = max(available_start, window_start)
                end = min(available_end, window_end)
                if start < end:
                    intersections.append((start, end))
        result[day] = _merged_ranges(intersections)
    return result


def _available_hours(windows: dict[str, list[tuple[int, int]]]) -> float:
    return _hours(
        sum(end - start for ranges in windows.values() for start, end in ranges)
    )


def _unused_blocks(
    availability: dict[str, list[tuple[int, int]]],
    scheduled: dict[str, list[tuple[int, int]]],
) -> int:
    count = 0
    for day in DAYS:
        busy_ranges = _merged_ranges(scheduled.get(day, []))
        for available_start, available_end in availability[day]:
            cursor = available_start
            for busy_start, busy_end in busy_ranges:
                if busy_end <= cursor or busy_start >= available_end:
                    continue
                gap_end = min(busy_start, available_end)
                if gap_end - cursor >= MIN_EMPTY_BLOCK_MINUTES:
                    count += 1
                cursor = max(cursor, min(busy_end, available_end))
            if available_end - cursor >= MIN_EMPTY_BLOCK_MINUTES:
                count += 1
    return count


def _internal_gap_minutes(ranges: list[tuple[int, int]]) -> int:
    merged = _merged_ranges(ranges)
    return sum(
        next_start - current_end
        for (_, current_end), (next_start, _) in pairwise(merged)
    )


def _configured_courses(
    config: CombinedConfig,
    scheduled_names: set[str],
) -> list[UnscheduledCourse]:
    section_counts: Counter[str] = Counter()
    unscheduled = []
    for course in config.config.courses:
        section_counts[course.course_id] += 1
        section = course.section_id or f"{section_counts[course.course_id]:02d}"
        if f"{course.course_id}.{section}" not in scheduled_names:
            unscheduled.append(UnscheduledCourse(course.course_id, section))
    return unscheduled


def _resource_usage(
    totals: dict[str, int],
    daily_totals: dict[str, dict[str, int]],
    meetings: Counter[str],
    resources: list[RoomConfig] | list[LabConfig],
    configured_windows: dict[str, list[tuple[int, int]]],
) -> list[ResourceUsage]:
    availability_by_resource = {
        resource.name: _availability_windows(resource.times, configured_windows)
        for resource in resources
    }
    resource_names = sorted(set(totals) | set(availability_by_resource))
    return [
        ResourceUsage(
            resource=resource,
            meetings=meetings[resource],
            used_hours=_hours(totals.get(resource, 0)),
            hours_by_day={
                day: _hours(daily_totals[resource].get(day, 0)) for day in DAYS
            },
            available_hours=(
                _available_hours(availability_by_resource[resource])
                if resource in availability_by_resource
                else None
            ),
        )
        for resource in resource_names
    ]


class ScheduleAnalysisModel:
    """Derive schedule statistics from the schedule records."""

    def analyze(self, entry: ScheduleEntry | None) -> ScheduleAnalysis | None:
        """Analyze a schedule, returning ``None`` when no schedule is selected."""
        if entry is None:
            return None

        weekday_meetings: Counter[str] = Counter()
        weekday_minutes: dict[str, int] = defaultdict(int)
        faculty_sections: dict[str, set[str]] = defaultdict(set)
        faculty_daily: dict[str, dict[str, int]] = defaultdict(
            lambda: defaultdict(int)
        )
        faculty_spans: dict[str, dict[str, list[int]]] = defaultdict(
            lambda: defaultdict(list)
        )
        room_totals: dict[str, int] = defaultdict(int)
        room_daily: dict[str, dict[str, int]] = defaultdict(
            lambda: defaultdict(int)
        )
        room_meetings: Counter[str] = Counter()
        lab_totals: dict[str, int] = defaultdict(int)
        lab_daily: dict[str, dict[str, int]] = defaultdict(
            lambda: defaultdict(int)
        )
        lab_meetings: Counter[str] = Counter()
        early_starts = 0
        late_ends = 0
        faculty_scheduled: dict[str, dict[str, list[tuple[int, int]]]] = defaultdict(
            lambda: defaultdict(list)
        )
        scheduled_names: set[str] = set()

        for record in entry.records:
            course = record.get("course", "").strip()
            faculty = record.get("faculty", "").strip()
            scheduled_names.add(course)
            meetings = record.get("times", "").split(",")

            if faculty:
                faculty_sections[faculty].add(course)

            for meeting_text in meetings:
                if not meeting_text.strip():
                    continue
                day, start, end = _meeting_duration(meeting_text, course)
                duration = end - start
                weekday_meetings[day] += 1
                weekday_minutes[day] += duration
                early_starts += start < 9 * 60
                late_ends += end > 17 * 60

                if faculty:
                    faculty_daily[faculty][day] += duration
                    faculty_spans[faculty][day].extend((start, end))
                    faculty_scheduled[faculty][day].append((start, end))

                room = record.get("room", "").strip()
                if room:
                    room_totals[room] += duration
                    room_daily[room][day] += duration
                    room_meetings[room] += 1

                lab = record.get("lab", "").strip()
                if lab:
                    lab_totals[lab] += duration
                    lab_daily[lab][day] += duration
                    lab_meetings[lab] += 1

        faculty_workload = []
        for faculty in sorted(faculty_sections):
            daily_minutes = faculty_daily[faculty]
            spans = faculty_spans[faculty]
            gap_minutes = sum(
                _internal_gap_minutes(ranges)
                for ranges in faculty_scheduled[faculty].values()
            )
            longest_span = max(
                (max(times) - min(times) for times in spans.values()),
                default=0,
            )
            faculty_workload.append(
                FacultyWorkload(
                    faculty=faculty,
                    sections=len(faculty_sections[faculty]),
                    teaching_hours=_hours(sum(daily_minutes.values())),
                    hours_by_day={day: _hours(daily_minutes.get(day, 0)) for day in DAYS},
                    longest_daily_span_hours=_hours(longest_span),
                    gap_minutes=gap_minutes,
                )
            )

        config = entry.config
        unscheduled_courses = None
        available_empty_blocks = None
        room_resources = []
        lab_resources = []
        configured_windows = {day: [] for day in DAYS}
        if config is not None:
            configured_windows = _configured_windows(config)
            unscheduled_courses = _configured_courses(config, scheduled_names)
            faculty_configs = {item.name: item for item in config.config.faculty}
            available_empty_blocks = sum(
                _unused_blocks(
                    _availability_windows(item.times, configured_windows),
                    faculty_scheduled.get(item.name, {}),
                )
                for item in faculty_configs.values()
            )
            room_resources = config.config.rooms
            lab_resources = config.config.labs

        return ScheduleAnalysis(
            schedule_label=entry.label,
            scheduled_sections=len(entry.records),
            faculty_assigned=len(faculty_sections),
            weekday_meetings={day: weekday_meetings.get(day, 0) for day in DAYS},
            faculty_workload=faculty_workload,
            room_utilization=_resource_usage(
                room_totals,
                room_daily,
                room_meetings,
                room_resources,
                configured_windows,
            ),
            lab_utilization=_resource_usage(
                lab_totals,
                lab_daily,
                lab_meetings,
                lab_resources,
                configured_windows,
            ),
            unscheduled_courses=unscheduled_courses,
            available_empty_blocks=available_empty_blocks,
            early_starts=early_starts,
            late_ends=late_ends,
            weekday_teaching_hours={
                day: _hours(weekday_minutes.get(day, 0)) for day in DAYS
            },
        )
