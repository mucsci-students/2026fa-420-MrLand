import json
from types import SimpleNamespace

import pytest

from src.models.schedule_files import (
    CsvScheduleExportStrategy,
    JsonScheduleExportStrategy,
    config_name_from_file_name,
    instance_times,
    parse_schedule_file,
    records_from_result,
    records_to_csv,
    records_to_json,
    schedule_export_strategy,
)
from src.models.schedule_result import ScheduleResult


def test_schedule_records_csv_json_and_export_strategies():
    records = [
        {
            "course": "CS 101",
            "faculty": "Dr. Smith",
            "room": "Room 1",
            "lab": "Lab 1",
            "times": "MON 09:00-09:50",
        }
    ]

    csv_bytes = records_to_csv(records, {"schedule": "1", "config": "fall"})
    assert csv_bytes.decode().splitlines()[0] == "schedule,config,course,faculty,room,lab,times"
    assert "CS 101" in csv_bytes.decode()
    assert json.loads(records_to_json(records)) == records
    assert CsvScheduleExportStrategy().serialize(records) == records_to_csv(records)
    assert json.loads(JsonScheduleExportStrategy().serialize(records)) == records
    assert schedule_export_strategy("csv").serialize(records) == records_to_csv(records)
    assert schedule_export_strategy("json").serialize(records) == records_to_json(records)


def test_schedule_export_strategy_rejects_unknown_format():
    with pytest.raises(ValueError, match="Please choose CSV or JSON"):
        schedule_export_strategy("xml")


def test_generated_result_records_remove_marker_without_lab_and_keep_with_lab():
    result = ScheduleResult(
        config_name="fall",
        schedule=[
            SimpleNamespace(
                course="CS 101",
                faculty="Dr. Smith",
                room="Room 1",
                lab=None,
                time="MON 09:00-09:50^",
            ),
            SimpleNamespace(
                course="CS 102",
                faculty="Dr. Jones",
                room="Room 2",
                lab="Lab 1",
                time="TUE 10:00-10:50^",
            ),
        ],
    )

    records = records_from_result(result)

    assert instance_times(result.schedule[0]) == "MON 09:00-09:50"
    assert records[0]["lab"] == ""
    assert records[0]["room"] == "Room 1"
    assert records[1]["lab"] == "Lab 1"
    assert records[1]["times"] == "TUE 10:00-10:50^"


@pytest.mark.parametrize(
    ("file_name", "expected"),
    [
        ("fall_schedule1.csv", "fall"),
        ("spring_schedule_12.json", "spring"),
        ("custom.csv", "custom"),
    ],
)
def test_config_name_from_file_name(file_name, expected):
    assert config_name_from_file_name(file_name) == expected


def test_parse_csv_accepts_extra_columns_and_legacy_times():
    content = (
        "schedule,config,course,faculty,room,lab,times\n"
        "1,fall,CS 101,Dr. Smith,Room 1,,"
        "\"[TimeInstance(day=TUE, start=TimePoint(timepoint=540), "
        "duration=Duration(duration=50))]\"\n"
    ).encode()

    config_name, records = parse_schedule_file("ignored.csv", content)

    assert config_name == "fall"
    assert records[0]["course"] == "CS 101"
    assert records[0]["times"] == "TUE 09:00-09:50"


def test_parse_json_accepts_wrapped_document_and_online_times():
    content = json.dumps(
        {
            "config": "spring",
            "schedule": [],
            "meetings": [
                {
                    "course": "CS 201",
                    "faculty": "Dr. Jones",
                    "room": None,
                    "lab": None,
                    "times": "MON 18:00-19:15@online",
                }
            ],
        }
    ).encode()

    config_name, records = parse_schedule_file("spring_schedule2.json", content)

    assert config_name == "spring"
    assert records[0]["room"] == ""
    assert records[0]["times"] == "MON 18:00-19:15@online"


@pytest.mark.parametrize(
    ("file_name", "content", "message"),
    [
        ("schedule.csv", b"\xff", "The file is not UTF-8 text"),
        ("schedule.txt", b"", "Only .csv and .json"),
        ("schedule.json", b"{", "Invalid JSON"),
        ("schedule.json", b"{}", "Expected a list"),
        ("schedule.json", b'[{"course": "CS 101"}]', "Unrecognized meeting time"),
        ("schedule.csv", b"course,faculty\nCS 101,Dr. Smith", "missing column"),
        ("schedule.json", b"[]", "does not contain"),
        ("schedule.json", b'[null]', "must be a JSON object"),
        ("schedule.json", b'[{"course": "", "times": ""}]', "missing the course name"),
    ],
)
def test_parse_schedule_file_rejects_invalid_input(file_name, content, message):
    with pytest.raises(ValueError, match=message):
        parse_schedule_file(file_name, content)
