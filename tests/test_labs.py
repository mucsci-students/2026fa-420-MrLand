import unittest 
from unittest.mock import patch, MagicMock, call
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

class test_modify_lab(unittest.TestCase):
    def setUp(self):
        lab_menu.labs = []
        
    @patch("builtins.print")

    def test_no_labs_prints_message_and_returns(self, mock_print):
        lab_menu.modify_lab()
 
        mock_print.assert_called_once_with("\nNo labs found.")
 
    @patch(f"{MODULE}.view_labs")
    @patch("builtins.input")
    @patch("builtins.print")

    def test_non_integer_index_prints_error(self, mock_print, mock_input, mock_view_labs):
        lab_menu.labs = [MagicMock(name="lab")]
        mock_input.return_value = "abc"
 
        lab_menu.modify_lab()
 
        mock_view_labs.assert_called_once()
        mock_print.assert_any_call("Enter Valid Number.")
 
    @patch(f"{MODULE}.view_labs")
    @patch("builtins.input")
    @patch("builtins.print")

    def test_out_of_range_index_prints_error(self, mock_print, mock_input, mock_view_labs):
        lab_menu.labs = [MagicMock()]
        mock_input.return_value = "5"  
 
        lab_menu.modify_lab()
 
        mock_print.assert_any_call("Invalid Selection.")
 
    @patch(f"{MODULE}.view_labs")
    @patch("builtins.input")
    @patch("builtins.print")

    def test_zero_index_is_invalid(self, mock_print, mock_input, mock_view_labs):
        lab_menu.labs = [MagicMock()]
        mock_input.return_value = "0"  
 
        lab_menu.modify_lab()
 
        mock_print.assert_any_call("Invalid Selection.")
  
    @patch(f"{MODULE}.get_lab_name")
    @patch(f"{MODULE}.view_labs")
    @patch("builtins.input")
    @patch("builtins.print")

    def test_choice_1_assigns_result_of_get_lab_name(self, mock_print, mock_input, mock_view_labs, mock_get_lab_name):
        lab = MagicMock()
        lab.name = "old name"
        lab_menu.labs = [lab]
        mock_input.side_effect = ["1", "1"]
        mock_get_lab_name.return_value = "new name"
 
        lab_menu.modify_lab()
 
        mock_get_lab_name.assert_called_once()
        self.assertEqual(lab.name, "new name")
        mock_print.assert_any_call("Name Updated to 'new name'")
  
    @patch(f"{MODULE}.get_lab_capacity")
    @patch(f"{MODULE}.view_labs")
    @patch("builtins.input")
    @patch("builtins.print")

    def test_choice_2_assigns_result_of_get_lab_capacity(
        self, mock_print, mock_input, mock_view_labs, mock_get_lab_capacity
    ):
        lab = MagicMock()
        lab.capacity = 10
        lab_menu.labs = [lab]
        mock_input.side_effect = ["1", "2"]
        mock_get_lab_capacity.return_value = 50
 
        lab_menu.modify_lab()
 
        mock_get_lab_capacity.assert_called_once()
        self.assertEqual(lab.capacity, 50)
        mock_print.assert_any_call("Capacity Updated to '50'")
  
    @patch(f"{MODULE}.view_labs")
    @patch("builtins.input")
    @patch("builtins.print")

    def test_choice_3_collects_and_persists_features(self, mock_print, mock_input, mock_view_labs):
        lab = MagicMock()
        lab.features = {"Old Feature"}
        lab_menu.labs = [lab]
        mock_input.side_effect = ["1", "3", "Projector", "", "done"]
 
        lab_menu.modify_lab()
 
        self.assertEqual(lab.features, {"Projector"})
  
    @patch(f"{MODULE}.get_lab_times")
    @patch(f"{MODULE}.view_labs")
    @patch("builtins.input")
    @patch("builtins.print")

    def test_choice_4_calls_get_lab_times_and_persists(
        self, mock_print, mock_input, mock_view_labs, mock_get_lab_times
    ):
        lab = MagicMock()
        lab.times = None
        lab_menu.labs = [lab]
        mock_input.side_effect = ["1", "4"]
        mock_get_lab_times.return_value = {"MON": ["09:00-10:00"]}
 
        lab_menu.modify_lab()
 
        mock_get_lab_times.assert_called_once()
        self.assertEqual(lab.times, {"MON": ["09:00-10:00"]})

    @patch(f"{MODULE}.view_labs")
    @patch("builtins.input")
    @patch("builtins.print")
    
    def test_choice_5_cancels(self, mock_print, mock_input, mock_view_labs):
        lab_menu.labs = [MagicMock()]
        mock_input.side_effect = ["1", "5"]
 
        lab_menu.modify_lab()
 
        mock_print.assert_any_call("Modification Cancelled.")
 
    @patch(f"{MODULE}.view_labs")
    @patch("builtins.input")
    @patch("builtins.print")

    def test_invalid_choice_prints_error(self, mock_print, mock_input, mock_view_labs):
        lab_menu.labs = [MagicMock()]
        mock_input.side_effect = ["1", "9"]
 
        lab_menu.modify_lab()
 
        mock_print.assert_any_call("Invalid Option.")

class test_delete_lab(unittest.TestCase):
    def setUp(self):
        lab_menu.labs = []
 
    @patch("builtins.print")

    def test_no_labs_prints_message_and_returns(self, mock_print):
        lab_menu.delete_lab()
 
        mock_print.assert_called_once_with("\nNo Labs Found.")
 
    @patch(f"{MODULE}.view_labs")
    @patch("builtins.input")
    @patch("builtins.print")

    def test_non_integer_index_prints_error(self, mock_print, mock_input, mock_view_labs):
        lab_menu.labs = [MagicMock()]
        mock_input.return_value = "abc"
 
        lab_menu.delete_lab()
 
        mock_view_labs.assert_called_once()
        mock_print.assert_any_call("Enter Valid Number.")
        self.assertEqual(len(lab_menu.labs), 1)
 
    @patch(f"{MODULE}.view_labs")
    @patch("builtins.input")
    @patch("builtins.print")

    def test_out_of_range_index_prints_error(self, mock_print, mock_input, mock_view_labs):
        lab_menu.labs = [MagicMock()]
        mock_input.return_value = "5"
 
        lab_menu.delete_lab()
 
        mock_print.assert_any_call("Invalid Selection.")
        self.assertEqual(len(lab_menu.labs), 1)
 
    @patch(f"{MODULE}.view_labs")
    @patch("builtins.input")
    @patch("builtins.print")

    def test_zero_index_is_invalid(self, mock_print, mock_input, mock_view_labs):
        lab_menu.labs = [MagicMock()]
        mock_input.return_value = "0"  
 
        lab_menu.delete_lab()
 
        mock_print.assert_any_call("Invalid Selection.")
        self.assertEqual(len(lab_menu.labs), 1)
 
    @patch(f"{MODULE}.view_labs")
    @patch("builtins.input")
    @patch("builtins.print")

    def test_confirm_yes_deletes_lab(self, mock_print, mock_input, mock_view_labs):
        lab = MagicMock()
        lab.name = "chem lab"
        lab_menu.labs = [lab]
        mock_input.side_effect = ["1", "y"]
 
        lab_menu.delete_lab()
 
        self.assertEqual(lab_menu.labs, [])
        mock_print.assert_any_call("Deleted 'chem lab'.")
 
    @patch(f"{MODULE}.view_labs")
    @patch("builtins.input")
    @patch("builtins.print")

    def test_confirm_yes_is_case_insensitive_and_trims_whitespace(self, mock_print, mock_input, mock_view_labs):
        lab = MagicMock()
        lab.name = "chem lab"
        lab_menu.labs = [lab]
        mock_input.side_effect = ["1", "  Y  "]
 
        lab_menu.delete_lab()
 
        self.assertEqual(lab_menu.labs, [])
        mock_print.assert_any_call("Deleted 'chem lab'.")
 
    @patch(f"{MODULE}.view_labs")
    @patch("builtins.input")
    @patch("builtins.print")

    def test_confirm_no_cancels_deletion(self, mock_print, mock_input, mock_view_labs):
        lab = MagicMock()
        lab.name = "chem lab"
        lab_menu.labs = [lab]
        mock_input.side_effect = ["1", "n"]
 
        lab_menu.delete_lab()
 
        self.assertEqual(lab_menu.labs, [lab])
        mock_print.assert_any_call("Deletion Cancelled.")
 
    @patch(f"{MODULE}.view_labs")
    @patch("builtins.input")
    @patch("builtins.print")

    def test_confirm_anything_other_than_y_cancels(self, mock_print, mock_input, mock_view_labs):
        lab = MagicMock()
        lab.name = "chem lab"
        lab_menu.labs = [lab]
        mock_input.side_effect = ["1", ""]
 
        lab_menu.delete_lab()
 
        self.assertEqual(lab_menu.labs, [lab])
        mock_print.assert_any_call("Deletion Cancelled.")
 
    @patch(f"{MODULE}.view_labs")
    @patch("builtins.input")
    @patch("builtins.print")

    def test_deletes_correct_lab_from_multiple(self, mock_print, mock_input, mock_view_labs):
        lab1, lab2, lab3 = MagicMock(), MagicMock(), MagicMock()
        lab1.name, lab2.name, lab3.name = "lab one", "lab two", "lab three"
        lab_menu.labs = [lab1, lab2, lab3]
        mock_input.side_effect = ["2", "y"]  
 
        lab_menu.delete_lab()
 
        self.assertEqual(lab_menu.labs, [lab1, lab3])
        mock_print.assert_any_call("Deleted 'lab two'.")


if __name__ == "__main__":
    unittest.main()