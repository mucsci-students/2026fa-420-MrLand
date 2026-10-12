import json

from src.controllers.schedule_controller import ScheduleController
from src.models.schedule_files import records_to_csv
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
