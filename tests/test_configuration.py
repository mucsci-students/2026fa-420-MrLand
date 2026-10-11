# Unit tests for saving and loading scheduler configurations.

import json
import os

import pytest
from scheduler.config import CombinedConfig

from src.controllers.configuration_controller import ConfigurationController
from src.models import configuration_model as config_model
from src.models import configuration_repository as config_repo


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
    )


def break_config(config: CombinedConfig) -> None:
    """A mutation that makes a valid config invalid (no rooms; courses reference one)."""
    config.config.rooms.clear()


@pytest.fixture
def temp_config_dir(monkeypatch, tmp_path):
    monkeypatch.setattr(config_repo, "CONFIG_DIR", tmp_path)
    return tmp_path


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


def test_save_config_writes_json_file(temp_config_dir, valid_config):
    config_repo.save_config(valid_config, "demo config")

    saved_path = temp_config_dir / "demo config.json"
    assert saved_path.is_file()
    payload = json.loads(saved_path.read_text(encoding="utf-8"))
    assert payload == valid_config.model_dump(mode="json")


def test_save_config_strips_whitespace_from_name(temp_config_dir, valid_config):
    config_repo.save_config(valid_config, "  demo  ")
    assert (temp_config_dir / "demo.json").is_file()


def test_save_config_creates_missing_directory(monkeypatch, tmp_path, valid_config):
    missing_dir = tmp_path / "does" / "not" / "exist"
    monkeypatch.setattr(config_repo, "CONFIG_DIR", missing_dir)

    config_repo.save_config(valid_config, "demo")

    assert (missing_dir / "demo.json").is_file()


def test_save_config_overwrites_existing_file(temp_config_dir, valid_config):
    config_repo.save_config(valid_config, "demo")

    changed = make_valid_config()
    changed.limit = 99
    config_repo.save_config(changed, "demo")

    assert config_repo.load_config("demo").limit == 99


def test_save_config_leaves_no_temp_files(temp_config_dir, valid_config):
    config_repo.save_config(valid_config, "demo")
    assert [p.name for p in temp_config_dir.iterdir()] == ["demo.json"]


def test_save_config_failure_keeps_original_and_cleans_temp(
    temp_config_dir, valid_config, monkeypatch
):
    """The atomic write must not corrupt an existing config if the swap fails."""
    config_repo.save_config(valid_config, "demo")
    original_text = (temp_config_dir / "demo.json").read_text(encoding="utf-8")

    def failing_replace(src, dst):
        raise OSError("disk full")

    monkeypatch.setattr(config_repo.os, "replace", failing_replace)

    changed = make_valid_config()
    changed.limit = 99
    with pytest.raises(OSError):
        config_repo.save_config(changed, "demo")

    assert (temp_config_dir / "demo.json").read_text(encoding="utf-8") == original_text
    assert [p.name for p in temp_config_dir.iterdir()] == ["demo.json"]


def test_save_config_rejects_invalid_name_without_writing(temp_config_dir, valid_config):
    with pytest.raises(ValueError):
        config_repo.save_config(valid_config, "../escape")
    assert list(temp_config_dir.iterdir()) == []



def test_load_config_round_trips_saved_config(temp_config_dir, valid_config):
    config_repo.save_config(valid_config, "demo config")

    loaded = config_repo.load_config("demo config")

    assert isinstance(loaded, CombinedConfig)
    assert loaded.model_dump() == valid_config.model_dump()


def test_load_config_missing_file_raises_file_not_found(temp_config_dir):
    with pytest.raises(FileNotFoundError):
        config_repo.load_config("missing config")


def test_load_config_malformed_json_raises_config_load_error(temp_config_dir):
    (temp_config_dir / "broken.json").write_text("{not valid json}", encoding="utf-8")
    with pytest.raises(config_repo.ConfigLoadError):
        config_repo.load_config("broken")


def test_load_config_schema_invalid_json_raises_config_load_error(temp_config_dir):
    """Well-formed JSON that fails CombinedConfig validation."""
    (temp_config_dir / "wrong_shape.json").write_text("{}", encoding="utf-8")
    with pytest.raises(config_repo.ConfigLoadError):
        config_repo.load_config("wrong_shape")


def test_load_config_rejects_invalid_name(temp_config_dir):
    with pytest.raises(ValueError):
        config_repo.load_config("../escape")

def test_config_exists_false_then_true(temp_config_dir, valid_config):
    assert config_repo.config_exists("demo") is False
    config_repo.save_config(valid_config, "demo")
    assert config_repo.config_exists("demo") is True


def test_config_exists_rejects_invalid_name(temp_config_dir):
    with pytest.raises(ValueError):
        config_repo.config_exists("a/b")


def test_list_configs_empty_when_directory_missing(monkeypatch, tmp_path):
    monkeypatch.setattr(config_repo, "CONFIG_DIR", tmp_path / "nope")
    assert config_repo.list_configs() == []


def test_list_configs_empty_directory(temp_config_dir):
    assert config_repo.list_configs() == []


def test_list_configs_returns_sorted_stems_and_ignores_other_files(
    temp_config_dir, valid_config
):
    for name in ("zebra", "alpha", "middle"):
        config_repo.save_config(valid_config, name)
    (temp_config_dir / "notes.txt").write_text("ignore me", encoding="utf-8")
    (temp_config_dir / "stray.tmp").write_text("ignore me", encoding="utf-8")

    assert config_repo.list_configs() == ["alpha", "middle", "zebra"]

def test_validate_config_name_accepts_new_name(temp_config_dir):
    assert config_model.validate_config_name("  fresh  ") == "fresh"


def test_validate_config_name_rejects_existing_name(temp_config_dir, valid_config):
    config_repo.save_config(valid_config, "taken")
    with pytest.raises(ValueError, match="already exists"):
        config_model.validate_config_name("taken")


def test_validate_config_name_rejects_invalid_name(temp_config_dir):
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
        (("config", "rooms"), None),                 # whole-area error
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
def test_describe_maps_location_to_area_and_item(
    valid_config, loc, expected_area, expected_item
):
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


def test_config_service_save_load_round_trip(temp_config_dir, valid_config):
    service = config_model.ConfigService()
    service.save(valid_config, "demo")

    loaded = service.load("demo")

    assert loaded.model_dump() == valid_config.model_dump()


def test_config_service_save_cleans_name(temp_config_dir, valid_config):
    config_model.ConfigService().save(valid_config, "  demo  ")
    assert (temp_config_dir / "demo.json").is_file()


def test_config_service_save_rejects_invalid_name(temp_config_dir, valid_config):
    with pytest.raises(ValueError):
        config_model.ConfigService().save(valid_config, "../escape")
    assert list(temp_config_dir.iterdir()) == []


def test_config_service_exists_and_list_names(temp_config_dir, valid_config):
    service = config_model.ConfigService()
    assert service.exists("demo") is False
    assert service.list_names() == []

    service.save(valid_config, "demo")
    service.save(valid_config, "another")

    assert service.exists("demo") is True
    assert service.list_names() == ["another", "demo"]


def test_config_service_load_missing_raises(temp_config_dir):
    with pytest.raises(FileNotFoundError):
        config_model.ConfigService().load("nope")


@pytest.fixture
def controller(temp_config_dir) -> ConfigurationController:
    return ConfigurationController()


def test_controller_new_configuration_returns_draft(controller):
    config = controller.new_configuration()

    assert controller.configuration is config
    assert config.config.courses == []


def test_controller_save_without_config_raises(controller):
    with pytest.raises(ValueError):
        controller.save_configuration("demo")


def test_controller_save_invalid_draft_raises_and_writes_nothing(
    controller, temp_config_dir
):
    controller.new_configuration()

    with pytest.raises(config_model.ConfigValidationError) as exc_info:
        controller.save_configuration("demo")

    assert exc_info.value.problems
    assert list(temp_config_dir.iterdir()) == []


def test_controller_save_valid_config_writes_file(
    controller, temp_config_dir, valid_config
):
    controller.configuration = valid_config

    controller.save_configuration("demo")

    assert (temp_config_dir / "demo.json").is_file()


def test_controller_save_load_round_trip(controller, temp_config_dir, valid_config):
    controller.configuration = valid_config
    controller.save_configuration("demo")

    other = ConfigurationController()
    loaded = other.load_configuration("demo")

    assert other.configuration is loaded
    assert loaded.model_dump() == valid_config.model_dump()


def test_controller_load_missing_raises(controller):
    with pytest.raises(FileNotFoundError):
        controller.load_configuration("nope")


def test_controller_load_invalid_file_raises_config_load_error(
    controller, temp_config_dir
):
    (temp_config_dir / "broken.json").write_text("{nope", encoding="utf-8")
    with pytest.raises(config_repo.ConfigLoadError):
        controller.load_configuration("broken")


def test_controller_list_names(controller, temp_config_dir, valid_config):
    controller.configuration = valid_config
    controller.save_configuration("beta")
    controller.save_configuration("alpha")

    assert controller.list_names() == ["alpha", "beta"]


def test_controller_validate_without_config_raises(controller):
    with pytest.raises(ValueError):
        controller.validate_configuration()


def test_controller_validate_reports_draft_problems(controller):
    controller.new_configuration()
    assert controller.validate_configuration()


def test_controller_apply_change_without_config_raises(controller):
    with pytest.raises(ValueError):
        controller.apply_change(lambda: None)


def test_controller_loaded_config_rolls_back_invalid_change(
    controller, temp_config_dir, valid_config
):
    controller.configuration = valid_config
    controller.save_configuration("demo")

    other = ConfigurationController()
    loaded = other.load_configuration("demo")

    accepted, problems = other.apply_change(lambda: break_config(loaded))

    assert accepted is False
    assert problems
    assert len(other.configuration.config.rooms) == 1


def test_controller_valid_change_is_accepted_and_sets_baseline(controller, valid_config):
    controller.configuration = valid_config

    accepted, problems = controller.apply_change(lambda: setattr(valid_config, "limit", 25))

    assert accepted is True
    assert problems == []
    assert controller._has_valid_configuration is True


def test_controller_new_configuration_resets_valid_baseline(
    controller, temp_config_dir, valid_config
):
    controller.configuration = valid_config
    controller.save_configuration("demo")
    controller.load_configuration("demo")  # baseline now True

    draft = controller.new_configuration()  # baseline should reset

    accepted, problems = controller.apply_change(lambda: draft.config.rooms.clear())

    assert accepted is True   # drafts may stay incomplete
    assert problems           # ...but problems are still reported


def test_controller_full_flow_create_edit_save_load(controller, temp_config_dir):
    """Draft -> fill in with a valid config -> save -> reload in a new controller."""
    controller.new_configuration()
    assert controller.validate_configuration()  # draft is invalid

    expected = make_valid_config()
    controller.configuration = expected
    assert controller.validate_configuration() == []

    controller.save_configuration("flow")

    reloaded = ConfigurationController().load_configuration("flow")
    assert reloaded.model_dump() == expected.model_dump()
    assert os.path.isfile(temp_config_dir / "flow.json")