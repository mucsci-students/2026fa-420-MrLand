# Unit tests for saving and loading scheduler configurations.

import json

import pytest
from scheduler.config import CombinedConfig

from src.controllers.configuration_controller import ConfigurationController
from src.models import configuration_model as config_model
from src.models import configuration_repository as config_repo
from src.models.quality_grading import QualityGradeSettings


def make_valid_config() -> CombinedConfig:
    return CombinedConfig.model_validate(
        {
            "config": {
                "rooms": [{"name": "Room 101", "capacity": 30, "features": [], "times": None}],
                "labs": [{"name": "Lab 1", "capacity": 20, "features": [], "times": None}],
                "courses": [
                    {
                        "course_id": "CS 121",
                        "section_id": None,
                        "credits": 4,
                        "capacity": 25,
                        "room": ["Room 101"],
                        "lab": ["Lab 1"],
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
                        "times": {
                            "MON": [{"start": "09:00", "end": "12:00"}],
                            "TUE": [{"start": "09:00", "end": "12:00"}],
                            "WED": [{"start": "09:00", "end": "12:00"}],
                            "THU": [{"start": "09:00", "end": "12:00"}],
                            "FRI": [{"start": "09:00", "end": "12:00"}],
                        },
                        "course_preferences": {},
                        "room_preferences": {},
                        "lab_preferences": {},
                        "mandatory_days": ["MON", "WED", "FRI"],
                    }
                ],
            },
            "time_slot_config": {
                "times": {
                    "MON": [{"start": "10:00", "spacing": 60, "end": "11:00"}],
                    "TUE": [{"start": "10:00", "spacing": 60, "end": "11:00"}],
                    "WED": [{"start": "10:00", "spacing": 60, "end": "11:00"}],
                    "THU": [{"start": "10:00", "spacing": 60, "end": "11:00"}],
                    "FRI": [{"start": "10:00", "spacing": 60, "end": "11:00"}],
                },
                "classes": [
                    {
                        "credits": 4,
                        "meetings": [
                            {
                                "day": "MON",
                                "start_time": None,
                                "duration": 60,
                                "lab": False,
                                "delivery": "in_person",
                            },
                            {
                                "day": "WED",
                                "start_time": None,
                                "duration": 60,
                                "lab": True,
                                "delivery": "in_person",
                            },
                            {
                                "day": "FRI",
                                "start_time": None,
                                "duration": 60,
                                "lab": False,
                                "delivery": "in_person",
                            },
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
    )


def break_config(config: CombinedConfig) -> None:
    """A mutation that makes a valid config invalid (no rooms; courses reference one)."""
    config.config.rooms.clear()


@pytest.fixture
def valid_config() -> CombinedConfig:
    return make_valid_config()


def test_sample_config_is_valid(valid_config):
    """If this fails, fix make_valid_config() before looking at other failures."""
    assert config_model.validate_config(valid_config) == []


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("demo", "demo"),
        ("  demo  ", "demo"),
        ("demo config", "demo config"),
        ("fall_2026", "fall_2026"),
        ("A-1", "A-1"),
        ("a" * 64, "a" * 64),
    ],
)
def test_clean_config_name_accepts_valid_names(raw, expected):
    assert config_repo.clean_config_name(raw) == expected


@pytest.mark.parametrize(
    "bad_name",
    [
        "",
        "   ",
        "../evil",
        "a/b",
        "a\\b",
        "-leading-hyphen",
        "_leading_underscore",
        "bad!name",
        "dot.name",
        "a" * 65,
    ],
)
def test_clean_config_name_rejects_invalid_names(bad_name):
    with pytest.raises(ValueError):
        config_repo.clean_config_name(bad_name)


def test_validate_config_name_cleans_name():
    assert config_model.validate_config_name("  fresh  ") == "fresh"


def test_validate_config_name_allows_browser_managed_duplicate_names():
    assert config_model.validate_config_name("taken") == "taken"
    assert config_model.validate_config_name("taken") == "taken"


def test_validate_config_name_rejects_invalid_name():
    with pytest.raises(ValueError):
        config_model.validate_config_name("bad!name")


def test_create_draft_config_is_empty_with_defaults():
    draft = config_model.create_draft_config()

    assert draft.config.rooms == []
    assert draft.config.labs == []
    assert draft.config.courses == []
    assert draft.config.faculty == []
    assert draft.time_slot_config.times == {}
    assert draft.time_slot_config.classes == []
    assert draft.limit == 10
    assert draft.optimizer_flags == []


def test_validate_config_returns_no_problems_for_valid_config(valid_config):
    assert config_model.validate_config(valid_config) == []


def test_validate_config_reports_problems_for_empty_draft():
    problems = config_model.validate_config(config_model.create_draft_config())

    assert problems
    assert all(isinstance(p, config_model.ValidationProblem) for p in problems)
    assert all(p.message for p in problems)


def test_validate_config_reports_problems_for_broken_config(valid_config):
    break_config(valid_config)
    assert config_model.validate_config(valid_config)


def test_validate_config_does_not_modify_config(valid_config):
    before = valid_config.model_dump()
    config_model.validate_config(valid_config)
    assert valid_config.model_dump() == before


@pytest.mark.parametrize(
    "loc, expected",
    [
        (("config", "courses", 0, "capacity"), "CS 121"),
        (("config", "rooms", 0, "capacity"), "Room 101"),
        (("config", "labs", 0, "name"), "Lab 1"),
        (("config", "faculty", 0, "minimum_credits"), "Dr. Adrian"),
        (("time_slot_config", "times", "MON"), "MON"),
        (("time_slot_config", "classes", 0, "meetings"), "4-credit pattern"),
        (("config", "rooms", 5, "capacity"), "#6"),  # out-of-range index
        (("config", "rooms"), None),  # whole-area error
    ],
)
def test_item_label(valid_config, loc, expected):
    assert config_model._item_label(valid_config, loc) == expected


def test_item_label_includes_section_id(valid_config):
    valid_config.config.courses[0].section_id = "01"
    label = config_model._item_label(valid_config, ("config", "courses", 0, "capacity"))
    assert label == "CS 121 01"


@pytest.mark.parametrize(
    "loc, expected_area, expected_item",
    [
        (("config", "rooms"), "Rooms", None),
        (("config", "courses", 0, "capacity"), "Courses", "CS 121"),
        (("time_slot_config", "classes", 0), "Class patterns", "4-credit pattern"),
        (("limit",), "Global settings", None),
        (("optimizer_flags",), "Global settings", None),
        (("time_slot_config",), "Time slots", None),
        (("config",), "Configuration data", None),
        ((), "Whole configuration", None),
    ],
)
def test_describe_maps_location_to_area_and_item(valid_config, loc, expected_area, expected_item):
    area, item, _field = config_model._describe(valid_config, loc)
    assert area == expected_area
    assert item == expected_item


def test_describe_formats_field_name(valid_config):
    _area, _item, field = config_model._describe(
        valid_config, ("config", "courses", 0, "required_room_features", 0)
    )
    assert field == "required room features"  # underscores -> spaces, indexes dropped


def test_apply_change_accepts_valid_edit(valid_config):
    def mutation():
        valid_config.limit = 20
        return "done"

    accepted, problems, result = config_model.apply_configuration_change(
        valid_config, mutation, has_valid_baseline=True
    )

    assert accepted is True
    assert problems == []
    assert result == "done"
    assert valid_config.limit == 20


def test_apply_change_rolls_back_invalid_edit_with_valid_baseline(valid_config):
    before = valid_config.model_dump()

    accepted, problems, result = config_model.apply_configuration_change(
        valid_config, lambda: break_config(valid_config), has_valid_baseline=True
    )

    assert accepted is False
    assert problems
    assert result is None
    assert valid_config.model_dump() == before
    assert len(valid_config.config.rooms) == 1


def test_apply_change_keeps_invalid_edit_without_valid_baseline(valid_config):
    accepted, problems, _result = config_model.apply_configuration_change(
        valid_config, lambda: break_config(valid_config), has_valid_baseline=False
    )

    assert accepted is True
    assert problems
    assert valid_config.config.rooms == []


def test_apply_change_restores_config_and_reraises_on_exception(valid_config):
    before = valid_config.model_dump()

    def exploding_mutation():
        valid_config.limit = 99
        raise RuntimeError("boom")

    with pytest.raises(RuntimeError, match="boom"):
        config_model.apply_configuration_change(
            valid_config, exploding_mutation, has_valid_baseline=True
        )

    assert valid_config.model_dump() == before


def test_config_service_loads_uploaded_json(valid_config):
    service = config_model.ConfigService()

    loaded = service.load_uploaded(json.dumps(valid_config.model_dump(mode="json")).encode("utf-8"))

    assert loaded.model_dump() == valid_config.model_dump()


@pytest.fixture
def controller() -> ConfigurationController:
    return ConfigurationController()


def test_controller_new_configuration_returns_draft(controller):
    config = controller.new_configuration()

    assert controller.configuration is config
    assert config.config.courses == []


def test_controller_memento_restores_an_independent_configuration(controller, valid_config):
    controller.configuration = valid_config
    controller._has_valid_configuration = True
    memento = controller.create_memento()

    valid_config.limit = 25
    controller._has_valid_configuration = False
    controller.restore_memento(memento)

    assert controller.configuration.limit == 10
    assert controller.configuration is not valid_config
    assert controller._has_valid_configuration is True

    controller.configuration.limit = 30
    controller.restore_memento(memento)
    assert controller.configuration.limit == 10


def test_controller_export_configuration_returns_browser_download_data(controller, valid_config):
    controller.configuration = valid_config

    content, file_name, media_type = controller.export_configuration("demo")

    assert file_name == "demo.json"
    assert media_type == "application/json"
    assert json.loads(content) == valid_config.model_dump(mode="json")


def test_controller_keeps_uploaded_quality_targets_and_embeds_them_in_download(
    controller, valid_config
):
    settings = QualityGradeSettings(max_faculty_gap_minutes=420)
    controller.configuration = valid_config
    controller.set_quality_grade_settings("demo", settings)
    content, _, _ = controller.export_configuration("demo")

    loaded = ConfigurationController()
    loaded.load_uploaded_configuration(content, config_name="demo")
    assert loaded.quality_grade_settings == settings
    assert json.loads(content)["quality_grade_settings"] == settings.model_dump(mode="json")

    other = ConfigurationController()
    other.load_uploaded_configuration(
        json.dumps(valid_config.model_dump(mode="json")).encode("utf-8"),
        config_name="other",
    )
    assert other.quality_grade_settings == QualityGradeSettings()


def test_controller_upload_preserves_custom_quality_targets_for_dotted_name(
    controller, valid_config
):
    document = valid_config.model_dump(mode="json")
    document["quality_grade_settings"] = {"max_faculty_gap_minutes": 420}

    loaded = controller.load_uploaded_configuration(
        json.dumps(document).encode(),
        config_name="plan.final",
    )

    assert loaded == valid_config
    assert controller.quality_grade_settings.max_faculty_gap_minutes == 420


def test_controller_export_configuration_requires_open_valid_config(controller):
    with pytest.raises(ValueError, match="No configuration"):
        controller.export_configuration("demo.json")

    controller.new_configuration()
    with pytest.raises(config_model.ConfigValidationError):
        controller.export_configuration("demo.json")


def test_controller_validate_without_config_raises(controller):
    with pytest.raises(ValueError):
        controller.validate_configuration()


def test_controller_validate_reports_draft_problems(controller):
    controller.new_configuration()
    assert controller.validate_configuration()


def test_controller_apply_change_without_config_raises(controller):
    with pytest.raises(ValueError):
        controller.apply_change(lambda: None)


def test_controller_uploaded_config_rolls_back_invalid_change(controller, valid_config):
    loaded = controller.load_uploaded_configuration(
        json.dumps(valid_config.model_dump(mode="json")).encode("utf-8"),
        config_name="demo",
    )

    accepted, problems = controller.apply_change(lambda: break_config(loaded))

    assert accepted is False
    assert problems
    assert len(loaded.config.rooms) == 1


def test_controller_valid_change_is_accepted_and_sets_baseline(controller, valid_config):
    controller.configuration = valid_config

    accepted, problems = controller.apply_change(lambda: setattr(valid_config, "limit", 25))

    assert accepted is True
    assert problems == []
    assert controller._has_valid_configuration is True


def test_controller_rename_updates_relationships_in_transaction(controller, valid_config):
    controller.configuration = valid_config
    before = valid_config.model_copy(deep=True)

    accepted, problems = controller.apply_change(
        lambda: setattr(valid_config.config.faculty[0], "name", "Dr. Jones")
    )

    assert accepted
    assert problems == []
    assert valid_config.config.courses[0].faculty == ["Dr. Jones"]
    assert before.config.courses[0].faculty == ["Dr. Adrian"]


def test_controller_switches_configuration_when_previous_observer_was_removed(
    controller, valid_config
):
    controller.configuration = valid_config
    controller.apply_change(lambda: None)
    observer = controller._relationship_observer
    assert observer is not None
    controller._change_subject.unsubscribe(observer)

    replacement = make_valid_config()
    controller.configuration = replacement
    accepted, problems = controller.apply_change(
        lambda: setattr(replacement.config.faculty[0], "name", "Dr. Jones")
    )

    assert accepted
    assert problems == []
    assert replacement.config.courses[0].faculty == ["Dr. Jones"]


def test_controller_observer_failure_rolls_back_entity_and_relationship_changes(
    controller, valid_config
):
    controller.configuration = valid_config
    faculty = valid_config.config.faculty[0]
    faculty.course_preferences = {"CS 121": 6, "CS 222": 8}
    before = valid_config.model_copy(deep=True)

    with pytest.raises(ValueError, match="preference conflicts"):
        controller.apply_change(
            lambda: setattr(valid_config.config.courses[0], "course_id", "CS 222")
        )

    assert valid_config.model_dump() == before.model_dump()


def test_controller_new_configuration_resets_valid_baseline(controller, valid_config):
    controller.load_uploaded_configuration(
        json.dumps(valid_config.model_dump(mode="json")).encode("utf-8"),
        config_name="demo",
    )

    draft = controller.new_configuration()  # baseline should reset

    accepted, problems = controller.apply_change(lambda: draft.config.rooms.clear())

    assert accepted is True  # drafts may stay incomplete
    assert problems  # ...but problems are still reported


def test_controller_full_flow_create_edit_download_upload(controller):
    """Draft -> fill in with a valid config -> download -> upload."""
    controller.new_configuration()
    assert controller.validate_configuration()  # draft is invalid

    expected = make_valid_config()
    controller.configuration = expected
    assert controller.validate_configuration() == []

    content, file_name, media_type = controller.export_configuration("flow")

    reloaded_controller = ConfigurationController()
    reloaded = reloaded_controller.load_uploaded_configuration(content, config_name="flow")
    assert file_name == "flow.json"
    assert media_type == "application/json"
    assert reloaded.model_dump() == expected.model_dump()
