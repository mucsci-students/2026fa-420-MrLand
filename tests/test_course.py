
# file name: test_course.py
# Primary author: Dylan Groff
# run with: python -m unittest tests/test_course.py
# homebrew: python3 -m unittest tests/test_course.py

"""
Assertion Types:
assertEqual(a, b)	        a == b
assertNotEqual(a, b)	    a != b
assertTrue(x)	            x is true
assertFalse(x)	            x is false
assertIsNone(x)	            x is None
assertIsNotNone(x)	        x isn't None
assertIn(a, b)	            a is contained in b
assertRaises(...)	        code should produce an exception


@patch("builtins.input", return_value="___") mocks an input value from the user
@patch("builtins.input", side_effect=["___"]) mocks multiple inputs
"""

import unittest
from unittest.mock import patch
from src.controllers import course_operations_controller as course_service
from src.views.courses_gui import _faculty_candidates
from scheduler.config import CourseConfig


class TestCourse(unittest.TestCase):

    def setUp(self):
        self.course_members = []

    def test_explicit_faculty_candidates_override_derive_default(self):
        self.assertEqual(
            _faculty_candidates(True, "Dr. Smith, Dr. Jones"),
            ["Dr. Smith", "Dr. Jones"],
        )

    def test_empty_faculty_candidates_can_be_derived(self):
        self.assertIsNone(_faculty_candidates(True, ""))

    # --------- add, modify, delete tests --------------

    def test_add_course_from_values(self):
        course = course_service.add_course_from_values(
            self.course_members,
            "CS101",
            "001",
            3,
            30,
            "in_person",
            ["S101"],
            ["L101"],
            ["projector"],
            ["gpu"],
            True,
            [],
            ["Dr. Smith"],
        )

        self.assertIs(self.course_members[0], course)
        self.assertEqual(course.course_id, "CS101")
        self.assertEqual(course.section_id, "001")
        self.assertEqual(course.room, ["S101"])
        self.assertEqual(course.lab, ["L101"])
        self.assertEqual(course.required_room_features, {"projector"})
        self.assertEqual(course.required_lab_features, {"gpu"})
        self.assertEqual(course.faculty, ["Dr. Smith"])

    def test_online_course_clears_room_and_lab_fields(self):
        course = course_service.add_course_from_values(
            self.course_members,
            "CS102",
            None,
            3,
            30,
            "online",
            ["S101"],
            ["L101"],
            ["projector"],
            ["gpu"],
            True,
            [],
            None,
        )

        self.assertEqual(course.room, [])
        self.assertEqual(course.lab, [])
        self.assertEqual(course.required_room_features, set())
        self.assertEqual(course.required_lab_features, set())
        self.assertFalse(course.reserve_room_during_lab)

    def test_update_course_from_values(self):
        original = course_service.add_course_from_values(
            self.course_members,
            "CS101",
            "001",
            3,
            30,
            "in_person",
            ["S101"],
            [],
            [],
            [],
            True,
            [],
            ["Dr. Smith"],
        )
        other = course_service.add_course_from_values(
            self.course_members,
            "CS102",
            "001",
            3,
            30,
            "in_person",
            ["S102"],
            [],
            [],
            [],
            True,
            [],
            ["Dr. Jones"],
        )

        updated = course_service.update_course_from_values(
            self.course_members,
            original,
            "CS101",
            "001",
            4,
            40,
            "hybrid",
            ["S103"],
            [],
            ["accessible"],
            [],
            False,
            ["CS102"],
            ["Dr. Smith"],
        )

        self.assertIs(self.course_members[0], updated)
        self.assertIs(self.course_members[1], other)
        self.assertEqual(updated.credits, 4)
        self.assertEqual(updated.capacity, 40)
        self.assertEqual(updated.conflicts, ["CS102"])

    def test_duplicate_course_update_preserves_original(self):
        original = course_service.add_course_from_values(
            self.course_members,
            "CS101",
            "001",
            3,
            30,
            "in_person",
            ["S101"],
            [],
            [],
            [],
            True,
            [],
            None,
        )
        course_service.add_course_from_values(
            self.course_members,
            "CS102",
            "001",
            3,
            30,
            "in_person",
            ["S102"],
            [],
            [],
            [],
            True,
            [],
            None,
        )

        with self.assertRaisesRegex(ValueError, "already exists"):
            course_service.update_course_from_values(
                self.course_members,
                original,
                "CS102",
                "001",
                4,
                40,
                "in_person",
                ["S103"],
                [],
                [],
                [],
                True,
                [],
                None,
            )

        self.assertIs(self.course_members[0], original)
        self.assertEqual(original.credits, 3)

    def test_delete_course_from_values_removes_selected_course(self):
        first = course_service.add_course_from_values(
            self.course_members,
            "CS101",
            "001",
            3,
            30,
            "in_person",
            ["S101"],
            [],
            [],
            [],
            True,
            [],
            None,
        )
        selected = course_service.add_course_from_values(
            self.course_members,
            "CS102",
            "001",
            3,
            30,
            "in_person",
            ["S102"],
            [],
            [],
            [],
            True,
            [],
            None,
        )

        self.assertIs(
            course_service.delete_course_from_values(
                self.course_members, selected
            ),
            selected,
        )
        self.assertEqual(self.course_members, [first])

    # tests add_course
    @patch("builtins.input", side_effect=[
        "CS 101",                   # course ID
        "A",                        # section ID
        "3",                        # credits
        "28",                       # capacity
        "hybrid",                   # modality
        "Room A, Room B",           # room
        "Lab 1",                    # lab
        "accessible",               # room features
        "gpu",                      # lab features
        "no",                       # reserve room
        "",                         # conflicts
        "Dr. Smith, Dr. Johnson"    # faculty
    ])
    def test_add_course(self, mock_input):
        course_service.add_course(self.course_members)

        self.assertEqual(len(self.course_members), 1)
        self.assertEqual(self.course_members[0].course_id, "CS 101")
        self.assertEqual(self.course_members[0].section_id, "A")
        self.assertEqual(self.course_members[0].credits, 3)
        self.assertEqual(self.course_members[0].capacity, 28)
        self.assertEqual(self.course_members[0].modality, "hybrid")
        self.assertEqual(self.course_members[0].room, ["Room A", "Room B"])
        self.assertEqual(self.course_members[0].lab, ["Lab 1"])
        self.assertEqual(
            self.course_members[0].required_room_features,
            {"accessible"}
        )
        self.assertEqual(
            self.course_members[0].required_lab_features,
            {"gpu"}
        )
        self.assertEqual(
            self.course_members[0].reserve_room_during_lab,
            False
        )
        self.assertEqual(self.course_members[0].conflicts, [])
        self.assertEqual(
            self.course_members[0].faculty,
            ["Dr. Smith", "Dr. Johnson"]
        )

    @patch("builtins.input", side_effect=[
        "CS101",       # course ID
        "001",         # section ID
        "3",           # credits
        "30",          # capacity
        "in_person",   # modality
        "S101",        # room
        "",            # lab
        "",            # room features
        "",            # lab features
        "yes",         # reserve room
        "",            # conflicts
        "none"         # faculty
    ])
    def test_add_course_basic(self, mock_input):
        course_service.add_course(self.course_members)

        self.assertEqual(len(self.course_members), 1)
        self.assertEqual(self.course_members[0].course_id, "CS101")
        self.assertEqual(self.course_members[0].section_id, "001")
        self.assertEqual(self.course_members[0].credits, 3)
        self.assertEqual(self.course_members[0].capacity, 30)

    @patch("builtins.input", side_effect=[
        "CS101",
        "001",
        "3",
        "30",
        "in_person",
        "S101",
        "",
        "",
        "",
        "yes",
        "",
        "none",

        # Attempt to add duplicate
        "CS101",
        "001",

        # Enter a different course after duplicate is rejected
        "CS102",
        "001",
        "3",
        "30",
        "in_person",
        "S101",
        "",
        "",
        "",
        "yes",
        "",
        "none"
    ])
    def test_add_duplicate_course(self, mock_input):
        course_service.add_course(self.course_members)
        course_service.add_course(self.course_members)

        self.assertEqual(len(self.course_members), 2)
        self.assertEqual(self.course_members[0].course_id, "CS101")
        self.assertEqual(self.course_members[1].course_id, "CS102")

    @patch("builtins.input", side_effect=[
        "CS101",
        "001",
        "0",          # invalid credits
        "3",          # valid credits
        "30",
        "in_person",
        "S101",
        "",
        "",
        "",
        "yes",
        "",
        "none"
    ])
    def test_add_course_invalid_credits(self, mock_input):
        course_service.add_course(self.course_members)

        self.assertEqual(len(self.course_members), 1)
        self.assertEqual(self.course_members[0].credits, 3)

    @patch("builtins.input", side_effect=[
        "CS101",
        "001",
        "3",
        "0",          # invalid capacity
        "30",         # valid capacity
        "in_person",
        "S101",
        "",
        "",
        "",
        "yes",
        "",
        "none"
    ])
    def test_add_course_invalid_capacity(self, mock_input):
        course_service.add_course(self.course_members)

        self.assertEqual(len(self.course_members), 1)
        self.assertEqual(self.course_members[0].capacity, 30)

    @patch("builtins.input", side_effect=[
        "CS101",
        "",            # no section
        "3",
        "30",
        "online",
        "",            # room features
        "",            # lab features
        "yes",
        "",            # conflicts
        "none"
    ])
    def test_add_online_course(self, mock_input):
        course_service.add_course(self.course_members)

        self.assertEqual(len(self.course_members), 1)
        self.assertEqual(self.course_members[0].modality, "online")
        self.assertEqual(self.course_members[0].room, [])
        self.assertEqual(self.course_members[0].lab, [])

    # tests modify_course
    @patch("builtins.input", side_effect=[
        "CS101",
        "001",
        "3",
        "30",
        "in_person",
        "S101",
        "",
        "",
        "",
        "yes",
        "",
        "none"
    ])
    def test_modify_course_id(self, mock_input):
        course_service.add_course(self.course_members)

        with patch("builtins.input", side_effect=[
            "1",       # course number
            "1",       # field: Course ID
            "CS102"    # new course ID
        ]):
            course_service.modify_course(self.course_members)

        self.assertEqual(self.course_members[0].course_id, "CS102")

    @patch("builtins.input", side_effect=[
        "CS101",
        "001",
        "3",
        "30",
        "in_person",
        "S101",
        "",
        "",
        "",
        "yes",
        "",
        "none"
    ])
    def test_modify_course_credits(self, mock_input):
        course_service.add_course(self.course_members)

        with patch("builtins.input", side_effect=[
            "1",       # course number
            "3",       # field: Credits
            "4"        # new credits
        ]):
            course_service.modify_course(self.course_members)

        self.assertEqual(self.course_members[0].credits, 4)

    @patch("builtins.input", side_effect=[
        "CS101",
        "001",
        "3",
        "30",
        "in_person",
        "S101",
        "",
        "",
        "",
        "yes",
        "",
        "none"
    ])
    def test_modify_course_capacity(self, mock_input):
        course_service.add_course(self.course_members)

        with patch("builtins.input", side_effect=[
            "1",       # course number
            "4",       # field: Capacity
            "50"       # new capacity
        ]):
            course_service.modify_course(self.course_members)

        self.assertEqual(self.course_members[0].capacity, 50)

    @patch("builtins.input", side_effect=[
        "CS101",
        "001",
        "3",
        "30",
        "in_person",
        "S101",
        "",
        "",
        "",
        "yes",
        "",
        "none"
    ])
    def test_modify_course_modality(self, mock_input):
        course_service.add_course(self.course_members)

        with patch("builtins.input", side_effect=[
            "1",        # course number
            "5",        # field: Modality
            "online"    # new modality
        ]):
            course_service.modify_course(self.course_members)

        self.assertEqual(self.course_members[0].modality, "online")
        self.assertEqual(self.course_members[0].room, [])
        self.assertEqual(self.course_members[0].lab, [])

    # tests delete_course
    def test_delete_course(self):
        course = CourseConfig(
            course_id="CS101",
            section_id="001",
            credits=3,
            capacity=30,
            modality="in_person",
            room=["S101"],
            lab=[],
            required_room_features=set(),
            required_lab_features=set(),
            reserve_room_during_lab=True,
            conflicts=[],
            faculty=None
        )

        self.course_members.append(course)

        with patch("builtins.input", return_value="1"):
            course_service.delete_course(self.course_members)

        self.assertEqual(len(self.course_members), 0)

    @patch("builtins.input", side_effect=[
        "CS101",
        "001",
        "3",
        "30",
        "in_person",
        "S101",
        "",
        "",
        "",
        "yes",
        "",
        "none",

        "CS102",
        "001",
        "3",
        "30",
        "in_person",
        "S102",
        "",
        "",
        "",
        "yes",
        "",
        "none"
    ])
    def test_delete_correct_course(self, mock_input):
        course_service.add_course(self.course_members)
        course_service.add_course(self.course_members)

        with patch("builtins.input", return_value="1"):
            course_service.delete_course(self.course_members)

        self.assertEqual(len(self.course_members), 1)
        self.assertEqual(self.course_members[0].course_id, "CS102")

    def test_delete_course_when_empty(self):
        course_service.delete_course(self.course_members)

        self.assertEqual(len(self.course_members), 0)

    # ------- test getters -----------------------------

    # -------------------------
    # get_course_id()
    # -------------------------

    @patch("builtins.input", return_value="CS101")
    def test_get_course_id(self, mock_input):
        result = course_service.get_course_id()

        self.assertEqual(result, "CS101")

    @patch("builtins.input", side_effect=["", "CS101"])
    def test_get_course_id_invalid(self, mock_input):
        result = course_service.get_course_id()

        self.assertEqual(result, "CS101")
        self.assertEqual(mock_input.call_count, 2)

    # -------------------------
    # get_section_id()
    # -------------------------

    @patch("builtins.input", return_value="001")
    def test_get_section_id(self, mock_input):
        result = course_service.get_section_id()

        self.assertEqual(result, "001")

    @patch("builtins.input", return_value="")
    def test_get_section_id_empty(self, mock_input):
        result = course_service.get_section_id()

        self.assertIsNone(result)

    # -------------------------
    # get_credits()
    # -------------------------

    @patch("builtins.input", return_value="3")
    def test_get_credits(self, mock_input):
        result = course_service.get_credits()

        self.assertEqual(result, 3)

    @patch("builtins.input", side_effect=["0", "3"])
    def test_get_credits_invalid(self, mock_input):
        result = course_service.get_credits()

        self.assertEqual(result, 3)
        self.assertEqual(mock_input.call_count, 2)

    # -------------------------
    # get_capacity()
    # -------------------------

    @patch("builtins.input", return_value="30")
    def test_get_capacity(self, mock_input):
        result = course_service.get_capacity()

        self.assertEqual(result, 30)

    @patch("builtins.input", side_effect=["-5", "30"])
    def test_get_capacity_invalid(self, mock_input):
        result = course_service.get_capacity()

        self.assertEqual(result, 30)
        self.assertEqual(mock_input.call_count, 2)

    # -------------------------
    # get_modality()
    # -------------------------

    @patch("builtins.input", return_value="in_person")
    def test_get_modality(self, mock_input):
        result = course_service.get_modality()

        self.assertEqual(result, "in_person")

    @patch("builtins.input", side_effect=["invalid", "online"])
    def test_get_modality_invalid(self, mock_input):
        result = course_service.get_modality()

        self.assertEqual(result, "online")
        self.assertEqual(mock_input.call_count, 2)

    # -------------------------
    # get_room()
    # -------------------------

    @patch("builtins.input", return_value="S101, S102")
    def test_get_room(self, mock_input):
        result = course_service.get_room()

        self.assertEqual(result, ["S101", "S102"])

    @patch("builtins.input", side_effect=["S101,,S102", "S101,S102"])
    def test_get_room_invalid(self, mock_input):
        result = course_service.get_room()

        self.assertEqual(result, ["S101", "S102"])
        self.assertEqual(mock_input.call_count, 2)

    # -------------------------
    # get_lab()
    # -------------------------

    @patch("builtins.input", return_value="L101, L102")
    def test_get_lab(self, mock_input):
        result = course_service.get_lab()

        self.assertEqual(result, ["L101", "L102"])

    @patch("builtins.input", side_effect=["L101,,L102", "L101,L102"])
    def test_get_lab_invalid(self, mock_input):
        result = course_service.get_lab()

        self.assertEqual(result, ["L101", "L102"])
        self.assertEqual(mock_input.call_count, 2)

    # -------------------------
    # get_required_room_features()
    # -------------------------

    @patch("builtins.input", return_value="projector, whiteboard")
    def test_get_required_room_features(self, mock_input):
        result = course_service.get_required_room_features()

        self.assertEqual(result, {"projector", "whiteboard"})

    @patch("builtins.input", side_effect=[
        "projector,,whiteboard",
        "projector,whiteboard"
    ])
    def test_get_required_room_features_invalid(self, mock_input):
        result = course_service.get_required_room_features()

        self.assertEqual(result, {"projector", "whiteboard"})
        self.assertEqual(mock_input.call_count, 2)

    # -------------------------
    # get_required_lab_features()
    # -------------------------

    @patch("builtins.input", return_value="computers, software")
    def test_get_required_lab_features(self, mock_input):
        result = course_service.get_required_lab_features()

        self.assertEqual(result, {"computers", "software"})

    @patch("builtins.input", side_effect=[
        "computers,,software",
        "computers,software"
    ])
    def test_get_required_lab_features_invalid(self, mock_input):
        result = course_service.get_required_lab_features()

        self.assertEqual(result, {"computers", "software"})
        self.assertEqual(mock_input.call_count, 2)

    # -------------------------
    # get_reserve_room()
    # -------------------------

    @patch("builtins.input", return_value="yes")
    def test_get_reserve_room(self, mock_input):
        result = course_service.get_reserve_room()

        self.assertTrue(result)

    @patch("builtins.input", side_effect=["maybe", "no"])
    def test_get_reserve_room_invalid(self, mock_input):
        result = course_service.get_reserve_room()

        self.assertFalse(result)
        self.assertEqual(mock_input.call_count, 2)

    # -------------------------
    # get_conflicts()
    # -------------------------

    @patch("builtins.input", return_value="")
    def test_get_conflicts_empty(self, mock_input):
        result = course_service.get_conflicts(self.course_members, "CS101")

        self.assertEqual(result, [])

    # -------------------------
    # get_faculty()
    # -------------------------

    @patch("builtins.input", return_value="Smith, Jones")
    def test_get_faculty(self, mock_input):
        result = course_service.get_faculty()

        self.assertEqual(result, ["Smith", "Jones"])

    @patch("builtins.input", return_value="none")
    def test_get_faculty_none(self, mock_input):
        result = course_service.get_faculty()

        self.assertIsNone(result)
