# test_run_scheduler.py

from unittest.mock import MagicMock, patch

import pytest

import run_scheduler


@pytest.fixture(autouse=True)
def reset_generated_schedules():
    """Ensure the module-level schedule list doesn't leak state between tests."""
    run_scheduler.generated_schedules.clear()
    yield
    run_scheduler.generated_schedules.clear()


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
    assert run_scheduler.generated_schedules == []


def test_run_scheduler_load_raises(monkeypatch, capsys):
    monkeypatch.setattr("builtins.input", lambda _: "broken_config")

    with patch("run_scheduler.config_exists", return_value=True), \
         patch("run_scheduler.config_load", side_effect=ValueError("bad json")):
        run_scheduler.run_scheduler()

    out = capsys.readouterr().out
    assert "Failed to load configuration 'broken_config'" in out
    assert "bad json" in out
    assert run_scheduler.generated_schedules == []


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
    assert run_scheduler.generated_schedules == []


# ---- run_scheduler(): no valid schedule found -----------------------------


def test_run_scheduler_no_valid_schedule(monkeypatch, capsys):
    monkeypatch.setattr("builtins.input", lambda _: "tight_config")
    fake_config = MagicMock()

    mock_scheduler_instance = MagicMock()
    mock_scheduler_instance.get_models.return_value = iter([])  # next(..., None) -> None

    mock_diagnosis = MagicMock()
    mock_diagnosis.status = "INFEASIBLE"
    finding = MagicMock()
    finding.message = "Room1 double-booked MON 9:00"
    mock_diagnosis.conflicting_constraints = [finding]
    suggestion = MagicMock()
    suggestion.message = "Remove one MON 9:00 section"
    mock_diagnosis.relaxation_suggestions = [suggestion]
    mock_scheduler_instance.diagnose.return_value = mock_diagnosis

    with patch("run_scheduler.config_exists", return_value=True), \
         patch("run_scheduler.config_load", return_value=fake_config), \
         patch("run_scheduler.Scheduler", return_value=mock_scheduler_instance):
        run_scheduler.run_scheduler()

    out = capsys.readouterr().out
    assert "No valid schedule could be generated" in out
    assert "INFEASIBLE" in out
    assert "Room1 double-booked MON 9:00" in out
    assert "Remove one MON 9:00 section" in out
    assert run_scheduler.generated_schedules == []


# ---- run_scheduler(): success path -----------------------------------------


def test_run_scheduler_success(monkeypatch, capsys):
    monkeypatch.setattr("builtins.input", lambda _: "valid_config")
    fake_config = MagicMock()

    schedule = [make_schedule_instance(course="CS101", faculty="Dr. Smith", room="Room1", lab=None)]

    mock_scheduler_instance = MagicMock()
    mock_scheduler_instance.get_models.return_value = iter([schedule])
    mock_audit = MagicMock()
    mock_audit.is_valid = True
    mock_scheduler_instance.audit_schedule.return_value = mock_audit

    with patch("run_scheduler.config_exists", return_value=True), \
         patch("run_scheduler.config_load", return_value=fake_config), \
         patch("run_scheduler.Scheduler", return_value=mock_scheduler_instance):
        run_scheduler.run_scheduler()

    out = capsys.readouterr().out
    assert "Scheduler ran successfully." in out
    assert "Schedule valid: True" in out
    assert "CS101: Dr. Smith, room=Room1, lab=None" in out

    mock_scheduler_instance.audit_schedule.assert_called_once_with(schedule)
    assert run_scheduler.generated_schedules == [schedule]


# ---- view_schedules() ------------------------------------------------------


def test_view_schedules_empty(capsys):
    run_scheduler.generated_schedules.clear()
    run_scheduler.view_schedules()
    assert "Configuration has no saved schedules" in capsys.readouterr().out


def test_view_schedules_prints_all(capsys):
    schedule1 = [make_schedule_instance(course="CS101")]
    schedule2 = [make_schedule_instance(course="CS202", faculty="Dr. Lee", room="Room2", lab="LabA")]
    run_scheduler.generated_schedules.extend([schedule1, schedule2])

    run_scheduler.view_schedules()
    out = capsys.readouterr().out

    assert "Schedule 1:" in out
    assert "CS101" in out
    assert "Schedule 2:" in out
    assert "CS202: Dr. Lee, room=Room2, lab=LabA" in out


# ---- confirm_yes_no() -------------------------------------------------------


@pytest.mark.parametrize("response, expected", [("yes", True), ("y", True), ("no", False), ("n", False)])
def test_confirm_yes_no_valid(monkeypatch, response, expected):
    monkeypatch.setattr("builtins.input", lambda _: response)
    assert run_scheduler.confirm_yes_no("Continue?") == expected


def test_confirm_yes_no_reprompts_on_invalid(monkeypatch, capsys):
    responses = iter(["maybe", "yes"])
    monkeypatch.setattr("builtins.input", lambda _: next(responses))
    assert run_scheduler.confirm_yes_no("Continue?") is True
    assert "Please enter yes or no." in capsys.readouterr().out


# ---- run_scheduler(): input handling ---------------------------------------


def test_run_scheduler_strips_whitespace_from_config_name(monkeypatch):
    monkeypatch.setattr("builtins.input", lambda _: "  padded_name  ")

    with patch("run_scheduler.config_exists", return_value=False) as mock_exists:
        run_scheduler.run_scheduler()

    # confirms leading/trailing whitespace is stripped before lookup
    mock_exists.assert_called_once_with("padded_name")


def test_run_scheduler_empty_config_name(monkeypatch, capsys):
    monkeypatch.setattr("builtins.input", lambda _: "   ")

    with patch("run_scheduler.config_exists", return_value=False) as mock_exists:
        run_scheduler.run_scheduler()

    mock_exists.assert_called_once_with("")
    assert "No saved configuration named ''" in capsys.readouterr().out


# ---- run_scheduler(): get_models() raises mid-search ------------------------


def test_run_scheduler_get_models_raises(monkeypatch, capsys):
    monkeypatch.setattr("builtins.input", lambda _: "flaky_config")
    fake_config = MagicMock()

    mock_scheduler_instance = MagicMock()
    mock_scheduler_instance.get_models.side_effect = RuntimeError("z3 solver crashed")

    with patch("run_scheduler.config_exists", return_value=True), \
         patch("run_scheduler.config_load", return_value=fake_config), \
         patch("run_scheduler.Scheduler", return_value=mock_scheduler_instance):
        with pytest.raises(RuntimeError, match="z3 solver crashed"):
            run_scheduler.run_scheduler()

    # nothing should have been recorded since the run never completed
    assert run_scheduler.generated_schedules == []


# ---- run_scheduler(): empty-but-valid schedule -------------------------------


def test_run_scheduler_empty_schedule_is_still_success(monkeypatch, capsys):
    """A schedule with zero course instances (e.g. an empty config) is still
    a valid result distinct from 'no schedule found' (None)."""
    monkeypatch.setattr("builtins.input", lambda _: "trivial_config")
    fake_config = MagicMock()

    empty_schedule = []
    mock_scheduler_instance = MagicMock()
    mock_scheduler_instance.get_models.return_value = iter([empty_schedule])
    mock_audit = MagicMock()
    mock_audit.is_valid = True
    mock_scheduler_instance.audit_schedule.return_value = mock_audit

    with patch("run_scheduler.config_exists", return_value=True), \
         patch("run_scheduler.config_load", return_value=fake_config), \
         patch("run_scheduler.Scheduler", return_value=mock_scheduler_instance):
        run_scheduler.run_scheduler()

    out = capsys.readouterr().out
    assert "Scheduler ran successfully." in out
    assert run_scheduler.generated_schedules == [empty_schedule]


def test_run_scheduler_audit_reports_invalid(monkeypatch, capsys):
    """A schedule can come back from get_models() but still fail audit -
    make sure that's surfaced accurately rather than assumed valid."""
    monkeypatch.setattr("builtins.input", lambda _: "sketchy_config")
    fake_config = MagicMock()

    schedule = [make_schedule_instance()]
    mock_scheduler_instance = MagicMock()
    mock_scheduler_instance.get_models.return_value = iter([schedule])
    mock_audit = MagicMock()
    mock_audit.is_valid = False
    mock_scheduler_instance.audit_schedule.return_value = mock_audit

    with patch("run_scheduler.config_exists", return_value=True), \
         patch("run_scheduler.config_load", return_value=fake_config), \
         patch("run_scheduler.Scheduler", return_value=mock_scheduler_instance):
        run_scheduler.run_scheduler()

    out = capsys.readouterr().out
    assert "Schedule valid: False" in out
    # still recorded even though invalid - matches current run_scheduler() behavior
    assert run_scheduler.generated_schedules == [schedule]


# ---- run_scheduler(): repeated calls accumulate state ------------------------


def test_run_scheduler_multiple_runs_accumulate(monkeypatch):
    fake_config = MagicMock()
    schedule_a = [make_schedule_instance(course="A")]
    schedule_b = [make_schedule_instance(course="B")]

    names = iter(["config_a", "config_b"])
    monkeypatch.setattr("builtins.input", lambda _: next(names))

    def make_mock_scheduler(schedule):
        mock = MagicMock()
        mock.get_models.return_value = iter([schedule])
        mock.audit_schedule.return_value = MagicMock(is_valid=True)
        return mock

    schedulers = iter([make_mock_scheduler(schedule_a), make_mock_scheduler(schedule_b)])

    with patch("run_scheduler.config_exists", return_value=True), \
         patch("run_scheduler.config_load", return_value=fake_config), \
         patch("run_scheduler.Scheduler", side_effect=lambda cfg: next(schedulers)):
        run_scheduler.run_scheduler()
        run_scheduler.run_scheduler()

    assert run_scheduler.generated_schedules == [schedule_a, schedule_b]


# ---- run_scheduler(): diagnosis with no findings -----------------------------


def test_run_scheduler_no_schedule_empty_diagnosis(monkeypatch, capsys):
    """diagnose() might return no specific conflicts/suggestions - make sure
    that doesn't crash the print loop."""
    monkeypatch.setattr("builtins.input", lambda _: "unsolvable_config")
    fake_config = MagicMock()

    mock_scheduler_instance = MagicMock()
    mock_scheduler_instance.get_models.return_value = iter([])
    mock_diagnosis = MagicMock()
    mock_diagnosis.status = "UNKNOWN"
    mock_diagnosis.conflicting_constraints = []
    mock_diagnosis.relaxation_suggestions = []
    mock_scheduler_instance.diagnose.return_value = mock_diagnosis

    with patch("run_scheduler.config_exists", return_value=True), \
         patch("run_scheduler.config_load", return_value=fake_config), \
         patch("run_scheduler.Scheduler", return_value=mock_scheduler_instance):
        run_scheduler.run_scheduler()

    out = capsys.readouterr().out
    assert "No valid schedule could be generated" in out
    assert "Status: UNKNOWN" in out
    assert run_scheduler.generated_schedules == []


# ---- view_schedules(): schedule with no instances -----------------------------


def test_view_schedules_handles_empty_schedule_entry(capsys):
    run_scheduler.generated_schedules.clear()
    run_scheduler.generated_schedules.append([])  # a recorded but empty schedule

    run_scheduler.view_schedules()
    out = capsys.readouterr().out

    assert "Schedule 1:" in out