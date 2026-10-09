import json

import pytest
from scheduler.config import CombinedConfig

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


@pytest.fixture
def temp_config_dir(monkeypatch, tmp_path):
    monkeypatch.setattr(config_repo, "CONFIG_DIR", tmp_path)
    return tmp_path


def test_save_config_writes_json_file(temp_config_dir):
    config = make_valid_config()

    config_repo.save_config(config, "demo config")

    saved_path = temp_config_dir / "demo config.json"
    assert saved_path.is_file()
    payload = json.loads(saved_path.read_text(encoding="utf-8"))
    assert payload == config.model_dump(mode="json")


def test_load_config_round_trips_saved_config(temp_config_dir):
    config = make_valid_config()
    config_repo.save_config(config, "demo config")

    loaded = config_repo.load_config("demo config")

    assert isinstance(loaded, CombinedConfig)
    assert loaded.model_dump() == config.model_dump()


@pytest.mark.parametrize(
    "config_name, expected_exception",
    [
        ("missing config", FileNotFoundError),
        ("broken config", config_repo.ConfigLoadError),
    ],
)
def test_load_config_rejects_missing_or_invalid_files(temp_config_dir, config_name, expected_exception):
    if expected_exception is config_repo.ConfigLoadError:
        broken_path = temp_config_dir / f"{config_name}.json"
        broken_path.write_text("{not valid json}", encoding="utf-8")

    with pytest.raises(expected_exception):
        config_repo.load_config(config_name)
