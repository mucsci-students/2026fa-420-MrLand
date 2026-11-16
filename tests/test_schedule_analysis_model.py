from pathlib import Path

from scheduler.config import CombinedConfig
from scheduler.scheduler import Scheduler

from src.models.configuration_repository import load_config
from src.models.schedule_analysis_model import ScheduleAnalysisModel
from src.models.schedule_files import parse_schedule_file, records_from_result
from src.models.schedule_result import ScheduleResult
from src.models.schedule_viewer_model import ScheduleEntry


def analysis_config() -> CombinedConfig:
    weekdays = ("MON", "TUE", "WED", "THU", "FRI")
    return CombinedConfig.model_validate(
        {
            "config": {
                "rooms": [
                    {
                        "name": "Room 101",
                        "capacity": 30,
                        "times": {
                            "MON": [{"start": "09:00", "end": "11:00"}],
                        },
                    }
                ],
                "labs": [
                    {"name": "Lab A", "capacity": 30},
                ],
                "courses": [
                    {
                        "course_id": "CS 101",
                        "credits": 3,
                        "capacity": 20,
                        "room": ["Room 101"],
                        "lab": [],
                        "conflicts": [],
                        "faculty": ["Dr. Smith"],
                    },
                    {
                        "course_id": "CS 101",
                        "credits": 3,
                        "capacity": 20,
                        "room": ["Room 101"],
                        "lab": [],
                        "conflicts": [],
                        "faculty": ["Dr. Smith"],
                    },
                ],
                "faculty": [
                    {
                        "name": "Dr. Smith",
                        "maximum_credits": 12,
                        "minimum_credits": 0,
                        "unique_course_limit": 3,
                        "times": {
                            "MON": [{"start": "09:00", "end": "12:00"}],
                        },
                    }
                ],
            },
            "time_slot_config": {
                "times": {
                    day: [{"start": "09:00", "spacing": 30, "end": "12:00"}]
                    for day in weekdays
                },
                "classes": [
                    {
                        "credits": 3,
                        "meetings": [
                            {"day": "MON", "duration": 60, "lab": False},
                        ],
                    }
                ],
            },
        }
    )


def test_analysis_uses_config_for_unscheduled_and_availability_statistics():
    entry = ScheduleEntry(
        label="Generated schedule",
        config_name="test",
        source="generated",
        config=analysis_config(),
        records=[
            {
                "course": "CS 101.01",
                "faculty": "Dr. Smith",
                "room": "Room 101",
                "lab": "",
                "times": "MON 10:00-11:00",
            }
        ],
    )

    analysis = ScheduleAnalysisModel().analyze(entry)

    assert analysis is not None
    assert analysis.unscheduled_courses is not None
    assert [(course.course, course.section) for course in analysis.unscheduled_courses] == [
        ("CS 101", "02")
    ]
    assert analysis.available_empty_blocks == 2
    room = analysis.room_utilization[0]
    assert room.resource == "Room 101"
    assert room.available_hours == 2
    assert room.utilization_percent == 50
    assert room.unused_hours == 1
    lab = analysis.lab_utilization[0]
    assert lab.resource == "Lab A"
    assert lab.available_hours == 15
    assert lab.utilization_percent == 0
    assert lab.unused_hours == 15


def test_analysis_leaves_configuration_statistics_unavailable_for_uploaded_schedules():
    entry = ScheduleEntry(
        label="Uploaded schedule",
        config_name="test",
        source="file",
        records=[],
    )

    analysis = ScheduleAnalysisModel().analyze(entry)

    assert analysis is not None
    assert analysis.unscheduled_courses is None
    assert analysis.available_empty_blocks is None


def test_analysis_counts_early_starts_and_late_ends_per_meeting():
    entry = ScheduleEntry(
        label="Uploaded schedule",
        config_name="test",
        source="file",
        records=[
            {
                "course": "CS 101.01",
                "faculty": "Dr. Smith",
                "room": "Room 101",
                "lab": "",
                "times": (
                    "MON 08:59-09:00,TUE 16:00-17:01,"
                    "WED 09:00-17:00,THU 08:00-17:00"
                ),
            }
        ],
    )

    analysis = ScheduleAnalysisModel().analyze(entry)

    assert analysis is not None
    assert analysis.early_starts == 2
    assert analysis.late_ends == 1


def test_stats_outliers_config_generates_flagged_schedule():
    config = load_config("stats_outliers")
    schedule = next(Scheduler(config).get_models())
    result = ScheduleResult("stats_outliers", schedule, config)
    entry = ScheduleEntry(
        label="stats_outliers — schedule 1 (generated)",
        config_name="stats_outliers",
        source="generated",
        records=records_from_result(result),
        config=config,
        schedule=schedule,
    )

    analysis = ScheduleAnalysisModel().analyze(entry)

    assert analysis is not None
    assert analysis.scheduled_sections == 3
    assert analysis.early_starts == 1
    assert analysis.late_ends == 1
    assert analysis.unscheduled_courses == []
    assert analysis.available_empty_blocks == 3
    assert [resource.utilization_percent for resource in analysis.room_utilization] == [
        100,
        100,
        100,
    ]
    assert analysis.lab_utilization[0].utilization_percent == 0


def test_stats_outliers_partial_schedule_fixture_flags_missing_course():
    config = load_config("stats_outliers")
    fixture_path = Path(__file__).parent / "fixtures" / "stats_outliers_partial_schedule.csv"
    config_name, records = parse_schedule_file(
        fixture_path.name,
        fixture_path.read_bytes(),
    )
    entry = ScheduleEntry(
        label="stats_outliers_partial_schedule.csv (file)",
        config_name=config_name,
        source="file",
        records=records,
        config=config,
        file_name=fixture_path.name,
    )

    analysis = ScheduleAnalysisModel().analyze(entry)

    assert analysis is not None
    assert analysis.unscheduled_courses is not None
    assert [(course.course, course.section) for course in analysis.unscheduled_courses] == [
        ("Late Course", "01")
    ]
    assert analysis.early_starts == 1
    assert analysis.late_ends == 0
