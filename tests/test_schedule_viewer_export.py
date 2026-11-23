import csv
import io
import json
import zipfile
from types import SimpleNamespace
from typing import cast

from scheduler.models.course import CourseInstance

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
    model = ScheduleViewerModel()
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


def test_generated_exports_do_not_require_a_saved_schedule_directory():
    model = ScheduleViewerModel()
    model.set_generated([ScheduleResult(config_name="fall", schedule=[])])
    controller = ScheduleController(model=model)

    current_export, current_error = controller.export_current("csv", "")
    all_export, all_error = controller.export_all_generated("csv")

    assert current_error is None
    assert current_export is not None
    assert current_export[1] == "fall_schedule1.csv"
    assert all_error is None
    assert all_export is not None
    with zipfile.ZipFile(io.BytesIO(all_export[0])) as archive:
        assert archive.namelist() == ["fall_schedule1.csv"]


def test_export_current_uses_selected_serialization_strategy():
    records = [
        {
            "course": "CMSC 420",
            "faculty": "Dr. Smith",
            "room": "Room 101",
            "lab": "",
            "times": "MON 09:00-09:50",
        }
    ]
    model = ScheduleViewerModel()
    entry = model.load_bytes("fall_schedule1.csv", records_to_csv(records))

    assert model.serialize(entry, "csv") == records_to_csv(records)
    assert json.loads(model.serialize(entry, "json")) == records


def test_export_current_rejects_unsupported_format():
    model = ScheduleViewerModel()
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


def test_export_all_generated_returns_zip_without_loaded_schedules():
    model = ScheduleViewerModel()
    model.set_generated(
        [
            ScheduleResult(
                config_name="fall",
                schedule=[
                    cast(
                        CourseInstance,
                        SimpleNamespace(
                            course="CS101",
                            faculty="Dr. Smith",
                            room="Room 101",
                            lab=None,
                            time="MON 09:00-09:50",
                        ),
                    )
                ],
            ),
            ScheduleResult(
                config_name="fall",
                schedule=[
                    cast(
                        CourseInstance,
                        SimpleNamespace(
                            course="CS102",
                            faculty="Dr. Jones",
                            room="Room 202",
                            lab=None,
                            time="TUE 10:00-10:50",
                        ),
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


def test_export_all_generated_starts_at_one_and_numbers_same_config_sequentially():
    model = ScheduleViewerModel()
    model.set_generated(
        [
            ScheduleResult(
                config_name="fall",
                schedule=[
                    cast(
                        CourseInstance,
                        SimpleNamespace(
                            course="CS101",
                            faculty="Dr. Smith",
                            room="Room 101",
                            lab=None,
                            time="MON 09:00-09:50",
                        ),
                    )
                ],
            ),
            ScheduleResult(config_name="fall", schedule=[]),
        ]
    )

    content, file_name, media_type = model.export_all_generated("json")

    assert file_name == "generated_schedules.zip"
    assert media_type == "application/zip"
    with zipfile.ZipFile(io.BytesIO(content)) as archive:
        assert archive.namelist() == ["fall_schedule1.json", "fall_schedule2.json"]
        assert json.loads(archive.read(archive.namelist()[0]))[0]["course"] == "CS101"


def test_export_all_generated_reports_missing_schedules_and_invalid_format():
    model = ScheduleViewerModel()
    controller = ScheduleController(model=model)

    download, error = controller.export_all_generated("csv")
    assert download is None
    assert error == "There are no generated schedules to export."

    download, error = controller.export_all_generated("txt")
    assert download is None
    assert error == "Please choose CSV or JSON."
