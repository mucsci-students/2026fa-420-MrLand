
import unittest
from unittest.mock import patch
import sys
import os

# Add the project's src folder to Python's path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src_path = os.path.join(project_root, "src")
sys.path.insert(0, src_path)

from scheduler.config import (
    TimeSlotConfig,
    TimeBlock,
    ClassPattern,
    Meeting,
    Day,
    DeliveryMode,
)

import services.class_pattern_service as class_pattern


class TestClassPatternCRUD(unittest.TestCase):

    def setUp(self):
        # Create a valid TimeSlotConfig before every test.
        self.time_slot_config = TimeSlotConfig(
            times={
                "MON": [
                    TimeBlock(start="09:00", spacing=30, end="12:00")
                ],
                "TUE": [
                    TimeBlock(start="09:00", spacing=30, end="12:00")
                ],
                "WED": [
                    TimeBlock(start="09:00", spacing=30, end="12:00")
                ],
                "THU": [
                    TimeBlock(start="09:00", spacing=30, end="12:00")
                ],
                "FRI": [
                    TimeBlock(start="09:00", spacing=30, end="12:00")
                ],
            },
            classes=[
                ClassPattern(
                    credits=3,
                    meetings=[
                        Meeting(
                            day=Day.MON,
                            start_time="09:00",
                            duration=75,
                            lab=False,
                            delivery=DeliveryMode.IN_PERSON
                        )
                    ],
                    disabled=False,
                    start_time="09:00"
                )
            ]
        )

    # ---------------- GET DAY ----------------

    @patch("builtins.input", return_value="mon")
    def test_get_day_valid(self, mock_input):
        result = class_pattern.get_day()

        self.assertEqual(result, Day.MON)

    @patch("builtins.input", return_value="INVALID")
    @patch("builtins.print")
    def test_get_day_invalid(self, mock_print, mock_input):
        result = class_pattern.get_day()

        self.assertIsNone(result)

        mock_print.assert_called_with(
            "Invalid day. Please enter MON, TUE, WED, THU, or FRI."
        )

    # ---------------- GET INTEGER ----------------

    @patch("builtins.input", return_value="3")
    def test_get_integer(self, mock_input):
        result = class_pattern.get_integer("Enter number: ")

        self.assertEqual(result, 3)

    @patch("builtins.input", side_effect=[
        "abc",
        "3"
    ])
    @patch("builtins.print")
    def test_get_integer_invalid_then_valid(
        self,
        mock_print,
        mock_input
    ):
        result = class_pattern.get_integer("Enter number: ")

        self.assertEqual(result, 3)

        mock_print.assert_called_with(
            "Please enter a valid number."
        )

    # ---------------- DELIVERY MODE ----------------

    @patch("builtins.input", return_value="in_person")
    def test_get_delivery_mode_in_person(self, mock_input):
        result = class_pattern.get_delivery_mode()

        self.assertEqual(result, DeliveryMode.IN_PERSON)

    @patch("builtins.input", return_value="online")
    def test_get_delivery_mode_online(self, mock_input):
        result = class_pattern.get_delivery_mode()

        self.assertEqual(result, DeliveryMode.ONLINE)

    @patch("builtins.input", return_value="invalid")
    @patch("builtins.print")
    def test_get_delivery_mode_invalid(
        self,
        mock_print,
        mock_input
    ):
        result = class_pattern.get_delivery_mode()

        self.assertIsNone(result)

        mock_print.assert_called_with(
            "Invalid delivery mode."
        )

    # ---------------- CREATE MEETING ----------------

    @patch("builtins.input", side_effect=[
        "MON",       # Day
        "10:00",     # Start time
        "75",        # Duration
        "n",         # Lab
        "in_person"  # Delivery
    ])
    def test_create_meeting(self, mock_input):
        meeting = class_pattern.create_meeting()

        self.assertIsNotNone(meeting)
        self.assertEqual(meeting.day, Day.MON)
        self.assertEqual(meeting.start_time, "10:00")
        self.assertEqual(meeting.duration, 75)
        self.assertFalse(meeting.lab)
        self.assertEqual(
            meeting.delivery,
            DeliveryMode.IN_PERSON
        )

    @patch("builtins.input", side_effect=[
        "TUE",       # Day
        "",          # No start time
        "60",        # Duration
        "y",         # Lab
        "online"     # Delivery
    ])
    def test_create_meeting_no_start_time(self, mock_input):
        meeting = class_pattern.create_meeting()

        self.assertIsNotNone(meeting)
        self.assertEqual(meeting.day, Day.TUE)
        self.assertIsNone(meeting.start_time)
        self.assertEqual(meeting.duration, 60)
        self.assertTrue(meeting.lab)
        self.assertEqual(
            meeting.delivery,
            DeliveryMode.ONLINE
        )

    @patch("builtins.input", side_effect=[
        "SAT"
    ])
    @patch("builtins.print")
    def test_create_meeting_invalid_day(
        self,
        mock_print,
        mock_input
    ):
        result = class_pattern.create_meeting()

        self.assertIsNone(result)

    @patch("builtins.input", side_effect=[
        "MON",
        "10:00",
        "75",
        "n",
        "invalid"
    ])
    @patch("builtins.print")
    def test_create_meeting_invalid_delivery(
        self,
        mock_print,
        mock_input
    ):
        result = class_pattern.create_meeting()

        self.assertIsNone(result)

        mock_print.assert_called_with(
            "Invalid delivery mode."
        )

    # ---------------- ADD CLASS PATTERN ----------------

    @patch("builtins.input", side_effect=[
        "4",        # Credits
        "n",        # Disabled
        "10:00",    # Start time
        "y",        # Add meeting
        "TUE",      # Meeting day
        "10:00",    # Meeting start
        "75",       # Duration
        "n",        # Lab
        "in_person",# Delivery
        "n"         # Add another meeting
    ])
    @patch("builtins.print")
    def test_add_class_pattern(
        self,
        mock_print,
        mock_input
    ):
        class_pattern.add_class_pattern(self.time_slot_config)

        self.assertEqual(len(self.time_slot_config.classes), 2)

        pattern = self.time_slot_config.classes[1]

        self.assertEqual(pattern.credits, 4)
        self.assertFalse(pattern.disabled)
        self.assertEqual(pattern.start_time, "10:00")
        self.assertEqual(len(pattern.meetings), 1)

        meeting = pattern.meetings[0]

        self.assertEqual(meeting.day, Day.TUE)
        self.assertEqual(meeting.start_time, "10:00")
        self.assertEqual(meeting.duration, 75)
        self.assertFalse(meeting.lab)
        self.assertEqual(
            meeting.delivery,
            DeliveryMode.IN_PERSON
        )

        mock_print.assert_any_call(
            "Class pattern added successfully."
        )

    @patch("builtins.input", side_effect=[
        "4",        # Credits
        "n",        # Disabled
        "",         # No start time
        "n"         # No meetings
    ])
    @patch("builtins.print")
    def test_add_class_pattern_invalid_no_meetings(
        self,
        mock_print,
        mock_input
    ):
        class_pattern.add_class_pattern(self.time_slot_config)

        # The ClassPattern validator should reject a pattern
        # without meetings.
        self.assertEqual(len(self.time_slot_config.classes), 1)

        mock_print.assert_any_call(
            "Invalid class pattern:"
        )

    # ---------------- VIEW CLASS PATTERNS ----------------

    @patch("builtins.print")
    def test_view_class_patterns(self, mock_print):
        class_pattern.view_class_patterns(
            self.time_slot_config
        )

        mock_print.assert_any_call("\nCLASS PATTERNS")
        mock_print.assert_any_call("\n1. Credits: 3")
        mock_print.assert_any_call("   Status: Enabled")
        mock_print.assert_any_call("   Start time: 09:00")

    @patch("builtins.print")
    def test_view_class_patterns_empty(self, mock_print):
        empty_config = TimeSlotConfig.model_construct(
            times={},
            classes=[]
        )

        class_pattern.view_class_patterns(empty_config)

        mock_print.assert_any_call(
            "No class patterns found."
        )

    # ---------------- SELECT CLASS PATTERN ----------------

    @patch("builtins.input", return_value="1")
    @patch("builtins.print")
    def test_select_class_pattern(
        self,
        mock_print,
        mock_input
    ):
        result = class_pattern.select_class_pattern(
            self.time_slot_config
        )

        self.assertIsNotNone(result)
        self.assertEqual(result.credits, 3)

    @patch("builtins.input", return_value="99")
    @patch("builtins.print")
    def test_select_invalid_class_pattern(
        self,
        mock_print,
        mock_input
    ):
        result = class_pattern.select_class_pattern(
            self.time_slot_config
        )

        self.assertIsNone(result)

        mock_print.assert_any_call(
            "Invalid class pattern."
        )

    @patch("builtins.print")
    def test_select_class_pattern_empty(self, mock_print):
        empty_config = TimeSlotConfig.model_construct(
            times={},
            classes=[]
        )

        result = class_pattern.select_class_pattern(
            empty_config
        )

        self.assertIsNone(result)

        mock_print.assert_called_with(
            "No class patterns found."
        )

    # ---------------- MODIFY CLASS PATTERN ----------------

    @patch("builtins.input", side_effect=[
        "1",        # Pattern number
        "4",        # New credits
        "y",        # Disabled
        "11:00"     # New start time
    ])
    @patch("builtins.print")
    def test_modify_class_pattern(
        self,
        mock_print,
        mock_input
    ):
        class_pattern.modify_class_pattern(
            self.time_slot_config
        )

        pattern = self.time_slot_config.classes[0]

        self.assertEqual(pattern.credits, 4)
        self.assertTrue(pattern.disabled)
        self.assertEqual(pattern.start_time, "11:00")

        mock_print.assert_any_call(
            "Class pattern modified successfully."
        )

    @patch("builtins.input", side_effect=[
        "99"
    ])
    @patch("builtins.print")
    def test_modify_invalid_class_pattern(
        self,
        mock_print,
        mock_input
    ):
        class_pattern.modify_class_pattern(
            self.time_slot_config
        )

        mock_print.assert_any_call(
            "Invalid class pattern."
        )

    # ---------------- DELETE CLASS PATTERN ----------------

    @patch("builtins.input", return_value="1")
    @patch("builtins.print")
    def test_delete_class_pattern(
        self,
        mock_print,
        mock_input
    ):
        class_pattern.delete_class_pattern(
            self.time_slot_config
        )

        self.assertEqual(
            len(self.time_slot_config.classes),
            0
        )

        mock_print.assert_any_call(
            "Class pattern deleted successfully."
        )

    @patch("builtins.input", return_value="99")
    @patch("builtins.print")
    def test_delete_invalid_class_pattern(
        self,
        mock_print,
        mock_input
    ):
        class_pattern.delete_class_pattern(
            self.time_slot_config
        )

        self.assertEqual(
            len(self.time_slot_config.classes),
            1
        )

        mock_print.assert_any_call(
            "Invalid class pattern."
        )

    # =========================================================
    # MEETING CRUD
    # =========================================================

    # ---------------- SELECT MEETING ----------------

    @patch("builtins.input", side_effect=[
        "1",    # Class pattern
        "1"     # Meeting
    ])
    @patch("builtins.print")
    def test_select_meeting(
        self,
        mock_print,
        mock_input
    ):
        pattern, index = class_pattern.select_meeting(
            self.time_slot_config
        )

        self.assertIsNotNone(pattern)
        self.assertEqual(index, 0)

    @patch("builtins.input", side_effect=[
        "1",    # Class pattern
        "99"    # Meeting
    ])
    @patch("builtins.print")
    def test_select_invalid_meeting(
        self,
        mock_print,
        mock_input
    ):
        pattern, index = class_pattern.select_meeting(
            self.time_slot_config
        )

        self.assertIsNone(pattern)
        self.assertIsNone(index)

        mock_print.assert_any_call(
            "Invalid meeting."
        )

    # ---------------- ADD MEETING ----------------

    @patch("builtins.input", side_effect=[
        "1",         # Class pattern
        "TUE",       # Meeting day
        "10:00",     # Start time
        "75",        # Duration
        "n",         # Lab
        "online"     # Delivery
    ])
    @patch("builtins.print")
    def test_add_meeting(
        self,
        mock_print,
        mock_input
    ):
        class_pattern.add_meeting(
            self.time_slot_config
        )

        pattern = self.time_slot_config.classes[0]

        self.assertEqual(len(pattern.meetings), 2)

        meeting = pattern.meetings[1]

        self.assertEqual(meeting.day, Day.TUE)
        self.assertEqual(meeting.start_time, "10:00")
        self.assertEqual(meeting.duration, 75)
        self.assertFalse(meeting.lab)
        self.assertEqual(
            meeting.delivery,
            DeliveryMode.ONLINE
        )

        mock_print.assert_any_call(
            "Meeting added successfully."
        )

    @patch("builtins.input", side_effect=[
        "1",         # Class pattern
        "MON",       # Same day as existing meeting
        "11:00",     # Start
        "75",        # Duration
        "n",         # Lab
        "in_person"  # Delivery
    ])
    @patch("builtins.print")
    def test_add_duplicate_day_meeting(
        self,
        mock_print,
        mock_input
    ):
        class_pattern.add_meeting(
            self.time_slot_config
        )

        pattern = self.time_slot_config.classes[0]

        # Meeting should not be added if the ClassPattern
        # validator rejects the duplicate day.
        self.assertEqual(len(pattern.meetings), 1)

        mock_print.assert_any_call(
            "Meeting cannot be added:"
        )

    # ---------------- VIEW MEETINGS ----------------

    @patch("builtins.input", return_value="1")
    @patch("builtins.print")
    def test_view_meetings(
        self,
        mock_print,
        mock_input
    ):
        class_pattern.view_meetings(
            self.time_slot_config
        )

        mock_print.assert_any_call(
            "\nMEETINGS"
        )

        mock_print.assert_any_call(
            "1. MON 09:00 (75 min) Lab: False Delivery: in_person"
        )

    # ---------------- MODIFY MEETING ----------------

    @patch("builtins.input", side_effect=[
        "1",         # Class pattern
        "1",         # Meeting
        "TUE",       # New day
        "11:00",     # New start
        "90",        # Duration
        "n",         # Lab
        "online"     # Delivery
    ])
    @patch("builtins.print")
    def test_modify_meeting(
        self,
        mock_print,
        mock_input
    ):
        class_pattern.modify_meeting(
            self.time_slot_config
        )

        meeting = self.time_slot_config.classes[0].meetings[0]

        self.assertEqual(meeting.day, Day.TUE)
        self.assertEqual(meeting.start_time, "11:00")
        self.assertEqual(meeting.duration, 90)
        self.assertFalse(meeting.lab)
        self.assertEqual(
            meeting.delivery,
            DeliveryMode.ONLINE
        )

        mock_print.assert_any_call(
            "Meeting modified successfully."
        )

    @patch("builtins.input", side_effect=[
        "1",    # Class pattern
        "99"    # Invalid meeting
    ])
    @patch("builtins.print")
    def test_modify_invalid_meeting(
        self,
        mock_print,
        mock_input
    ):
        class_pattern.modify_meeting(
            self.time_slot_config
        )

        mock_print.assert_any_call(
            "Invalid meeting."
        )

    # ---------------- DELETE MEETING ----------------

    @patch("builtins.input", side_effect=[
        "1",    # Class pattern
        "1"     # Meeting
    ])
    @patch("builtins.print")
    def test_delete_meeting(
        self,
        mock_print,
        mock_input
    ):
        class_pattern.delete_meeting(
            self.time_slot_config
        )

        pattern = self.time_slot_config.classes[0]

        self.assertEqual(len(pattern.meetings), 0)

        mock_print.assert_any_call(
            "Meeting deleted successfully."
        )


if __name__ == "__main__":
    unittest.main()

