
import unittest
from unittest.mock import patch
import sys
import os

# Add the project's src folder to Python's path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src_path = os.path.join(project_root, "src")
sys.path.insert(0, src_path)

import src.services.faculty_service as faculty


class TestFacultyCRUD(unittest.TestCase):

    def setUp(self):
        # Create a separate faculty list for every test
        self.faculty_members = []

    def test_add_faculty(self):
        # Inputs for add_faculty()
        inputs = [
            "Dr. Smith",       # name
            "12",              # maximum credits
            "6",               # minimum credits
            "3",               # course limit

            # Monday availability
            "09:00-17:00",
            "done",

            # Tuesday
            "09:00-17:00",
            "done",

            # Wednesday
            "09:00-17:00",
            "done",

            # Thursday
            "done",

            # Friday
            "done",

            "4",               # maximum days

            # Course preferences
            "CS101",
            "10",
            "done",

            # Room preferences
            "Room A",
            "8",
            "done",

            # Lab preferences
            "Lab 1",
            "7",
            "done",

            # Mandatory days
            "mon",
            "wed",
            "done"
        ]

        with patch("builtins.input", side_effect=inputs):
            faculty.add_faculty(self.faculty_members)

        # Check that one faculty member was added
        self.assertEqual(len(self.faculty_members), 1)

        # Check the information that was entered
        new_faculty = self.faculty_members[0]

        self.assertEqual(new_faculty.name, "Dr. Smith")
        self.assertEqual(new_faculty.maximum_credits, 12)
        self.assertEqual(new_faculty.minimum_credits, 6)
        self.assertEqual(new_faculty.unique_course_limit, 3)
        self.assertEqual(new_faculty.maximum_days, 4)

        self.assertEqual(
            new_faculty.times["MON"][0].start,
            "09:00"
        )

        self.assertEqual(
            new_faculty.times["MON"][0].end,
            "17:00"
        )

        self.assertEqual(
            new_faculty.course_preferences,
            {"CS101": 10}
        )

        self.assertEqual(
            new_faculty.room_preferences,
            {"Room A": 8}
        )

        self.assertEqual(
            new_faculty.lab_preferences,
            {"Lab 1": 7}
        )

        self.assertEqual(
            new_faculty.mandatory_days,
            {"MON", "WED"}
        )

    def test_view_faculty(self):
        # Add a faculty member directly so this test
        # only tests view_faculty()
        faculty_member = faculty.FacultyConfig(
            name="Dr. Smith",
            maximum_credits=12,
            minimum_credits=6,
            unique_course_limit=3,
            maximum_days=4,
            times={
                "MON": ["09:00-17:00"],
                "TUE": ["09:00-17:00"]
            },
            course_preferences={"CS101": 10},
            room_preferences={"Room A": 8},
            lab_preferences={"Lab 1": 7},
            mandatory_days={"MON"}
        )

        self.faculty_members.append(faculty_member)

        # Capture what view_faculty() prints
        with patch("builtins.print") as mock_print:
            faculty.view_faculty(self.faculty_members)

        # Check that the faculty member's information was printed
        printed_text = "\n".join(
            str(call.args[0]) for call in mock_print.call_args_list
        )

        self.assertIn("Dr. Smith", printed_text)
        self.assertIn("Maximum Credits: 12", printed_text)
        self.assertIn("Minimum Credits: 6", printed_text)
        self.assertIn("Course Limit: 3", printed_text)
        self.assertIn("Maximum Days: 4", printed_text)

    def test_modify_faculty(self):
        # Add a faculty member directly
        faculty_member = faculty.FacultyConfig(
            name="Dr. Smith",
            maximum_credits=12,
            minimum_credits=6,
            unique_course_limit=3,
            maximum_days=4,
            times={
                "MON": ["09:00-17:00"]
            },
            course_preferences={},
            room_preferences={},
            lab_preferences={},
            mandatory_days={"MON"}
        )

        self.faculty_members.append(faculty_member)

        # Modify maximum credits
        # First input = faculty number
        # Second input = attribute number
        # Third input = new maximum credits
        inputs = [
            "1",
            "2",
            "15"
        ]

        with patch("builtins.input", side_effect=inputs):
            faculty.modify_faculty(self.faculty_members)

        # Check that maximum credits changed
        self.assertEqual(
            self.faculty_members[0].maximum_credits,
            15
        )

    def test_delete_faculty(self):
        # Add a faculty member directly
        faculty_member = faculty.FacultyConfig(
            name="Dr. Smith",
            maximum_credits=12,
            minimum_credits=6,
            unique_course_limit=3,
            maximum_days=4,
            times={
                "MON": ["09:00-17:00"]
            },
            course_preferences={},
            room_preferences={},
            lab_preferences={},
            mandatory_days={"MON"}
        )

        self.faculty_members.append(faculty_member)

        self.assertEqual(len(self.faculty_members), 1)

        # Delete the first faculty member
        with patch("builtins.input", return_value="1"):
            faculty.delete_faculty(self.faculty_members)

        # Check that the faculty member was deleted
        self.assertEqual(len(self.faculty_members), 0)


class TestFacultyGetters(unittest.TestCase):
    """Direct tests of the individual input-getter helper functions."""

    def setUp(self):
        self.faculty_members = []

    def test_get_name_rejects_duplicate_case_insensitive(self):
        existing = faculty.FacultyConfig(
            name="Dr. Smith",
            maximum_credits=12,
            minimum_credits=6,
            unique_course_limit=3,
            maximum_days=4,
            times={},
            course_preferences={},
            room_preferences={},
            lab_preferences={},
            mandatory_days=set()
        )

        self.faculty_members.append(existing)

        # First attempt reuses the existing name in a different case,
        # so get_name() should prompt again.
        inputs = ["dr. smith", "Dr. Jones"]

        with patch("builtins.input", side_effect=inputs):
            with patch("builtins.print") as mock_print:
                result = faculty.get_name(self.faculty_members)

        self.assertEqual(result, "Dr. Jones")

        printed_text = "\n".join(
            str(c.args[0]) for c in mock_print.call_args_list
        )

        self.assertIn("already exists", printed_text)

    def test_get_max_credits_invalid_then_valid(self):
        with patch("builtins.input", side_effect=["not_a_number", "12"]):
            with patch("builtins.print"):
                result = faculty.get_max_credits()

        self.assertEqual(result, 12)

    def test_get_min_credits_invalid_then_valid(self):
        with patch("builtins.input", side_effect=["abc", "6"]):
            with patch("builtins.print"):
                result = faculty.get_min_credits()

        self.assertEqual(result, 6)

    def test_get_course_limit_invalid_then_valid(self):
        with patch("builtins.input", side_effect=["x", "3"]):
            with patch("builtins.print"):
                result = faculty.get_course_limit()

        self.assertEqual(result, 3)

    def test_get_max_days_invalid_then_valid(self):
        with patch("builtins.input", side_effect=["", "5"]):
            with patch("builtins.print"):
                result = faculty.get_max_days()

        self.assertEqual(result, 5)

    def test_faculty_times_multiple_ranges_single_day(self):
        inputs = [
            # MON: two ranges
            "09:00-12:00",
            "13:00-17:00",
            "done",

            # TUE - FRI: nothing entered
            "done",
            "done",
            "done",
            "done",
        ]

        with patch("builtins.input", side_effect=inputs):
            with patch("builtins.print"):
                times = faculty.faculty_times()

        self.assertEqual(
            times["MON"],
            ["09:00-12:00", "13:00-17:00"]
        )

        # Days with no ranges entered should not appear in the dict
        self.assertNotIn("TUE", times)
        self.assertNotIn("WED", times)

    def test_course_preference_getter_rejects_out_of_range_then_accepts(self):
        inputs = ["CS101", "15", "5", "done"]

        with patch("builtins.input", side_effect=inputs):
            with patch("builtins.print") as mock_print:
                result = faculty.course_preference_getter()

        self.assertEqual(result, {"CS101": 5})

        printed_text = "\n".join(
            str(c.args[0]) for c in mock_print.call_args_list
        )

        self.assertIn("Invalid preference", printed_text)

    def test_course_preference_getter_rejects_non_digit(self):
        inputs = ["CS101", "abc", "7", "done"]

        with patch("builtins.input", side_effect=inputs):
            with patch("builtins.print"):
                result = faculty.course_preference_getter()

        self.assertEqual(result, {"CS101": 7})

    def test_room_preference_getter_basic(self):
        inputs = ["Room A", "8", "done"]

        with patch("builtins.input", side_effect=inputs):
            with patch("builtins.print"):
                result = faculty.room_preference_getter()

        self.assertEqual(result, {"Room A": 8})

    def test_lab_preference_getter_basic(self):
        inputs = ["Lab 1", "9", "done"]

        with patch("builtins.input", side_effect=inputs):
            with patch("builtins.print"):
                result = faculty.lab_preference_getter()

        self.assertEqual(result, {"Lab 1": 9})

    def test_mandatory_days_getter_rejects_invalid_day(self):
        inputs = ["funday", "mon", "fri", "done"]

        with patch("builtins.input", side_effect=inputs):
            with patch("builtins.print") as mock_print:
                result = faculty.mandatory_days_getter()

        self.assertEqual(result, {"MON", "FRI"})

        printed_text = "\n".join(
            str(c.args[0]) for c in mock_print.call_args_list
        )

        self.assertIn("Invalid day", printed_text)

    def test_mandatory_days_getter_no_days_selected(self):
        with patch("builtins.input", side_effect=["done"]):
            with patch("builtins.print"):
                result = faculty.mandatory_days_getter()

        self.assertEqual(result, set())


class TestViewFacultyNames(unittest.TestCase):

    def setUp(self):
        self.faculty_members = []

    def test_empty_list_returns_false(self):
        with patch("builtins.print") as mock_print:
            result = faculty.view_faculty_names(self.faculty_members)

        self.assertFalse(result)

        printed_text = "\n".join(
            str(c.args[0]) for c in mock_print.call_args_list
        )

        self.assertIn("No faculty members found.", printed_text)

    def test_prints_all_faculty_member_names(self):
        for name in ["Dr. Smith", "Dr. Jones", "Dr. Lee"]:
            self.faculty_members.append(
                faculty.FacultyConfig(
                    name=name,
                    maximum_credits=12,
                    minimum_credits=6,
                    unique_course_limit=3,
                    maximum_days=4,
                    times={},
                    course_preferences={},
                    room_preferences={},
                    lab_preferences={},
                    mandatory_days=set()
                )
            )

        with patch("builtins.print") as mock_print:
            result = faculty.view_faculty_names(self.faculty_members)

        self.assertTrue(result)

        printed_text = "\n".join(
            str(c.args[0]) for c in mock_print.call_args_list
        )

        self.assertIn("Dr. Smith", printed_text)
        self.assertIn("Dr. Jones", printed_text)
        self.assertIn("Dr. Lee", printed_text)


class TestViewFacultyEdgeCases(unittest.TestCase):

    def setUp(self):
        self.faculty_members = []

    def test_view_faculty_empty_list(self):
        with patch("builtins.print") as mock_print:
            faculty.view_faculty(self.faculty_members)

        mock_print.assert_called_once_with(
            "No faculty members found."
        )

    def test_view_faculty_prints_all_members(self):
        # Unlike view_faculty_names(), view_faculty() has no early-return
        # bug, so every member should be printed.
        for name in ["Dr. Smith", "Dr. Jones"]:
            self.faculty_members.append(
                faculty.FacultyConfig(
                    name=name,
                    maximum_credits=12,
                    minimum_credits=6,
                    unique_course_limit=3,
                    maximum_days=4,
                    times={},
                    course_preferences={},
                    room_preferences={},
                    lab_preferences={},
                    mandatory_days=set()
                )
            )

        with patch("builtins.print") as mock_print:
            faculty.view_faculty(self.faculty_members)

        printed_text = "\n".join(
            str(c.args[0]) for c in mock_print.call_args_list
        )

        self.assertIn("Dr. Smith", printed_text)
        self.assertIn("Dr. Jones", printed_text)


class TestModifyFacultyEdgeCases(unittest.TestCase):

    def setUp(self):
        self.faculty_members = []

        self.faculty_member = faculty.FacultyConfig(
            name="Dr. Smith",
            maximum_credits=12,
            minimum_credits=6,
            unique_course_limit=3,
            maximum_days=4,
            times={
                "MON": ["09:00-17:00"],
                "TUE": ["09:00-17:00"],
                "THU": ["09:00-17:00"]
            },
            course_preferences={},
            room_preferences={},
            lab_preferences={},
            mandatory_days={"MON"}
        )

        self.faculty_members.append(self.faculty_member)

    def test_modify_faculty_with_empty_list_prompts_nothing(self):
        self.faculty_members.clear()

        with patch("builtins.input") as mock_input:
            with patch("builtins.print"):
                faculty.modify_faculty(self.faculty_members)

        mock_input.assert_not_called()

    def test_modify_faculty_invalid_index_then_valid(self):
        # First attempt: non-numeric index triggers a ValueError and a
        # recursive call back into modify_faculty(); the second attempt
        # succeeds with a valid index/attribute/value.
        inputs = [
            "not_a_number",
            "1",
            "2",
            "20"
        ]

        with patch("builtins.input", side_effect=inputs):
            with patch("builtins.print"):
                faculty.modify_faculty(self.faculty_members)

        self.assertEqual(
            self.faculty_members[0].maximum_credits,
            20
        )

    def test_modify_faculty_index_out_of_range(self):
        with patch("builtins.input", side_effect=["99"]):
            with patch("builtins.print") as mock_print:
                faculty.modify_faculty(self.faculty_members)

        printed_text = "\n".join(
            str(c.args[0]) for c in mock_print.call_args_list
        )

        self.assertIn("Invalid selection.", printed_text)

        # Faculty member should be untouched
        self.assertEqual(
            self.faculty_members[0].maximum_credits,
            12
        )

    def test_modify_faculty_invalid_attribute_choice_leaves_data_unchanged(self):
        # Valid faculty index, but an out-of-range attribute number.
        inputs = ["1", "99"]

        with patch("builtins.input", side_effect=inputs):
            with patch("builtins.print") as mock_print:
                faculty.modify_faculty(self.faculty_members)

        printed_text = "\n".join(
            str(c.args[0]) for c in mock_print.call_args_list
        )

        self.assertIn("Invalid selection.", printed_text)

        self.assertEqual(
            self.faculty_members[0].maximum_credits,
            12
        )

        self.assertEqual(
            self.faculty_members[0].minimum_credits,
            6
        )

    def test_modify_faculty_non_numeric_attribute_choice_retries_then_bails(self):
        # A non-numeric attribute choice raises inside the try block and
        # is caught, prompting the retry/(f)aculty menu; choosing "f"
        # exits without modifying anything.
        inputs = [
            "1",
            "not_a_number",
            "f"
        ]

        with patch("builtins.input", side_effect=inputs):
            with patch("builtins.print"):
                faculty.modify_faculty(self.faculty_members)

        self.assertEqual(
            self.faculty_members[0].maximum_credits,
            12
        )

    def test_modify_faculty_name(self):
        inputs = [
            "1",
            "1",
            "Dr. Renamed"
        ]

        with patch("builtins.input", side_effect=inputs):
            faculty.modify_faculty(self.faculty_members)

        self.assertEqual(
            self.faculty_members[0].name,
            "Dr. Renamed"
        )

    def test_modify_faculty_mandatory_days(self):
        inputs = [
            "1",
            "10",
            "tue",
            "thu",
            "done"
        ]

        with patch("builtins.input", side_effect=inputs):
            faculty.modify_faculty(self.faculty_members)

        self.assertEqual(
            self.faculty_members[0].mandatory_days,
            {"TUE", "THU"}
        )


class TestDeleteFacultyEdgeCases(unittest.TestCase):

    def setUp(self):
        self.faculty_members = []

        self.faculty_members.append(
            faculty.FacultyConfig(
                name="Dr. Smith",
                maximum_credits=12,
                minimum_credits=6,
                unique_course_limit=3,
                maximum_days=4,
                times={
                    "MON": ["09:00-17:00"]
                },
                course_preferences={},
                room_preferences={},
                lab_preferences={},
                mandatory_days={"MON"}
            )
        )

    def test_delete_faculty_invalid_input_leaves_list_unchanged(self):
        with patch("builtins.input", return_value="not_a_number"):
            with patch("builtins.print") as mock_print:
                faculty.delete_faculty(self.faculty_members)

        printed_text = "\n".join(
            str(c.args[0]) for c in mock_print.call_args_list
        )

        self.assertIn(
            "Invalid input. Please enter a valid number.",
            printed_text
        )

        self.assertEqual(
            len(self.faculty_members),
            1
        )

    def test_delete_faculty_out_of_range_leaves_list_unchanged(self):
        with patch("builtins.input", return_value="99"):
            with patch("builtins.print") as mock_print:
                faculty.delete_faculty(self.faculty_members)

        printed_text = "\n".join(
            str(c.args[0]) for c in mock_print.call_args_list
        )

        self.assertIn(
            "Invalid selection.",
            printed_text
        )

        self.assertEqual(
            len(self.faculty_members),
            1
        )

    def test_delete_faculty_correct_member_among_multiple(self):
        self.faculty_members.append(
            faculty.FacultyConfig(
                name="Dr. Jones",
                maximum_credits=9,
                minimum_credits=3,
                unique_course_limit=2,
                maximum_days=3,
                times={},
                course_preferences={},
                room_preferences={},
                lab_preferences={},
                mandatory_days=set()
            )
        )

        self.assertEqual(
            len(self.faculty_members),
            2
        )

        # Delete faculty member #2 ("Dr. Jones")
        with patch("builtins.input", return_value="2"):
            with patch("builtins.print"):
                faculty.delete_faculty(self.faculty_members)

        self.assertEqual(
            len(self.faculty_members),
            1
        )

        self.assertEqual(
            self.faculty_members[0].name,
            "Dr. Smith"
        )


if __name__ == "__main__":
    unittest.main()

