import unittest
from unittest.mock import patch

import src.services.faculty_service as faculty


class TestFacultyCRUD(unittest.TestCase):

    def setUp(self):
        # Clear the faculty list before every test
        faculty.faculty_members.clear()

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
            faculty.add_faculty()

        # Check that one faculty member was added
        self.assertEqual(len(faculty.faculty_members), 1)

        # Check the information that was entered
        new_faculty = faculty.faculty_members[0]

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

        faculty.faculty_members.append(faculty_member)

        # Capture what view_faculty() prints
        with patch("builtins.print") as mock_print:
            faculty.view_faculty()

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

        faculty.faculty_members.append(faculty_member)

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
            faculty.modify_faculty()

        # Check that maximum credits changed
        self.assertEqual(
            faculty.faculty_members[0].maximum_credits,
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

        faculty.faculty_members.append(faculty_member)

        self.assertEqual(len(faculty.faculty_members), 1)

        # Delete the first faculty member
        with patch("builtins.input", return_value="1"):
            faculty.delete_faculty()

        # Check that the faculty member was deleted
        self.assertEqual(len(faculty.faculty_members), 0)


if __name__ == "__main__":
    unittest.main()
