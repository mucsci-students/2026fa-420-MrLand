import copy

from scheduler.config import CombinedConfig, SchedulerConfig, TimeSlotConfig

from src.models.configuration_model import (
    ValidationProblem,
    apply_configuration_change,
    validate_config,
)

WEEKDAYS = ("MON", "TUE", "WED", "THU", "FRI")

VALID_CONFIG = {
    "config": {
        "rooms": [{"name": "Room", "capacity": 30, "features": [], "times": None}],
        "labs": [{"name": "Lab", "capacity": 30, "features": [], "times": None}],
        "courses": [
            {
                "course_id": "CS 121",
                "section_id": None,
                "credits": 4,
                "capacity": 25,
                "room": ["Room"],
                "lab": ["Lab"],
                "conflicts": [],
                "faculty": ["Dr. Adrian"],
                "modality": "in_person",
                "required_room_features": [],
                "required_lab_features": [],
                "reserve_room_during_lab": False,
            }
        ],
        "faculty": [
            {
                "name": "Dr. Adrian",
                "maximum_credits": 8,
                "maximum_days": 4,
                "minimum_credits": 1,
                "unique_course_limit": 2,
                "times": {day: [{"start": "01:00", "end": "14:00"}] for day in WEEKDAYS},
                "course_preferences": {},
                "room_preferences": {},
                "lab_preferences": {},
                "mandatory_days": ["MON", "WED", "FRI"],
            }
        ],
    },
    "time_slot_config": {
        "times": {
            day: [{"start": "10:00", "spacing": 60, "end": "11:00"}] for day in WEEKDAYS
        },
        "classes": [
            {
                "credits": 4,
                "meetings": [
                    {"day": "MON", "start_time": None, "duration": 60, "lab": False, "delivery": "in_person"},
                    {"day": "WED", "start_time": None, "duration": 60, "lab": True, "delivery": "in_person"},
                    {"day": "FRI", "start_time": None, "duration": 60, "lab": False, "delivery": "in_person"},
                ],
                "disabled": False,
                "start_time": None,
            }
        ],
        "max_time_gap": 30,
        "min_time_overlap": 45,
    },
    "limit": 10,
    "optimizer_flags": [],
}


def make_config() -> CombinedConfig:
    return CombinedConfig.model_validate(copy.deepcopy(VALID_CONFIG))


def empty_draft() -> CombinedConfig:
    """An empty draft, built the same way the editor's Create button builds one."""
    return CombinedConfig.model_construct(
        config=SchedulerConfig.model_construct(rooms=[], labs=[], courses=[], faculty=[]),
        time_slot_config=TimeSlotConfig.model_construct(times={}, classes=[]),
        limit=10,
        optimizer_flags=[],
    )


def test_complete_config_has_no_problems():
    assert validate_config(make_config()) == []


def test_empty_draft_reports_missing_sections():
    areas = {problem.area for problem in validate_config(empty_draft())}
    assert {"Rooms", "Courses", "Faculty", "Time blocks", "Class patterns"} <= areas


def test_empty_list_message_is_readable():
    messages = [problem.message for problem in validate_config(empty_draft())]
    assert not any("after validation" in message for message in messages)


def test_only_disabled_class_patterns_is_a_problem():
    config = make_config()
    # Disable the only pattern in place, the way the GUI edits the config.
    pattern = config.time_slot_config.classes[0]
    config.time_slot_config.classes[0] = pattern.model_copy(update={"disabled": True})
    problems = validate_config(config)
    assert any(problem.area == "Class patterns" for problem in problems)


def test_broken_reference_is_reported():
    config = make_config()
    # Point the course at a room that doesn't exist, the way an in-place GUI edit could.
    config.config.courses[0].room.append("Ghost Room")
    problems = validate_config(config)
    assert problems, "a course referencing a missing room should not validate"
    assert all(isinstance(problem, ValidationProblem) for problem in problems)


def test_validation_does_not_change_the_config():
    config = make_config()
    config.config.courses[0].room.append("Ghost Room")
    before = config.model_dump_json()
    validate_config(config)
    assert config.model_dump_json() == before


def test_validation_checks_the_published_json_schema():
    valid = make_config()
    invalid = CombinedConfig.model_construct(
        config=valid.config,
        time_slot_config=valid.time_slot_config,
        limit="ten",
        optimizer_flags=[],
    )

    problems = validate_config(invalid)

    assert any(problem.area == "Global settings" for problem in problems)
    assert any("limit" in problem.message.lower() for problem in problems)


def test_invalid_change_restores_a_valid_configuration():
    config = make_config()

    accepted, problems, result = apply_configuration_change(
        config,
        lambda: config.config.courses[0].room.append("Ghost Room"),
        has_valid_baseline=True,
    )

    assert not accepted
    assert problems
    assert result is None
    assert config.config.courses[0].room == ["Room"]


def test_incomplete_draft_can_be_edited_before_it_is_valid():
    config = empty_draft()

    accepted, problems, _ = apply_configuration_change(
        config,
        lambda: config.config.rooms.append({}),
        has_valid_baseline=False,
    )

    assert accepted
    assert problems
    assert config.config.rooms == [{}]