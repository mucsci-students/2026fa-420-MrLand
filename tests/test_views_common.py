from unittest.mock import Mock, patch

import pytest

from src.views.common import parse_whole_number, run_crud_mutation


@pytest.mark.parametrize(("value", "expected"), [(4, 4), (4.0, 4), ("4", 4)])
def test_parse_whole_number_accepts_integer_values(value, expected):
    assert parse_whole_number(value, "Enter a whole number.") == expected


@pytest.mark.parametrize("value", [None, 2.5, "invalid"])
def test_parse_whole_number_rejects_invalid_values(value):
    with pytest.raises(ValueError, match="Enter a whole number."):
        parse_whole_number(value, "Enter a whole number.")


def test_run_crud_mutation_reports_validation_errors():
    mutation = Mock(side_effect=ValueError("Invalid value."))

    with patch("src.views.common.ui.notify") as notify:
        assert not run_crud_mutation(None, mutation)

    notify.assert_called_once_with("Invalid value.", type="negative")


def test_run_crud_mutation_preserves_rejected_changes():
    mutation = Mock()
    on_change = Mock(return_value=False)

    assert not run_crud_mutation(on_change, mutation)

    on_change.assert_called_once_with(mutation)
    mutation.assert_not_called()
