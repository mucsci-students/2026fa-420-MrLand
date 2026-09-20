import unittest
from unittest.mock import patch

from scheduler.config import (
    CombinedConfig,
    OptimizerFlags,
)

from services.settings_service import (
    view_settings,
    modify_settings,
    reset_settings,
)


class TestGlobalSettingsCRUD(unittest.TestCase):

    def setUp(self):
        self.config = CombinedConfig(
            config={
                "rooms": [
                    {
                        "name": "Room 101",
                        "capacity": 30,
                    }
                ],
                "labs": [],
                "courses": [
                    {
                        "course_id": "CS 101",
                        "credits": 3,
                        "capacity": 20,
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
                        "times": {
                            "MON": ["09:00-17:00"],
                        },
                        "course_preferences": {
                            "CS 101": 5,
                        },
                    }
                ],
            },
            time_slot_config={
                "times": {
                    "MON": [
                        {
                            "start": "09:00",
                            "spacing": 60,
                            "end": "17:00",
                        }
                    ],
                    "TUE": [
                        {
                            "start": "09:00",
                            "spacing": 60,
                            "end": "17:00",
                        }
                    ],
                    "WED": [
                        {
                            "start": "09:00",
                            "spacing": 60,
                            "end": "17:00",
                        }
                    ],
                    "THU": [
                        {
                            "start": "09:00",
                            "spacing": 60,
                            "end": "17:00",
                        }
                    ],
                    "FRI": [
                        {
                            "start": "09:00",
                            "spacing": 60,
                            "end": "17:00",
                        }
                    ],
                },
                "classes": [
                    {
                        "credits": 3,
                        "meetings": [
                            {
                                "day": "MON",
                                "duration": 60,
                            }
                        ],
                    }
                ],
            },
        )

    # -------------------------
    # CREATE
    # -------------------------

    def test_create_default_settings(self):
        self.assertEqual(self.config.limit, 10)
        self.assertEqual(self.config.optimizer_flags, [])

    def test_create_settings_with_values(self):
        config = self.config.model_copy(
            update={
                "limit": 20,
                "optimizer_flags": [
                    OptimizerFlags.FACULTY_COURSE,
                    OptimizerFlags.PACK_ROOMS,
                ],
            }
        )

        self.assertEqual(config.limit, 20)
        self.assertEqual(
            config.optimizer_flags,
            [
                OptimizerFlags.FACULTY_COURSE,
                OptimizerFlags.PACK_ROOMS,
            ],
        )

    # -------------------------
    # READ
    # -------------------------

    @patch("builtins.print")
    def test_view_settings(self, mock_print):
        view_settings(self.config)

        output = "\n".join(
            str(call.args[0])
            for call in mock_print.call_args_list
            if call.args
        )

        self.assertIn("GLOBAL SETTINGS", output)
        self.assertIn("Generation limit: 10", output)
        self.assertIn("Optimizer flags: None", output)

    @patch("builtins.print")
    def test_view_settings_with_optimizer_flags(self, mock_print):
        self.config.optimizer_flags = [
            OptimizerFlags.FACULTY_COURSE,
            OptimizerFlags.PACK_ROOMS,
        ]

        view_settings(self.config)

        output = "\n".join(
            str(call.args[0])
            for call in mock_print.call_args_list
            if call.args
        )

        self.assertIn("faculty_course", output)
        self.assertIn("pack_rooms", output)

    # -------------------------
    # UPDATE
    # -------------------------

    @patch(
        "builtins.input",
        side_effect=[
            "25",
            "faculty_course, pack_rooms",
        ],
    )
    def test_modify_settings(self, mock_input):
        modify_settings(self.config)

        self.assertEqual(self.config.limit, 25)

        self.assertEqual(
            self.config.optimizer_flags,
            [
                OptimizerFlags.FACULTY_COURSE,
                OptimizerFlags.PACK_ROOMS,
            ],
        )

    @patch(
        "builtins.input",
        side_effect=[
            "15",
            "",
        ],
    )
    def test_modify_settings_without_optimizer_flags(self, mock_input):
        modify_settings(self.config)

        self.assertEqual(self.config.limit, 15)
        self.assertEqual(self.config.optimizer_flags, [])

    @patch(
        "builtins.input",
        side_effect=[
            "20",
            "not_a_real_flag",
        ],
    )
    def test_modify_settings_invalid_optimizer_flag(self, mock_input):
        original_limit = self.config.limit
        original_flags = self.config.optimizer_flags.copy()

        modify_settings(self.config)

        self.assertEqual(self.config.limit, original_limit)
        self.assertEqual(self.config.optimizer_flags, original_flags)

    # -------------------------
    # RESET
    # -------------------------

    def test_reset_settings(self):
        self.config.limit = 25
        self.config.optimizer_flags = [
            OptimizerFlags.FACULTY_COURSE,
            OptimizerFlags.SAME_ROOM,
        ]

        reset_settings(self.config)

        self.assertEqual(self.config.limit, 10)
        self.assertEqual(self.config.optimizer_flags, [])

    # -------------------------
    # VALIDATION
    # -------------------------

    def test_generation_limit_must_be_positive(self):
        with self.assertRaises(ValueError):
            self.config.limit = 0

    def test_invalid_optimizer_flag_rejected(self):
        with self.assertRaises(ValueError):
            self.config.optimizer_flags = ["not_a_real_flag"]


if __name__ == "__main__":
    unittest.main()