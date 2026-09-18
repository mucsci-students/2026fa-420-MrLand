"""Quick smoke tests for src/config_io.py (save/load/exists/print)."""

import os
import sys

# Make src/ importable regardless of where this script is run from.
_TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
_SRC_DIR = os.path.normpath(os.path.join(_TESTS_DIR, "..", "src"))
if _SRC_DIR not in sys.path:
    sys.path.insert(0, _SRC_DIR)

from config_io import config_exists, config_load, config_print, config_save, filepath
from scheduler.config import CombinedConfig

TEST_CONFIG_NAME = "test_config"

# Minimal valid CombinedConfig: one room, one course (no lab, in-person),
# one faculty member, and a single enabled 3-credit class pattern with
# no lab meeting (matching the course's lab-less requirement).
SAMPLE_CONFIG = CombinedConfig.model_validate(
    {
        "config": {
            "rooms": [{"name": "Room 101", "capacity": 40}],
            "labs": [],
            "courses": [
                {
                    "course_id": "CS 101",
                    "credits": 3,
                    "capacity": 24,
                    "room": ["Room 101"],
                    "lab": [],
                    "conflicts": [],
                    "faculty": ["Dr. Smith"],
                }
            ],
            "faculty": [
                {
                    "name": "Dr. Smith",
                    "maximum_credits": 12,
                    "minimum_credits": 3,
                    "unique_course_limit": 3,
                    "times": {"MON": ["09:00-12:00"], "TUE": ["09:00-12:00"]},
                    "course_preferences": {"CS 101": 5},
                }
            ],
        },
        "time_slot_config": {
            "times": {
                "MON": [{"start": "09:00", "spacing": 60, "end": "12:00"}],
                "TUE": [{"start": "09:00", "spacing": 60, "end": "12:00"}],
                "WED": [{"start": "09:00", "spacing": 60, "end": "12:00"}],
                "THU": [{"start": "09:00", "spacing": 60, "end": "12:00"}],
                "FRI": [{"start": "09:00", "spacing": 60, "end": "12:00"}],
            },
            "classes": [
                {"credits": 3, "meetings": [{"day": "MON", "duration": 150, "lab": False}]}
            ],
        },
        "limit": 5,
    }
)


def _test_file_path():
    return os.path.join(filepath, f"{TEST_CONFIG_NAME}.json")


def reset_test_file():
    """Remove only this test's file (if left over from a prior run), not the whole dir."""
    test_file = _test_file_path()
    if os.path.isfile(test_file):
        os.remove(test_file)


def test_does_not_exist_before_save():
    reset_test_file()
    assert not config_exists(TEST_CONFIG_NAME), "Config should not exist before saving"
    print("PASS: config_exists is False before save")


def test_save_creates_file():
    config_save(SAMPLE_CONFIG, TEST_CONFIG_NAME)
    expected_path = _test_file_path()
    assert os.path.isfile(expected_path), f"Expected file at {expected_path}"
    print(f"PASS: config_save wrote a file to {expected_path}")


def test_exists_after_save():
    assert config_exists(TEST_CONFIG_NAME), "Config should exist after saving"
    print("PASS: config_exists is True after save")


def test_load_round_trip():
    loaded = config_load(TEST_CONFIG_NAME)
    assert isinstance(loaded, CombinedConfig), "Loaded object should be a CombinedConfig"
    assert loaded.model_dump() == SAMPLE_CONFIG.model_dump(), "Loaded config should match saved config"
    print("PASS: config_load round-trips to an equal CombinedConfig")


def test_load_missing_raises():
    try:
        config_load("does_not_exist_xyz")
    except FileNotFoundError:
        print("PASS: config_load raises FileNotFoundError for missing config")
    else:
        raise AssertionError("Expected FileNotFoundError for missing config")


def test_print_smoke():
    # Just confirm it runs without raising.
    config_print(SAMPLE_CONFIG)
    print("PASS: config_print ran without error")


if __name__ == "__main__":
    tests = [
        test_does_not_exist_before_save,
        test_save_creates_file,
        test_exists_after_save,
        test_load_round_trip,
        test_load_missing_raises,
        test_print_smoke,
    ]

    for test in tests:
        test()

    print(f"\nAll tests passed. Written config left at: {_test_file_path()}")