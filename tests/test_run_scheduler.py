# test_run_scheduler.py

from unittest.mock import MagicMock, patch

import pytest

import run_scheduler
from schedule_result import ScheduleResult


def make_schedule_instance(course="CS101", faculty="Dr. Smith", room="Room1", lab=None):
    instance = MagicMock()
    instance.course = course
    instance.faculty = faculty
    instance.room = room
    instance.lab = lab
    return instance


def make_audit(is_valid):
    audit = MagicMock()
    audit.is_valid = is_valid
    return audit


# ---- confirm_yes_no() -----------------------------------------------------


def test_confirm_yes_no_accepts_yes(monkeypatch):
    monkeypatch.setattr("builtins.input", lambda _: "yes")
    assert run_scheduler.confirm_yes_no("Continue?") is True


def test_confirm_yes_no_accepts_no(monkeypatch):
    monkeypatch.setattr("builtins.input", lambda _: "no")
    assert run_scheduler.confirm_yes_no("Continue?") is False


def test_confirm_yes_no_reprompts_on_invalid(monkeypatch):
    answers = iter(["maybe", "y"])
    monkeypatch.setattr("builtins.input", lambda _: next(answers))
    assert run_scheduler.confirm_yes_no("Continue?") is True


# ---- run_scheduler(): missing / bad config -------------------------------


def test_run_scheduler_missing_config(monkeypatch, capsys):
    monkeypatch.setattr("builtins.input", lambda _: "nonexistent")
    schedules = []

    with patch("run_scheduler.config_exists", return_value=False) as mock_exists, \
         patch("run_scheduler.config_load") as mock_load:
        run_scheduler.run_scheduler(schedules)

    mock_exists.assert_called_once_with("nonexistent")
    mock_load.assert_not_called()
    assert "No saved configuration named 'nonexistent'" in capsys.readouterr().out
    assert schedules == []


def test_run_scheduler_load_raises(monkeypatch, capsys):
    monkeypatch.setattr("builtins.input", lambda _: "broken_config")
    schedules = []

    with patch("run_scheduler.config_exists", return_value=True), \
         patch("run_scheduler.config_load", side_effect=ValueError("bad json")):
        run_scheduler.run_scheduler(schedules)

    out = capsys.readouterr().out
    assert "Failed to load configuration 'broken_config'" in out
    assert "bad json" in out
    assert schedules == []


# ---- run_scheduler(): Scheduler construction fails ------------------------


def test_run_scheduler_scheduler_init_fails(monkeypatch, capsys):
    monkeypatch.setattr("builtins.input", lambda _: "good_config")
    fake_config = MagicMock()
    schedules = []

    with patch("run_scheduler.config_exists", return_value=True), \
         patch("run_scheduler.config_load", return_value=fake_config), \
         patch("run_scheduler.Scheduler", side_effect=RuntimeError("z3 init failed")):
        run_scheduler.run_scheduler(schedules)

    out = capsys.readouterr().out
    assert "Error occurred while starting the scheduler" in out
    assert "z3 init failed" in out
    assert schedules == []


# ---- run_scheduler(): no valid schedule found -----------------------------


def test_run_scheduler_no_valid_schedule(monkeypatch, capsys):
    monkeypatch.setattr("builtins.input", lambda _: "tight_config")
    fake_config = MagicMock()
    fake_config.limit = 5
    schedules = []

    mock_scheduler_instance = MagicMock()
    mock_scheduler_instance.get_models.return_value = iter([])

    diagnosis = MagicMock()
    diagnosis.status = "UNSAT"
    finding = MagicMock()
    finding.message = "faculty double-booked"
    suggestion = MagicMock()
    suggestion.message = "widen faculty availability"
    diagnosis.conflicting_constraints = [finding]
    diagnosis.relaxation_suggestions = [suggestion]
    mock_scheduler_instance.diagnose.return_value = diagnosis

    with patch("run_scheduler.config_exists", return_value=True), \
         patch("run_scheduler.config_load", return_value=fake_config), \
         patch("run_scheduler.Scheduler", return_value=mock_scheduler_instance):
        run_scheduler.run_scheduler(schedules)

    out = capsys.readouterr().out
    assert "No valid schedule could be generated" in out
    assert "UNSAT" in out
    assert "faculty double-booked" in out
    assert "widen faculty availability" in out
    assert schedules == []


# ---- run_scheduler(): success, respects limit ------------------------------


def test_run_scheduler_success_stops_at_limit(monkeypatch, capsys):
    monkeypatch.setattr("builtins.input", lambda _: "good_config")
    fake_config = MagicMock()
    fake_config.limit = 2
    schedules = []

    all_models = [[make_schedule_instance()] for _ in range(5)]

    mock_scheduler_instance = MagicMock()
    mock_scheduler_instance.get_models.return_value = iter(all_models)
    mock_scheduler_instance.audit_schedule.return_value = make_audit(True)

    with patch("run_scheduler.config_exists", return_value=True), \
         patch("run_scheduler.config_load", return_value=fake_config), \
         patch("run_scheduler.Scheduler", return_value=mock_scheduler_instance):
        run_scheduler.run_scheduler(schedules)

    out = capsys.readouterr().out
    assert "Generated 2 schedule(s), 2 valid." in out
    assert len(schedules) == 2
    assert all(isinstance(r, ScheduleResult) for r in schedules)
    assert all(r.config_name == "good_config" for r in schedules)
    assert mock_scheduler_instance.audit_schedule.call_count == 2


def test_run_scheduler_success_counts_invalid_schedules(monkeypatch, capsys):
    monkeypatch.setattr("builtins.input", lambda _: "good_config")
    fake_config = MagicMock()
    fake_config.limit = 3
    schedules = []

    all_models = [[make_schedule_instance()] for _ in range(3)]

    mock_scheduler_instance = MagicMock()
    mock_scheduler_instance.get_models.return_value = iter(all_models)
    mock_scheduler_instance.audit_schedule.side_effect = [
        make_audit(True), make_audit(False), make_audit(True)
    ]

    with patch("run_scheduler.config_exists", return_value=True), \
         patch("run_scheduler.config_load", return_value=fake_config), \
         patch("run_scheduler.Scheduler", return_value=mock_scheduler_instance):
        run_scheduler.run_scheduler(schedules)

    out = capsys.readouterr().out
    assert "Generated 3 schedule(s), 2 valid." in out
    assert len(schedules) == 3


def test_run_scheduler_appends_to_existing_schedules_list(monkeypatch, capsys):
    """schedules is passed in by the caller and should accumulate across
    multiple runs instead of being reset each time."""
    monkeypatch.setattr("builtins.input", lambda _: "good_config")
    fake_config = MagicMock()
    fake_config.limit = 1
    schedules = [ScheduleResult(config_name="earlier_config", schedule=[make_schedule_instance()])]

    mock_scheduler_instance = MagicMock()
    mock_scheduler_instance.get_models.return_value = iter([[make_schedule_instance()]])
    mock_scheduler_instance.audit_schedule.return_value = make_audit(True)

    with patch("run_scheduler.config_exists", return_value=True), \
         patch("run_scheduler.config_load", return_value=fake_config), \
         patch("run_scheduler.Scheduler", return_value=mock_scheduler_instance):
        run_scheduler.run_scheduler(schedules)

    assert len(schedules) == 2
    assert schedules[0].config_name == "earlier_config"
    assert schedules[1].config_name == "good_config"