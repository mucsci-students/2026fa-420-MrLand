# test_run_scheduler.py

from unittest.mock import MagicMock, patch

import pytest

import run_scheduler
from config_state import state


@pytest.fixture(autouse=True)
def reset_state_schedules():
    """Ensure the shared schedule list doesn't leak state between tests."""
    state.schedules.clear()
    yield
    state.schedules.clear()


def make_schedule_instance(course="CS101", faculty="Dr. Smith", room="Room1", lab=None):
    instance = MagicMock()
    instance.course = course
    instance.faculty = faculty
    instance.room = room
    instance.lab = lab
    return instance


# ---- run_scheduler(): missing / bad config -------------------------------


def test_run_scheduler_missing_config(monkeypatch, capsys):
    monkeypatch.setattr("builtins.input", lambda _: "nonexistent")

    with patch("run_scheduler.config_exists", return_value=False) as mock_exists, \
         patch("run_scheduler.config_load") as mock_load:
        run_scheduler.run_scheduler()

    mock_exists.assert_called_once_with("nonexistent")
    mock_load.assert_not_called()
    assert "No saved configuration named 'nonexistent'" in capsys.readouterr().out
    assert state.schedules == []


def test_run_scheduler_load_raises(monkeypatch, capsys):
    monkeypatch.setattr("builtins.input", lambda _: "broken_config")

    with patch("run_scheduler.config_exists", return_value=True), \
         patch("run_scheduler.config_load", side_effect=ValueError("bad json")):
        run_scheduler.run_scheduler()

    out = capsys.readouterr().out
    assert "Failed to load configuration 'broken_config'" in out
    assert "bad json" in out
    assert state.schedules == []


# ---- run_scheduler(): Scheduler construction fails ------------------------


def test_run_scheduler_scheduler_init_fails(monkeypatch, capsys):
    monkeypatch.setattr("builtins.input", lambda _: "good_config")
    fake_config = MagicMock()

    with patch("run_scheduler.config_exists", return_value=True), \
         patch("run_scheduler.config_load", return_value=fake_config), \
         patch("run_scheduler.Scheduler", side_effect=RuntimeError("z3 init failed")):
        run_scheduler.run_scheduler()

    out = capsys.readouterr().out
    assert "Error occurred while starting the scheduler" in out
    assert "z3 init failed" in out
    assert state.schedules == []


# ---- run_scheduler(): no valid schedule found -----------------------------


def test_run_scheduler_no_valid_schedule(monkeypatch, capsys):
    monkeypatch.setattr("builtins.input", lambda _: "tight_config")
    fake_config = MagicMock()

    mock_scheduler_instance = MagicMock()
    mock_scheduler_instance.get_models.return_value = iter([])  # next(..., None) -> None