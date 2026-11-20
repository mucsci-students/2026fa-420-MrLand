import io
import json
import zipfile
from types import SimpleNamespace

import pytest

from src.models.schedule_files import records_to_csv
from src.models.schedule_result import ScheduleResult
from src.models.schedule_viewer_model import ScheduleEntry, ScheduleViewerModel


def _record(course="CS 101"):
    return {
        "course": course,
        "faculty": "Dr. Smith",
        "room": "Room 1",
        "lab": "",
        "times": "MON 09:00-09:50",
    }


def test_selection_and_empty_viewer_behavior():
    model = ScheduleViewerModel()

    assert model.entries == []
    assert model.current is None
    assert model.has_generated_schedules is False

    model.select(20)
    assert model.selected_index == 0


def test_set_generated_is_change_sensitive_and_selects_first_entry():
    model = ScheduleViewerModel()
    first = ScheduleResult(
        config_name="fall",
        schedule=[SimpleNamespace(course="CS 101", faculty="Dr. Smith", room="Room 1", lab=None, time="MON 09:00-09:50")],
    )

    assert model.set_generated([first]) is True
    assert model.has_generated_schedules is True
    assert model.current is not None
    assert model.current.config_name == "fall"
    assert model.current.records[0]["course"] == "CS 101"
    assert model.set_generated([first]) is False

    replacement = ScheduleResult(config_name="spring", schedule=[])
    assert model.set_generated([replacement]) is True
    assert model.current is not None
    assert model.current.config_name == "spring"


def test_loading_refreshes_existing_file_and_preserves_generated_before_it():
    model = ScheduleViewerModel()
    model.set_generated([ScheduleResult(config_name="fall", schedule=[])])

    original = model.load_bytes("schedule.csv", records_to_csv([_record("CS 101")]))
    refreshed = model.load_bytes("schedule.csv", records_to_csv([_record("CS 202")]))

    assert len(model.entries) == 2
    assert model.entries[0].source == "generated"
    assert model.entries[1] is refreshed
    assert original is not refreshed
    assert model.current is refreshed
    assert model.current.records[0]["course"] == "CS 202"


def test_serialize_default_names_and_export_current():
    model = ScheduleViewerModel()
    loaded = model.load_bytes("fall_schedule1.csv", records_to_csv([_record()]))

    assert model.serialize(loaded, "csv").decode().count("CS 101") == 1
    assert json.loads(model.serialize(loaded, "json")) == [_record()]
    assert model.default_export_file_name(loaded, "json") == "fall_schedule1.json"

    generated = ScheduleEntry(
        label="fall",
        config_name="fall",
        source="generated",
        records=[_record()],
    )
    assert model.default_export_file_name(generated, "csv") == "fall_schedule1.csv"

    content, name, media_type = model.export(generated, "json", "../bad/name")
    assert json.loads(content) == [_record()]
    assert name == "name.json"
    assert media_type == "application/json"


@pytest.mark.parametrize("file_format", ["txt", ""])
def test_export_rejects_unsupported_format(file_format):
    model = ScheduleViewerModel()
    entry = ScheduleEntry("x", "fall", "file", [_record()])

    with pytest.raises(ValueError, match="Please choose CSV or JSON"):
        model.serialize(entry, file_format)
    with pytest.raises(ValueError, match="Please choose CSV or JSON"):
        model.export(entry, file_format, "schedule")
    with pytest.raises(ValueError, match="Please choose CSV or JSON"):
        model.export_all_generated(file_format)


def test_export_validates_name_and_all_generated_sanitizes_names():
    model = ScheduleViewerModel()
    entry = ScheduleEntry("x", "bad<> name", "generated", [_record()])

    with pytest.raises(ValueError, match="valid file name"):
        model.export(entry, "csv", ".csv")

    model.set_generated(
        [
            ScheduleResult(config_name='bad<>/name', schedule=[
                SimpleNamespace(course="CS 101", faculty="Dr. Smith", room="Room 1", lab=None, time="MON 09:00-09:50")
            ]),
            ScheduleResult(config_name='bad<>/name', schedule=[]),
        ]
    )
    content, name, media_type = model.export_all_generated("csv")

    assert name == "generated_schedules.zip"
    assert media_type == "application/zip"
    with zipfile.ZipFile(io.BytesIO(content)) as archive:
        assert archive.namelist() == [
            "bad___name_schedule1.csv",
            "bad___name_schedule2.csv",
        ]


def test_export_all_generated_requires_generated_schedules():
    model = ScheduleViewerModel()

    with pytest.raises(ValueError, match="There are no generated schedules"):
        model.export_all_generated("csv")
