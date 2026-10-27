import json
from types import SimpleNamespace

from src.ai.scheduler_agent import SchedulerAgentState, get_tool_list
from src.controllers.configuration_controller import ConfigurationController
from src.models.configuration_model import ValidationProblem
from src.views.configuration_editor import PANEL_COMBINATIONS


def _tools(state, **kwargs):
    return {
        tool.name: tool
        for tool in get_tool_list(state, **kwargs)
    }


def test_list_combinations_returns_panel_sequences_and_hats():
    tools = _tools(SchedulerAgentState())

    result = tools["list_combinations"].invoke({})

    assert result["success"]
    assert result["combinations"] == [
        {"name": name, "panels": list(panels), "hat": hat}
        for name, panels, hat in PANEL_COMBINATIONS
    ]


def test_general_create_tool_edits_the_active_configuration_through_controller():
    controller = ConfigurationController()
    config = controller.new_configuration()
    tools = _tools(
        SchedulerAgentState(config),
        apply_change=controller.apply_change,
    )

    result = tools["create_configuration_item"].invoke(
        {
            "area": "rooms",
            "item": {
                "name": "Room 101",
                "capacity": 30,
                "features": ["projector"],
            },
        }
    )

    assert result["success"]
    assert result["message"].startswith("Created rooms item")
    assert config.config.rooms[0].name == "Room 101"
    assert tools["get_rooms"].invoke({})["items"][0]["name"] == "Room 101"


def test_general_create_tool_preserves_case_sensitive_duplicate_checks():
    config = ConfigurationController().new_configuration()
    tools = _tools(SchedulerAgentState(config))

    for area, item in (
        ("rooms", {"name": "Room 101", "capacity": 30}),
        ("rooms", {"name": "room 101", "capacity": 30}),
        ("labs", {"name": "Lab 1", "capacity": 30}),
        ("labs", {"name": "lab 1", "capacity": 30}),
        ("faculty", {"name": "Dr. Smith"}),
        ("faculty", {"name": "dr. smith"}),
    ):
        result = tools["create_configuration_item"].invoke(
            {"area": area, "item": item}
        )
        assert result["success"]

    assert len(config.config.rooms) == 2
    assert len(config.config.labs) == 2
    assert len(config.config.faculty) == 2


def test_general_create_tool_keeps_defaults_for_all_item_types():
    config = ConfigurationController().new_configuration()
    tools = _tools(SchedulerAgentState(config))
    create = tools["create_configuration_item"]

    course = create.invoke(
        {"area": "courses", "item": {"course_id": "CS 101"}}
    )
    faculty = create.invoke(
        {"area": "faculty", "item": {"name": "Dr. Smith"}}
    )

    assert course["success"]
    assert config.config.courses[0].credits == 3
    assert config.config.courses[0].faculty is None
    assert faculty["success"]
    assert config.config.faculty[0].maximum_credits == 12


def test_scheduler_tool_reports_controller_rejection_without_mutating():
    config = ConfigurationController().new_configuration()

    def reject_change(mutation):
        return False, [ValidationProblem("Rooms", "Room 101", "Rejected for test")]

    tools = _tools(
        SchedulerAgentState(config),
        apply_change=reject_change,
    )
    result = tools["create_configuration_item"].invoke(
        {"area": "rooms", "item": {"name": "Room 101", "capacity": 30}}
    )

    assert result["success"] is False
    assert "Change rejected by scheduler validation" in result["message"]
    assert "Rejected for test" in result["message"]
    assert config.config.rooms == []


def test_configuration_tools_require_an_active_config_without_one():
    tools = _tools(SchedulerAgentState())
    required = "Please create or load a configuration"
    calls = {
        "get_rooms": {},
        "get_labs": {},
        "get_faculty": {},
        "get_courses": {},
        "get_config_summary": {},
        "validate_current_config": {},
        "inspect_configuration": {"area": "all"},
        "create_configuration_item": {
            "area": "rooms",
            "item": {"name": "Room 101", "capacity": 30},
        },
        "update_configuration_item": {
            "area": "rooms",
            "item_key": "Room 101",
            "item": {"capacity": 40},
        },
        "delete_configuration_item": {"area": "rooms", "item_key": "Room 101"},
        "update_configuration_settings": {"limit": 3},
        "save_configuration": {"config_name": "Fall 2026"},
        "generate_schedules": {},
    }

    assert not {"add_room", "add_lab", "add_faculty", "add_course"} & tools.keys()
    for name, arguments in calls.items():
        assert required in tools[name].invoke(arguments)["message"], name

    assert required in tools["get_active_configuration_status"].invoke({})["message"]


def test_scheduler_tools_inspect_and_manage_all_configuration_areas():
    config = ConfigurationController().new_configuration()
    tools = _tools(SchedulerAgentState(config))

    created = tools["create_configuration_item"].invoke(
        {
            "area": "rooms",
            "item": {"name": "Room 101", "capacity": 30, "features": ["projector"]},
        }
    )
    assert created["success"]
    assert "Created rooms item" in created["message"]
    assert tools["inspect_configuration"].invoke({"area": "rooms"})["data"] == [
        {"name": "Room 101", "capacity": 30, "features": ["projector"], "times": None}
    ]

    updated = tools["update_configuration_item"].invoke(
        {
            "area": "rooms",
            "item_key": "Room 101",
            "item": {"capacity": 40},
        }
    )
    assert updated["success"]
    assert "Updated rooms item" in updated["message"]
    assert config.config.rooms[0].capacity == 40

    deleted = tools["delete_configuration_item"].invoke(
        {"area": "rooms", "item_key": "Room 101"}
    )
    assert deleted["success"] is False
    assert "confirmation" in deleted["message"].lower() or "cancelled" in deleted["message"].lower()
    assert len(config.config.rooms) == 1
    tools = _tools(
        SchedulerAgentState(config, confirm_action=lambda _question: True)
    )
    deleted = tools["delete_configuration_item"].invoke(
        {"area": "rooms", "item_key": "Room 101"}
    )
    assert deleted["success"]
    assert "Deleted rooms item" in deleted["message"]
    assert config.config.rooms == []


def test_scheduler_tools_update_settings_and_time_blocks():
    config = ConfigurationController().new_configuration()
    tools = _tools(SchedulerAgentState(config))

    result = tools["create_configuration_item"].invoke(
        {
            "area": "time_blocks",
            "item_key": "MON",
            "item": {"blocks": [{"start": "09:00", "spacing": 30, "end": "12:00"}]},
        }
    )
    assert result["success"]
    assert "Created time_blocks item" in result["message"]
    assert config.time_slot_config.times["MON"][0].start == "09:00"

    tools["update_configuration_settings"].invoke(
        {"limit": 5, "max_time_gap": 20, "optimizer_flags": []}
    )
    assert config.limit == 5
    assert config.time_slot_config.max_time_gap == 20


def test_meeting_tools_create_update_inspect_and_confirm_delete():
    config = ConfigurationController().new_configuration()
    tools = _tools(SchedulerAgentState(config, confirm_action=lambda _question: True))

    pattern = tools["create_configuration_item"].invoke(
        {
            "area": "class_patterns",
            "item": {
                "credits": 3,
                "meetings": [{"day": "MON", "duration": 50}],
            },
        }
    )
    assert pattern["success"]

    created = tools["create_configuration_item"].invoke(
        {
            "area": "meetings",
            "item_key": "0",
            "item": {"day": "WED", "duration": 50, "delivery": "online"},
        }
    )
    assert created["success"]

    updated = tools["update_configuration_item"].invoke(
        {
            "area": "meetings",
            "item_key": "0::WED",
            "item": {"duration": 75},
        }
    )
    assert updated["success"]
    assert config.time_slot_config.classes[0].meetings[1].duration == 75

    inspected = tools["inspect_configuration"].invoke({"area": "meetings"})
    assert inspected["success"]
    assert inspected["data"][1]["class_pattern_index"] == 0
    assert inspected["data"][1]["duration"] == 75

    deleted = tools["delete_configuration_item"].invoke(
        {"area": "meetings", "item_key": "0::WED"}
    )
    assert deleted["success"]
    assert len(config.time_slot_config.classes[0].meetings) == 1


def test_overwriting_saved_configuration_requires_confirmation(monkeypatch):
    import src.ai.agent_tools as agent_tools

    config = ConfigurationController().new_configuration()
    saved_names = []
    monkeypatch.setattr(agent_tools, "validate_config", lambda _config: [])
    tools = _tools(
        SchedulerAgentState(
            config,
            save_configuration=saved_names.append,
            configuration_exists=lambda _name: True,
            confirm_action=lambda _question: False,
        )
    )

    result = tools["save_configuration"].invoke({"config_name": "Fall 2026"})

    assert result["success"] is False
    assert "cancelled" in result["message"].lower()
    assert saved_names == []


def test_global_settings_validate_before_mutating_any_setting():
    config = ConfigurationController().new_configuration()
    tools = _tools(SchedulerAgentState(config))

    result = tools["update_configuration_settings"].invoke(
        {"limit": 5, "max_time_gap": -1}
    )

    assert result["success"] is False
    assert config.limit == 10
    assert config.time_slot_config.max_time_gap == 30


def test_invalid_tool_arguments_return_structured_failure():
    config = ConfigurationController().new_configuration()
    reported = []
    tools = _tools(
        SchedulerAgentState(config),
        on_tool_result=reported.append,
    )

    result = tools["update_configuration_settings"].invoke({"limit": "not-a-number"})

    parsed = json.loads(result)
    assert parsed["success"] is False
    assert "Invalid tool arguments" in parsed["message"]
    assert reported[0]["success"] is False


def test_save_tool_uses_the_application_save_callback(monkeypatch):
    import src.ai.agent_tools as agent_tools

    config = ConfigurationController().new_configuration()
    saved_names = []
    monkeypatch.setattr(agent_tools, "validate_config", lambda _config: [])
    tools = _tools(
        SchedulerAgentState(config, configuration_exists=lambda _name: False),
        save_configuration=saved_names.append,
    )

    result = tools["save_configuration"].invoke({"config_name": "Fall 2026"})

    assert result["success"]
    assert result["message"] == "Configuration saved as 'Fall 2026.json'."
    assert saved_names == ["Fall 2026"]


def test_generate_schedules_uses_the_active_configuration(monkeypatch):
    import src.ai.agent_tools as agent_tools
    import src.models.schedule_generator_model as schedule_generator_model

    from src.controllers.schedule_controller import ScheduleController
    from src.controllers.schedule_generator_controller import ScheduleGeneratorController
    from src.models.schedule_generator_model import ScheduleGeneratorModel

    config = ConfigurationController().new_configuration()
    schedule = [
        SimpleNamespace(
            course="CS 101.01",
            faculty="Dr. Smith",
            room="Room 101",
            lab=None,
            time="MON 09:00-09:50",
        )
    ]

    class FakeScheduler:
        def __init__(self, current_config):
            assert current_config is config

        def get_models(self):
            return iter([schedule])

        def audit_schedule(self, _schedule):
            return SimpleNamespace(is_valid=True)

    monkeypatch.setattr(schedule_generator_model, "Scheduler", FakeScheduler)
    monkeypatch.setattr(agent_tools, "validate_config", lambda _config: [])
    generator = ScheduleGeneratorController(ScheduleGeneratorModel())
    state = SchedulerAgentState(config, schedule_generator=generator)

    result = state.generate_schedules()
    viewer = ScheduleController(generator=generator)

    assert result["success"]
    assert "Generated 1 schedule(s), 1 valid." in result["message"]
    assert "Schedule Viewer tab" in result["message"]
    assert "CS 101.01" not in result["message"]
    assert viewer.sync_generated()
    assert viewer.current.records[0]["course"] == "CS 101.01"
