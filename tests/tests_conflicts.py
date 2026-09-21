
import unittest
from unittest.mock import patch

from scheduler.config import CourseConfig

import src.conflict as conflict

MODULE = "src.conflict"


def make_course(course_id, conflicts=None):
    """Helper to build a minimal valid CourseConfig for conflict tests."""
    return CourseConfig(
        course_id=course_id,
        credits=3,
        capacity=30,
        room=[f"Room-{course_id}"],
        conflicts=conflicts if conflicts is not None else [],
        faculty=None,
    )


class ConflictTestBase(unittest.TestCase):

    def setUp(self):
        self.course_a = make_course("CS101")
        self.course_b = make_course("CS102")
        self.course_c = make_course("CS103")
        self.course_d = make_course("CS104")

        self.courses = [
            self.course_a,
            self.course_b,
            self.course_c,
            self.course_d,
        ]


class TestAddConflicts(ConflictTestBase):
    """add_conflicts() operates on a course_id, conflicts list,
    and courses list."""

    def test_add_single(self):
        conflicts = []

        with patch("builtins.input", return_value="CS102"):
            result = conflict.add_conflicts(
                "CS101",
                conflicts,
                self.courses
            )

        self.assertEqual(result, ["CS102"])

    def test_add_comma_separated_list(self):
        conflicts = []

        with patch(
            "builtins.input",
            return_value="CS102, CS103"
        ):
            result = conflict.add_conflicts(
                "CS101",
                conflicts,
                self.courses
            )

        self.assertEqual(
            result,
            ["CS102", "CS103"]
        )

    def test_add_empty_input(self):
        conflicts = []

        with patch(
            "builtins.input",
            return_value=""
        ), patch("builtins.print") as mock_print:

            result = conflict.add_conflicts(
                "CS101",
                conflicts,
                self.courses
            )

        self.assertEqual(result, [])
        mock_print.assert_any_call(
            "No conflicts added."
        )

    def test_add_self_conflict_skipped(self):
        conflicts = []

        with patch(
            "builtins.input",
            return_value="CS101, CS102"
        ), patch("builtins.print") as mock_print:

            result = conflict.add_conflicts(
                "CS101",
                conflicts,
                self.courses
            )

        self.assertEqual(result, ["CS102"])

        mock_print.assert_any_call(
            "'CS101': a course cannot conflict with itself. Skipped."
        )

    def test_add_nonexistent_course_skipped(self):
        conflicts = []

        with patch(
            "builtins.input",
            return_value="CS999, CS102"
        ), patch("builtins.print") as mock_print:

            result = conflict.add_conflicts(
                "CS101",
                conflicts,
                self.courses
            )

        self.assertEqual(result, ["CS102"])

        mock_print.assert_any_call(
            "Course 'CS999' does not exist. Skipped."
        )

    def test_add_already_present_skipped(self):
        conflicts = ["CS102"]

        with patch(
            "builtins.input",
            return_value="CS102, CS103"
        ), patch("builtins.print") as mock_print:

            result = conflict.add_conflicts(
                "CS101",
                conflicts,
                self.courses
            )

        self.assertEqual(
            result,
            ["CS102", "CS103"]
        )

        mock_print.assert_any_call(
            "'CS102' is already a conflict for this course."
        )

    def test_add_case_insensitive_duplicate_skipped(self):
        conflicts = ["CS102"]

        with patch(
            "builtins.input",
            return_value="cs102"
        ), patch("builtins.print") as mock_print:

            result = conflict.add_conflicts(
                "CS101",
                conflicts,
                self.courses
            )

        self.assertEqual(result, ["CS102"])

        mock_print.assert_any_call(
            "'cs102' is already a conflict for this course."
        )


class TestDeleteConflicts(ConflictTestBase):

    def test_delete_single(self):
        conflicts = ["CS102", "CS103"]

        with patch(
            "builtins.input",
            return_value="CS102"
        ):
            result = conflict.delete_conflicts(
                "CS101",
                conflicts
            )

        self.assertEqual(result, ["CS103"])

    def test_delete_comma_separated_list(self):
        conflicts = ["CS102", "CS103", "CS104"]

        with patch(
            "builtins.input",
            return_value="CS102, CS103"
        ):
            result = conflict.delete_conflicts(
                "CS101",
                conflicts
            )

        self.assertEqual(result, ["CS104"])

    def test_delete_no_conflicts_to_delete(self):
        conflicts = []

        with patch("builtins.print") as mock_print:
            result = conflict.delete_conflicts(
                "CS101",
                conflicts
            )

        self.assertEqual(result, [])

        mock_print.assert_any_call(
            "CS101 has no conflicts to delete."
        )

    def test_delete_not_currently_a_conflict(self):
        conflicts = ["CS102"]

        with patch(
            "builtins.input",
            return_value="CS104"
        ), patch("builtins.print") as mock_print:

            result = conflict.delete_conflicts(
                "CS101",
                conflicts
            )

        self.assertEqual(result, ["CS102"])

        mock_print.assert_any_call(
            "'CS104' is not currently a conflict for this course."
        )

    def test_delete_case_insensitive_match(self):
        conflicts = ["CS102"]

        with patch(
            "builtins.input",
            return_value="cs102"
        ):
            result = conflict.delete_conflicts(
                "CS101",
                conflicts
            )

        self.assertEqual(result, [])


class TestToggleConflicts(ConflictTestBase):
    """toggle_conflicts() removes existing conflicts and adds
    missing valid conflicts."""

    def test_toggle_adds_when_absent(self):
        conflicts = []

        with patch(
            "builtins.input",
            return_value="CS102"
        ), patch("builtins.print") as mock_print:

            result = conflict.toggle_conflicts(
                "CS101",
                conflicts,
                self.courses
            )

        self.assertEqual(result, ["CS102"])

        mock_print.assert_any_call(
            "'CS102' was not a conflict — added."
        )

    def test_toggle_removes_when_present(self):
        conflicts = ["CS102"]

        with patch(
            "builtins.input",
            return_value="CS102"
        ), patch("builtins.print") as mock_print:

            result = conflict.toggle_conflicts(
                "CS101",
                conflicts,
                self.courses
            )

        self.assertEqual(result, [])

        mock_print.assert_any_call(
            "'CS102' was already a conflict — removed."
        )

    def test_toggle_mixed_list_adds_and_removes(self):
        conflicts = ["CS102"]

        with patch(
            "builtins.input",
            return_value="CS102, CS103"
        ):
            result = conflict.toggle_conflicts(
                "CS101",
                conflicts,
                self.courses
            )

        self.assertEqual(result, ["CS103"])

    def test_toggle_single_course_number_not_just_lists(self):
        conflicts = []

        with patch(
            "builtins.input",
            return_value="CS104"
        ):
            result = conflict.toggle_conflicts(
                "CS101",
                conflicts,
                self.courses
            )

        self.assertEqual(result, ["CS104"])

    def test_toggle_self_conflict_skipped(self):
        conflicts = []

        with patch(
            "builtins.input",
            return_value="CS101"
        ), patch("builtins.print") as mock_print:

            result = conflict.toggle_conflicts(
                "CS101",
                conflicts,
                self.courses
            )

        self.assertEqual(result, [])

        mock_print.assert_any_call(
            "'CS101': a course cannot conflict with itself. Skipped."
        )

    def test_toggle_nonexistent_course_skipped(self):
        conflicts = []

        with patch(
            "builtins.input",
            return_value="CS999"
        ), patch("builtins.print") as mock_print:

            result = conflict.toggle_conflicts(
                "CS101",
                conflicts,
                self.courses
            )

        self.assertEqual(result, [])

        mock_print.assert_any_call(
            "Course 'CS999' does not exist. Skipped."
        )

    def test_toggle_empty_input_no_changes(self):
        conflicts = ["CS102"]

        with patch(
            "builtins.input",
            return_value=""
        ), patch("builtins.print") as mock_print:

            result = conflict.toggle_conflicts(
                "CS101",
                conflicts,
                self.courses
            )

        self.assertEqual(result, ["CS102"])

        mock_print.assert_any_call(
            "No changes made."
        )

    def test_toggle_case_insensitive_removal(self):
        conflicts = ["CS102"]

        with patch(
            "builtins.input",
            return_value="cs102"
        ):
            result = conflict.toggle_conflicts(
                "CS101",
                conflicts,
                self.courses
            )

        self.assertEqual(result, [])


class TestConflictsMenu(ConflictTestBase):
    """conflicts_menu() dispatches to add, modify, delete, and view."""

    @patch(f"{MODULE}.add_conflicts")
    def test_dispatches_to_add(self, mock_add):
        mock_add.return_value = ["CS102"]

        with patch(
            "builtins.input",
            side_effect=["add", "done"]
        ):
            result = conflict.conflicts_menu(
                "CS101",
                self.courses
            )

        mock_add.assert_called_once_with(
            "CS101",
            [],
            self.courses
        )

        self.assertEqual(result, ["CS102"])

    @patch(f"{MODULE}.toggle_conflicts")
    def test_dispatches_to_modify(self, mock_toggle):
        mock_toggle.return_value = ["CS103"]

        with patch(
            "builtins.input",
            side_effect=["modify", "done"]
        ):
            result = conflict.conflicts_menu(
                "CS101",
                self.courses
            )

        mock_toggle.assert_called_once_with(
            "CS101",
            [],
            self.courses
        )

        self.assertEqual(result, ["CS103"])

    @patch(f"{MODULE}.delete_conflicts")
    def test_dispatches_to_delete(self, mock_delete):
        mock_delete.return_value = []

        with patch(
            "builtins.input",
            side_effect=["delete", "done"]
        ):
            result = conflict.conflicts_menu(
                "CS101",
                self.courses,
                ["CS102"]
            )

        mock_delete.assert_called_once_with(
            "CS101",
            ["CS102"]
        )

        self.assertEqual(result, [])

    @patch(f"{MODULE}.view_conflicts_list")
    def test_dispatches_to_view_then_continues(
        self,
        mock_view
    ):
        with patch(
            "builtins.input",
            side_effect=["view", "done"]
        ):
            result = conflict.conflicts_menu(
                "CS101",
                self.courses,
                ["CS102"]
            )

        mock_view.assert_called_once_with(
            "CS101",
            ["CS102"]
        )

        self.assertEqual(result, ["CS102"])

    def test_done_returns_immediately(self):
        with patch(
            "builtins.input",
            return_value="done"
        ):
            result = conflict.conflicts_menu(
                "CS101",
                self.courses,
                ["CS102"]
            )

        self.assertEqual(result, ["CS102"])

    def test_invalid_choice_reprompts(self):
        with patch(
            "builtins.input",
            side_effect=["blah", "done"]
        ), patch("builtins.print") as mock_print:

            result = conflict.conflicts_menu(
                "CS101",
                self.courses
            )

        self.assertEqual(result, [])

        mock_print.assert_any_call(
            "Invalid selection."
        )

    @patch(f"{MODULE}.add_conflicts")
    def test_commands_are_case_insensitive(
        self,
        mock_add
    ):
        mock_add.return_value = ["CS102"]

        with patch(
            "builtins.input",
            side_effect=["  ADD  ", "DONE"]
        ):
            result = conflict.conflicts_menu(
                "CS101",
                self.courses
            )

        mock_add.assert_called_once_with(
            "CS101",
            [],
            self.courses
        )

        self.assertEqual(result, ["CS102"])

    def test_multiple_actions_before_done(self):
        with patch(
            "builtins.input",
            side_effect=[
                "add",
                "CS102",
                "modify",
                "CS102",
                "done"
            ]
        ):
            result = conflict.conflicts_menu(
                "CS101",
                self.courses
            )

        self.assertEqual(result, [])

    def test_starts_from_existing_conflicts_without_mutating_original(self):
        original = ["CS102"]

        with patch(
            "builtins.input",
            side_effect=[
                "add",
                "CS103",
                "done"
            ]
        ):
            result = conflict.conflicts_menu(
                "CS101",
                self.courses,
                original
            )

        self.assertEqual(
            result,
            ["CS102", "CS103"]
        )

        self.assertEqual(
            original,
            ["CS102"]
        )


class TestModifyConflicts(ConflictTestBase):
    """modify_conflicts(course, courses) runs the conflict menu and
    persists the result back onto the CourseConfig."""

    def test_persists_result_onto_course(self):
        with patch(
            "builtins.input",
            side_effect=[
                "add",
                "CS102",
                "done"
            ]
        ), patch("builtins.print") as mock_print:

            conflict.modify_conflicts(
                self.course_a,
                self.courses
            )

        self.assertEqual(
            self.course_a.conflicts,
            ["CS102"]
        )

        mock_print.assert_any_call(
            "Conflicts updated successfully"
        )

    def test_done_immediately_leaves_conflicts_unchanged(self):
        self.course_a.conflicts = ["CS102"]

        with patch(
            "builtins.input",
            return_value="done"
        ):
            conflict.modify_conflicts(
                self.course_a,
                self.courses
            )

        self.assertEqual(
            self.course_a.conflicts,
            ["CS102"]
        )


if __name__ == "__main__":
    unittest.main()

