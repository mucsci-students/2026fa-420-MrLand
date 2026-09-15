import unittest 
from unittest.mock import patch, MagicMock
from src.services.lab_service import (
    labs,
    add_lab, 
    get_lab_name, 
    get_lab_capacity, 
    get_lab_features, 
    get_lab_times,
)

MODULE = "src.services.lab_service"

lab_menu = __import__(MODULE, fromlist=["*"])

# helper functions
class test_get_lab_name(unittest.TestCase):
    def setUp(self):
        lab_menu.labs = []

    @patch(f"{MODULE}.find_lab")
    @patch("builtins.input")

    def test_valid_name_returns_stripped_lowercased(self, mock_input, mock_find_lab):
        mock_input.return_value = "  Bio LAB  "
        mock_find_lab.return_value = None

        result = lab_menu.get_lab_name()

        self.assertEqual(result, "bio lab")
        mock_find_lab.assert_called_once_with(lab_menu.labs, "bio lab")

    @patch(f"{MODULE}.find_lab")
    @patch("builtins.input")
    @patch("builtins.print")

    def test_blank_name_recurses_until_valid(self, mock_print, mock_input, mock_find_lab):
        mock_input.side_effect = ["", "   ", "chem lab"]
        mock_find_lab.return_value = None

        result = lab_menu.get_lab_name()

        self.assertEqual(result, "chem lab")
        self.assertEqual(mock_input.call_count, 3)
        mock_print.assert_any_call("Lab Name Cannot Be Blank")

    @patch(f"{MODULE}.find_lab")
    @patch("builtins.input")
    @patch("builtins.print")

    def test_duplicate_name_recurses_until_unique(self, mock_print, mock_input, mock_find_lab):
        mock_input.side_effect = ["chem lab", "physics lab"]
        mock_find_lab.side_effect = [MagicMock(), None]

        result = lab_menu.get_lab_name()

        self.assertEqual(result, "physics lab")
        mock_print.assert_any_call("Lab Name Exists Already")
        self.assertEqual(mock_find_lab.call_count, 2)


class test_get_lab_capacity(unittest.TestCase):
    @patch("builtins.input")

    def test_valid_capacity(self, mock_input):
        mock_input.return_value = "30"

        result = lab_menu.get_lab_capacity()

        self.assertEqual(result, 30)

    @patch("builtins.input")
    @patch("builtins.print")

    def test_non_positive_capacity_recurses(self, mock_print, mock_input):
        mock_input.side_effect = ["0", "-5", "20"]

        result = lab_menu.get_lab_capacity()

        self.assertEqual(result, 20)
        self.assertEqual(mock_input.call_count, 3)
        mock_print.assert_any_call("Capacity Must Be Greater Than 0")

    @patch("builtins.input")
    @patch("builtins.print")

    def test_non_integer_capacity_returns_none(self, mock_print, mock_input):

        mock_input.side_effect = ["abc", "12.5", "20"]

        result = lab_menu.get_lab_capacity()

        self.assertEqual(result, 20)
        self.assertEqual(mock_input.call_count, 3)
        mock_print.assert_any_call("Value Must Be An Integer")


class test_get_lab_features(unittest.TestCase):
    @patch("builtins.input")
    @patch("builtins.print")

    def test_collects_unique_non_empty_features(self, mock_print, mock_input):
        mock_input.side_effect = ["Projector", "", "  ", "Whiteboard", "done"]

        result = lab_menu.get_lab_features()

        self.assertEqual(result, {"Projector", "Whiteboard"})

    @patch("builtins.input")
    def test_immediate_done_returns_empty_set(self, mock_input):
        mock_input.return_value = "done"

        result = lab_menu.get_lab_features()

        self.assertEqual(result, set())

    @patch("builtins.input")
    def test_done_is_case_insensitive(self, mock_input):
        mock_input.side_effect = ["Monitor", "DONE"]

        result = lab_menu.get_lab_features()

        self.assertEqual(result, {"Monitor"})


class Test_get_lab_times(unittest.TestCase):
    @patch("builtins.input")

    def test_choice_n_returns_none(self, mock_input):
        mock_input.return_value = "n"

        result = lab_menu.get_lab_times()

        self.assertIsNone(result)

    @patch("builtins.input")
    @patch("builtins.print")

    def test_invalid_choice_returns_none_with_message(self, mock_print, mock_input):
        mock_input.return_value = "maybe"

        result = lab_menu.get_lab_times()

        self.assertIsNone(result)
        mock_print.assert_any_call("Invalid choice. Using unrestricted availability.")

    @patch("builtins.input")

    def test_choice_y_collects_ranges_per_day(self, mock_input):
        mock_input.side_effect = [
            "y",
            "09:00-10:00", "done",   
            "done",                  
            "13:00-14:00", "14:00-15:00", "done",  
            "done",                   
            "done",                   
        ]

        result = lab_menu.get_lab_times()

        self.assertEqual(
            result,
            {
                "MON": ["09:00-10:00"],
                "WED": ["13:00-14:00", "14:00-15:00"],
            },
        )

    @patch("builtins.input")

    def test_blank_time_range_is_ignored(self, mock_input):
        mock_input.side_effect = [
            "y",
            "", "09:00-10:00", "done",  
            "done", "done", "done", "done",  
        ]

        result = lab_menu.get_lab_times()

        self.assertEqual(result, {"MON": ["09:00-10:00"]})

# add lab
class test_add_lab(unittest.TestCase):
    def setUp(self):
        lab_menu.labs = []

    @patch(f"{MODULE}.LabConfig")
    @patch(f"{MODULE}.get_lab_times")
    @patch(f"{MODULE}.get_lab_features")
    @patch(f"{MODULE}.get_lab_capacity")
    @patch(f"{MODULE}.get_lab_name")
    @patch("builtins.print")

    def test_add_lab_success(
        self,
        mock_print,
        mock_get_name,
        mock_get_capacity,
        mock_get_features,
        mock_get_times,
        mock_lab_config_cls,
    ):
        mock_get_name.return_value = "chem lab"
        mock_get_capacity.return_value = 25
        mock_get_features.return_value = mock_get_features
        mock_get_times.return_value = None
        mock_lab_instance = MagicMock()
        mock_lab_config_cls.return_value = mock_lab_instance

        lab_menu.add_lab()

        mock_lab_config_cls.assert_called_once_with(
            name="chem lab",
            capacity=25,
            features=mock_get_features,
            times=None,
        )
        self.assertIn(mock_lab_instance, lab_menu.labs)
        mock_print.assert_any_call("'chem lab' Added")
        mock_get_features.assert_called_once()

    @patch(f"{MODULE}.LabConfig")
    @patch(f"{MODULE}.get_lab_times")
    @patch(f"{MODULE}.get_lab_features")
    @patch(f"{MODULE}.get_lab_capacity")
    @patch(f"{MODULE}.get_lab_name")
    @patch("builtins.print")

    def test_add_lab_handles_lab_config_exception(
        self,
        mock_print,
        mock_get_name,
        mock_get_capacity,
        mock_get_features,
        mock_get_times,
        mock_lab_config_cls,
    ):
        mock_get_name.return_value = "bad lab"
        mock_get_capacity.return_value = 10
        mock_get_times.return_value = None
        mock_lab_config_cls.side_effect = ValueError("boom")

        lab_menu.add_lab()

        self.assertEqual(lab_menu.labs, [])
        mock_print.assert_any_call("Failed To Create Lab: boom")


class test_view_labs(unittest.TestCase):
    def setUp(self):
        lab_menu.labs = []

    @patch("builtins.print")
    def test_view_labs_empty(self, mock_print):
        lab_menu.view_labs()

        mock_print.assert_called_once_with("\nNo Lab Found")

    @patch("builtins.print")
    def test_view_labs_with_features_and_unrestricted_times(self, mock_print):
        lab = MagicMock()
        lab.name = "chem lab"
        lab.capacity = 20
        lab.features = {"Projector", "Whiteboard"}
        lab.times = None
        lab_menu.labs = [lab]

        lab_menu.view_labs()

        mock_print.assert_any_call("\n1. chem lab")
        mock_print.assert_any_call("Capacity: 20")
        mock_print.assert_any_call("Features: Projector, Whiteboard")
        mock_print.assert_any_call("Availability: Unrestricted")

    @patch("builtins.print")

    def test_view_labs_no_features_and_scheduled_times(self, mock_print):
        lab = MagicMock()
        lab.name = "physics lab"
        lab.capacity = 15
        lab.features = set()
        lab.times = {"MON": ["09:00-10:00"]}
        lab_menu.labs = [lab]

        lab_menu.view_labs()

        mock_print.assert_any_call("Features: None")
        mock_print.assert_any_call("Availability: ")
        mock_print.assert_any_call(" MON: ['09:00-10:00']")

    @patch("builtins.print")
    def test_view_labs_numbers_multiple_labs_sequentially(self, mock_print):
        lab1 = MagicMock(name="lab1", capacity=1, features=set(), times=None)
        lab1.name = "lab one"
        lab2 = MagicMock(name="lab2", capacity=2, features=set(), times=None)
        lab2.name = "lab two"
        lab_menu.labs = [lab1, lab2]

        lab_menu.view_labs()

        mock_print.assert_any_call("\n1. lab one")
        mock_print.assert_any_call("\n2. lab two")


if __name__ == "__main__":
    unittest.main()