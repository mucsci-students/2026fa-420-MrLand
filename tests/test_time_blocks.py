
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
)

from services.time_block_service import (
    get_day,
    get_integer,
    add_time_block,
    view_time_blocks,
    modify_time_block,
    delete_time_block,
)


class TestTimeBlockCRUD(unittest.TestCase):

    def setUp(self):
        # Create a valid TimeSlotConfig before every test.
        # TimeSlotConfig requires all five weekdays to have at least one
        # time block and requires at least one enabled class pattern.
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
                            day="MON",
                            duration=75,
                            lab=False
                        )
                    ],
                    disabled=False
                )
            ]
        )

    # ---------------- ADD ----------------

    @patch("builtins.input", side_effect=[
        "MON",     # Day
        "13:00",   # Start time
        "30",      # Spacing
        "15:00"    # End time
    ])
    @patch("builtins.print")
    def test_add_time_block(self, mock_print, mock_input):
        add_time_block(self.time_slot_config)

        self.assertEqual(len(self.time_slot_config.times["MON"]), 2)

        block = self.time_slot_config.times["MON"][1]

        self.assertEqual(block.start, "13:00")
        self.assertEqual(block.spacing, 30)
        self.assertEqual(block.end, "15:00")

        mock_print.assert_any_call("Time block added successfully.")

    @patch("builtins.input", side_effect=[
        "INVALID"
    ])
    @patch("builtins.print")
    def test_add_invalid_day(self, mock_print, mock_input):
        add_time_block(self.time_slot_config)

        # No time block should have been added.
        self.assertEqual(len(self.time_slot_config.times["MON"]), 1)

        mock_print.assert_any_call(
            "Invalid day. Please enter MON, TUE, WED, THU, or FRI."
        )

    @patch("builtins.input", side_effect=[
        "MON",     # Day
        "13:00",   # Start time
        "30",      # Spacing
        "12:00"    # End time - before start time
    ])
    @patch("builtins.print")
    def test_add_invalid_time_block(self, mock_print, mock_input):
        add_time_block(self.time_slot_config)

        # Invalid block should not be added.
        self.assertEqual(len(self.time_slot_config.times["MON"]), 1)

        mock_print.assert_any_call("Invalid time block:")

    @patch("builtins.input", side_effect=[
        "MON",       # Day
        "13:00",     # Start time
        "30",        # Spacing
        "15:00"      # End time
    ])
    @patch("builtins.print")
    def test_add_time_block_new_day(self, mock_print, mock_input):
        # Remove Monday so the service has to create the list for the day.
        # We use model_construct here because TimeSlotConfig normally
        # requires every weekday to be present when initially constructed.
        self.time_slot_config.times.pop("MON")

        add_time_block(self.time_slot_config)

        self.assertIn("MON", self.time_slot_config.times)
        self.assertEqual(len(self.time_slot_config.times["MON"]), 1)

        block = self.time_slot_config.times["MON"][0]

        self.assertEqual(block.start, "13:00")
        self.assertEqual(block.spacing, 30)
        self.assertEqual(block.end, "15:00")

    # ---------------- VIEW ----------------

    @patch("builtins.print")
    def test_view_time_blocks(self, mock_print):
        view_time_blocks(self.time_slot_config)

        mock_print.assert_any_call("\nTIME BLOCKS")
        mock_print.assert_any_call("\nMON:")
        mock_print.assert_any_call(
            "  1. 09:00-12:00 (spacing: 30 minutes)"
        )

    @patch("builtins.print")
    def test_view_no_time_blocks(self, mock_print):
        # Create an object with no time blocks so we can test the
        # service's empty-configuration behavior.
        empty_config = TimeSlotConfig.model_construct(
            times={},
            classes=[]
        )

        view_time_blocks(empty_config)

        mock_print.assert_any_call("No time blocks found.")

    # ---------------- MODIFY ----------------

    @patch("builtins.input", side_effect=[
        "MON",     # Day
        "1",       # Time block number
        "13:00",   # New start time
        "60",      # New spacing
        "16:00"    # New end time
    ])
    @patch("builtins.print")
    def test_modify_time_block(self, mock_print, mock_input):
        modify_time_block(self.time_slot_config)

        block = self.time_slot_config.times["MON"][0]

        self.assertEqual(block.start, "13:00")
        self.assertEqual(block.spacing, 60)
        self.assertEqual(block.end, "16:00")

        mock_print.assert_any_call(
            "Time block modified successfully."
        )

    @patch("builtins.input", side_effect=[
        "MON",     # Day
        "99"       # Invalid time block number
    ])
    @patch("builtins.print")
    def test_modify_invalid_index(self, mock_print, mock_input):
        modify_time_block(self.time_slot_config)

        # Original time block should still be there.
        block = self.time_slot_config.times["MON"][0]

        self.assertEqual(block.start, "09:00")
        self.assertEqual(block.spacing, 30)
        self.assertEqual(block.end, "12:00")

        mock_print.assert_any_call("Invalid time block.")

    @patch("builtins.input", side_effect=[
        "SAT"
    ])
    @patch("builtins.print")
    def test_modify_invalid_day(self, mock_print, mock_input):
        modify_time_block(self.time_slot_config)

        mock_print.assert_any_call(
            "Invalid day. Please enter MON, TUE, WED, THU, or FRI."
        )

    @patch("builtins.input", side_effect=[
        "SAT"
    ])
    @patch("builtins.print")
    def test_modify_day_not_in_config(self, mock_print, mock_input):
        # get_day() prevents SAT from being accepted, so this specifically
        # tests the invalid-day path.
        modify_time_block(self.time_slot_config)

        mock_print.assert_any_call(
            "Invalid day. Please enter MON, TUE, WED, THU, or FRI."
        )

    @patch("builtins.input", side_effect=[
        "MON",     # Day
        "1",       # Time block number
        "16:00",   # New start time
        "30",      # New spacing
        "12:00"    # End before start
    ])
    @patch("builtins.print")
    def test_modify_invalid_time_block(self, mock_print, mock_input):
        modify_time_block(self.time_slot_config)

        # Original block should remain unchanged.
        block = self.time_slot_config.times["MON"][0]

        self.assertEqual(block.start, "09:00")
        self.assertEqual(block.spacing, 30)
        self.assertEqual(block.end, "12:00")

        mock_print.assert_any_call("Invalid time block:")

    # ---------------- DELETE ----------------

    @patch("builtins.input", side_effect=[
        "MON",     # Day
        "1"        # Time block number
    ])
    @patch("builtins.print")
    def test_delete_time_block(self, mock_print, mock_input):
        delete_time_block(self.time_slot_config)

        self.assertEqual(len(self.time_slot_config.times["MON"]), 0)

        mock_print.assert_any_call(
            "Time block deleted successfully."
        )

    @patch("builtins.input", side_effect=[
        "MON",     # Day
        "99"       # Invalid time block number
    ])
    @patch("builtins.print")
    def test_delete_invalid_index(self, mock_print, mock_input):
        delete_time_block(self.time_slot_config)

        # Original time block should still be there.
        self.assertEqual(len(self.time_slot_config.times["MON"]), 1)

        mock_print.assert_any_call("Invalid time block.")

    @patch("builtins.input", side_effect=[
        "SAT"
    ])
    @patch("builtins.print")
    def test_delete_invalid_day(self, mock_print, mock_input):
        delete_time_block(self.time_slot_config)

        mock_print.assert_any_call(
            "Invalid day. Please enter MON, TUE, WED, THU, or FRI."
        )

    # ---------------- GET DAY ----------------

    @patch("builtins.input", return_value="mon")
    def test_get_day_valid(self, mock_input):
        result = get_day()

        self.assertEqual(result, "MON")

    @patch("builtins.input", return_value="INVALID")
    @patch("builtins.print")
    def test_get_day_invalid(self, mock_print, mock_input):
        result = get_day()

        self.assertIsNone(result)

        mock_print.assert_called_with(
            "Invalid day. Please enter MON, TUE, WED, THU, or FRI."
        )

    # ---------------- GET INTEGER ----------------

    @patch("builtins.input", return_value="30")
    def test_get_integer(self, mock_input):
        result = get_integer("Enter spacing: ")

        self.assertEqual(result, 30)

    @patch("builtins.input", side_effect=[
        "abc",
        "45"
    ])
    @patch("builtins.print")
    def test_get_integer_invalid_then_valid(self, mock_print, mock_input):
        result = get_integer("Enter spacing: ")

        self.assertEqual(result, 45)

        mock_print.assert_called_with(
            "Please enter a valid number."
        )


class TestTimeBlockEdgeCases(unittest.TestCase):

    def setUp(self):
        # Create a valid TimeSlotConfig for edge-case tests.
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
                            day="MON",
                            duration=75,
                            lab=False
                        )
                    ],
                    disabled=False
                )
            ]
        )

    @patch("builtins.input", side_effect=[
        "MON",     # Day
        "0"        # Invalid time block number
    ])
    @patch("builtins.print")
    def test_modify_zero_index(self, mock_print, mock_input):
        modify_time_block(self.time_slot_config)

        mock_print.assert_any_call("Invalid time block.")

    @patch("builtins.input", side_effect=[
        "MON",     # Day
        "-1"       # Invalid time block number
    ])
    @patch("builtins.print")
    def test_delete_negative_index(self, mock_print, mock_input):
        delete_time_block(self.time_slot_config)

        mock_print.assert_any_call("Invalid time block.")

    @patch("builtins.input", side_effect=[
        "MON",     # Day
        "1",       # Time block number
        "09:00",   # Start
        "0",       # Invalid spacing
        "12:00"    # End
    ])
    @patch("builtins.print")
    def test_add_zero_spacing(self, mock_print, mock_input):
        add_time_block(self.time_slot_config)

        # TimeBlock requires spacing to be a PositiveInt.
        self.assertEqual(len(self.time_slot_config.times["MON"]), 1)

        mock_print.assert_any_call("Invalid time block:")


if __name__ == "__main__":
    unittest.main()

