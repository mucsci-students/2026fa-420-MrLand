import csv
import io
import json
import zipfile
from types import SimpleNamespace

from src.controllers.schedule_controller import ScheduleController
from src.models.schedule_files import records_to_csv
from src.models.schedule_result import ScheduleResult
from src.models.schedule_viewer_model import ScheduleViewerModel


def test_export_current_returns_download_data_without_writing_to_disk(tmp_path):
    records = [
        {
            "course": "CMSC 420",
            "faculty": "Dr. Smith",
            "room": "Room 101",
            "lab": "",
            "times": "MON 09:00-09:50",
        }
    ]
    model = ScheduleViewerModel(directory=tmp_path)
    model.load_bytes("fall_schedule1.csv", records_to_csv(records))
    controller = ScheduleController(model=model)

    download, error = controller.export_current("json", "../fall_schedule1")

    assert error is None
    assert download is not None
    content, file_name, media_type = download
    assert file_name == "fall_schedule1.json"
    assert media_type == "application/json"
    assert json.loads(content) == records
    assert list(tmp_path.iterdir()) == []


def test_export_current_uses_selected_serialization_strategy(tmp_path):
    records = [
        {
            "course": "CMSC 420",
            "faculty": "Dr. Smith",
            "room": "Room 101",
            "lab": "",
            "times": "MON 09:00-09:50",
        }
    ]
    model = ScheduleViewerModel(directory=tmp_path)
    entry = model.load_bytes("fall_schedule1.csv", records_to_csv(records))

    assert model.serialize(entry, "csv") == records_to_csv(records)
    assert json.loads(model.serialize(entry, "json")) == records


def test_export_current_rejects_unsupported_format(tmp_path):
    model = ScheduleViewerModel(directory=tmp_path)
    model.load_bytes(
        "fall_schedule1.csv",
        records_to_csv(
            [
                {
                    "course": "CMSC 420",
                    "faculty": "Dr. Smith",
                    "room": "Room 101",
                    "lab": "",
                    "times": "MON 09:00-09:50",
                }
            ]
        ),
    )
    controller = ScheduleController(model=model)

    download, error = controller.export_current("txt", "schedule")

    assert download is None
    assert error == "Please choose CSV or JSON."


def test_export_all_generated_returns_zip_without_loaded_schedules(tmp_path):
    model = ScheduleViewerModel(directory=tmp_path)
    model.set_generated(
        [
            ScheduleResult(
                config_name="fall",
                schedule=[
                    SimpleNamespace(
                        course="CS101",
                        faculty="Dr. Smith",
                        room="Room 101",
                        lab=None,
                        time="MON 09:00-09:50",
                    )
                ],
            ),
            ScheduleResult(
                config_name="fall",
                schedule=[
                    SimpleNamespace(
                        course="CS102",
                        faculty="Dr. Jones",
                        room="Room 202",
                        lab=None,
                        time="TUE 10:00-10:50",
                    )
                ],
            ),
        ]
    )
    model.load_bytes(
        "uploaded.csv",
        records_to_csv(
            [
                {
                    "course": "CS999",
                    "faculty": "Dr. Upload",
                    "room": "Room 999",
                    "lab": "",
                    "times": "WED 11:00-11:50",
                }
            ]
        ),
    )
    controller = ScheduleController(model=model)

    download, error = controller.export_all_generated("csv")

    assert error is None
    assert download is not None
    content, file_name, media_type = download
    assert file_name == "generated_schedules.zip"
    assert media_type == "application/zip"
    with zipfile.ZipFile(io.BytesIO(content)) as archive:
        assert archive.namelist() == [
            "fall_schedule1.csv",
            "fall_schedule2.csv",
        ]
        exported_rows = [
            list(csv.DictReader(io.StringIO(archive.read(name).decode())))
            for name in archive.namelist()
        ]
    assert [rows[0]["course"] for rows in exported_rows] == [
        "CS101",
        "CS102",
    ]
    assert list(tmp_path.iterdir()) == []


def test_export_all_generated_supports_json_and_avoids_existing_names(tmp_path):
    (tmp_path / "fall_schedule1.csv").write_text("", encoding="utf-8")
    model = ScheduleViewerModel(directory=tmp_path)
    model.set_generated(
        [
            ScheduleResult(
                config_name="fall",
                schedule=[
                    SimpleNamespace(
                        course="CS101",
                        faculty="Dr. Smith",
                        room="Room 101",
                        lab=None,
                        time="MON 09:00-09:50",
                    )
                ],
            )
        ]
    )

    content, file_name, media_type = model.export_all_generated("json")

    assert file_name == "generated_schedules.zip"
    assert media_type == "application/zip"
    with zipfile.ZipFile(io.BytesIO(content)) as archive:
        assert archive.namelist() == ["fall_schedule2.json"]
        assert json.loads(archive.read(archive.namelist()[0]))[0]["course"] == "CS101"


def test_export_all_generated_reports_missing_schedules_and_invalid_format(
    tmp_path,
):
    model = ScheduleViewerModel(directory=tmp_path)
    controller = ScheduleController(model=model)

    download, error = controller.export_all_generated("csv")
    assert download is None
    assert error == "There are no generated schedules to export."

    download, error = controller.export_all_generated("txt")
    assert download is None
    assert error == "Please choose CSV or JSON."
