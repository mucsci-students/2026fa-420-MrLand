import unittest
from unittest.mock import patch

from scheduler.config import TimeRange

import src.services.rooms_service as rooms_service

# Unit tests for the rooms_service module
class TestRoomCRUD(unittest.TestCase):

    def setUp(self):
        # Clear the room list before every test
        rooms_service.rooms.clear()

    def test_add_room(self):
        # Inputs for add_rooms()
        inputs = [
            "Room 101",      # room name
            "30",            # capacity
            "Projector",     # feature
            "done",          # finish features
            "MON 09:00-17:00",
            "done",
        ]

        with patch("builtins.input", side_effect=inputs):
            rooms_service.add_rooms()

        # Check that one room was added
        self.assertEqual(len(rooms_service.rooms), 1)

        # Check the information that was entered
        new_room = rooms_service.rooms[0]

        self.assertEqual(new_room.name, "Room 101")
        self.assertEqual(new_room.capacity, 30)
        self.assertEqual(new_room.features, {"Projector"})

        self.assertEqual(
            new_room.times["MON"][0].start,
            "09:00"
        )

        self.assertEqual(
            new_room.times["MON"][0].end,
            "17:00"
        )

    def test_view_rooms(self):
        # Add a room directly so this test only tests view_rooms()
        room = rooms_service.RoomConfig(
            name="Room 101",
            capacity=30,
            features=["Projector"],
            times={
                "MON": [TimeRange.from_string("09:00-17:00")]
            }
        )

        rooms_service.rooms.append(room)

        # Capture what view_rooms() prints
        with patch("builtins.print") as mock_print:
            rooms_service.view_rooms()

        # Check that the room's information was printed
        printed_text = "\n".join(
            str(call.args[0]) for call in mock_print.call_args_list
        )

        self.assertIn("ROOMS:", printed_text)
        self.assertIn("Room 101", printed_text)
        self.assertIn("Capacity: 30", printed_text)

    def test_modify_room(self):
        # Add a room directly
        room = rooms_service.RoomConfig(
            name="Room 101",
            capacity=30,
            features=["Projector"],
            times={
                "MON": [TimeRange.from_string("09:00-17:00")]
            }
        )

        rooms_service.rooms.append(room)

        # Modify room capacity
        # First input = room number
        # Second input = attribute number
        # Third input = new capacity
        inputs = [
            "1",
            "2",
            "40"
        ]

        with patch("builtins.input", side_effect=inputs):
            rooms_service.modify_rooms()

        # Check that capacity changed
        self.assertEqual(
            rooms_service.rooms[0].capacity,
            40
        )

    def test_delete_room(self):
        # Add a room directly
        room = rooms_service.RoomConfig(
            name="Room 101",
            capacity=30,
            features=["Projector"],
            times={
                "MON": [TimeRange.from_string("09:00-17:00")]
            }
        )

        rooms_service.rooms.append(room)

        self.assertEqual(len(rooms_service.rooms), 1)

        # Delete the first room
        with patch("builtins.input", return_value="1"):
            rooms_service.delete_rooms()

        # Check that the room was deleted
        self.assertEqual(len(rooms_service.rooms), 0)


class TestGetRoomName(unittest.TestCase):

    def setUp(self):
        rooms_service.rooms.clear()

    @patch("builtins.input")
    @patch("builtins.print")
    def test_blank_name_retries_until_valid(self, mock_print, mock_input):
        mock_input.side_effect = ["", "   ", "Room 101"]

        result = rooms_service.get_room_name()

        self.assertEqual(result, "Room 101")
        self.assertEqual(mock_input.call_count, 3)
        mock_print.assert_any_call("Room name cannot be empty. Please try again.")

    @patch("builtins.input")
    @patch("builtins.print")
    def test_duplicate_name_retries_until_unique(self, mock_print, mock_input):
        rooms_service.rooms.append(
            rooms_service.RoomConfig(
                name="Room 101",
                capacity=20,
                features=[],
                times={}
            )
        )
        mock_input.side_effect = ["Room 101", "Room 202"]

        result = rooms_service.get_room_name()

        self.assertEqual(result, "Room 202")
        self.assertEqual(mock_input.call_count, 2)
        mock_print.assert_any_call("Room name already exists. Please try again.")


class TestGetRoomCapacity(unittest.TestCase):

    @patch("builtins.input")
    def test_valid_capacity(self, mock_input):
        mock_input.return_value = "25"

        result = rooms_service.get_room_capacity()

        self.assertEqual(result, 25)

    @patch("builtins.input")
    @patch("builtins.print")
    def test_invalid_capacity_retries_until_valid(self, mock_print, mock_input):
        mock_input.side_effect = ["0", "-5", "abc", "30"]

        result = rooms_service.get_room_capacity()

        self.assertEqual(result, 30)
        self.assertEqual(mock_input.call_count, 4)
        mock_print.assert_any_call("Capacity must be greater than zero. Please try again.")
        mock_print.assert_any_call("Capacity must be a positive integer. Please try again.")


class TestGetRoomFeatures(unittest.TestCase):

    @patch("builtins.input")
    def test_collects_non_empty_features_until_done(self, mock_input):
        mock_input.side_effect = ["Projector", "", "Whiteboard", "done"]

        result = rooms_service.get_room_features()

        self.assertEqual(result, ["Projector", "Whiteboard"])

    @patch("builtins.input")
    def test_done_immediately_returns_empty_list(self, mock_input):
        mock_input.return_value = "done"

        result = rooms_service.get_room_features()

        self.assertEqual(result, [])


class TestGetRoomAvailability(unittest.TestCase):

    @patch("builtins.input")
    def test_valid_availability_entries_are_collected(self, mock_input):
        mock_input.side_effect = [
            "MON 09:00-10:00",
            "done"
        ]

        result = rooms_service.get_room_availability()

        self.assertIn("MON", result)
        self.assertEqual(result["MON"][0].start, "09:00")
        self.assertEqual(result["MON"][0].end, "10:00")

    @patch("builtins.input")
    @patch("builtins.print")
    def test_invalid_availability_format_is_rejected(self, mock_print, mock_input):
        mock_input.side_effect = [
            "MON",
            "MON 09:00-10:00",
            "done"
        ]

        result = rooms_service.get_room_availability()

        self.assertIn("MON", result)
        mock_print.assert_any_call(
            "Invalid format. Please use the format: DAY HH:MM-HH:MM"
        )


if __name__ == "__main__":
    unittest.main()
