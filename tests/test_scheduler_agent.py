import json
from types import SimpleNamespace

from src.ai.scheduler_agent import SchedulerAgentState, get_tool_list
from src.controllers.configuration_controller import ConfigurationController
from src.models.configuration_model import ValidationProblem


def _tools(state, **kwargs):
    return {
        tool.name: tool
        for tool in get_tool_list(state, **kwargs)
    }


def test_scheduler_tools_edit_the_active_configuration_through_controller():
    controller = ConfigurationController()
    config = controller.new_configuration()
    tools = _tools(
        SchedulerAgentState(config),
        apply_change=controller.apply_change,
    )

    result = tools["add_room"].invoke(
        {"name": "Room 101", "capacity": 30, "features": ["projector"]}
    )

    assert result.startswith("Room Room 101 added successfully.")
    assert config.config.rooms[0].name == "Room 101"
    assert "Room 101" in tools["get_rooms"].invoke({})


def test_scheduler_tool_reports_controller_rejection_without_mutating():
    config = ConfigurationController().new_configuration()

    def reject_change(mutation):
        return False, [ValidationProblem("Rooms", "Room 101", "Rejected for test")]

    tools = get_tool_list(
        SchedulerAgentState(config),
        apply_change=reject_change,
    )
    add_room = next(tool for tool in tools if tool.name == "add_room")

    result = add_room.invoke({"name": "Room 101"})

    assert "Change rejected by scheduler validation" in result
    assert "Rejected for test" in result
    assert config.config.rooms == []


def test_configuration_tools_require_an_active_config_without_one():
    tools = _tools(SchedulerAgentState())
    required = "Please create or load a configuration"
    calls = {
        "add_room": {"name": "Room 101"},
        "add_lab": {"name": "Lab 1"},
        "add_faculty": {"name": "Dr. Smith"},
        "add_course": {"course_id": "CS 101"},
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

    for name, arguments in calls.items():
        assert required in tools[name].invoke(arguments), name

    assert required in tools["get_active_configuration_status"].invoke({})


def test_scheduler_tools_inspect_and_manage_all_configuration_areas():
    config = ConfigurationController().new_configuration()
    tools = _tools(SchedulerAgentState(config))

    created = tools["create_configuration_item"].invoke(
        {
            "area": "rooms",
            "item": {"name": "Room 101", "capacity": 30, "features": ["projector"]},
        }
    )
    assert "Created rooms item" in created
    assert json.loads(tools["inspect_configuration"].invoke({"area": "rooms"})) == [
        {"name": "Room 101", "capacity": 30, "features": ["projector"], "times": None}
    ]

    updated = tools["update_configuration_item"].invoke(
        {
            "area": "rooms",
            "item_key": "Room 101",
            "item": {"capacity": 40},
        }
    )
    assert "Updated rooms item" in updated
    assert config.config.rooms[0].capacity == 40

    deleted = tools["delete_configuration_item"].invoke(
        {"area": "rooms", "item_key": "Room 101"}
    )
    assert "Deleted rooms item" in deleted
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
    assert "Created time_blocks item" in result
    assert config.time_slot_config.times["MON"][0].start == "09:00"

    tools["update_configuration_settings"].invoke(
        {"limit": 5, "max_time_gap": 20, "optimizer_flags": []}
    )
    assert config.limit == 5
    assert config.time_slot_config.max_time_gap == 20


def test_save_tool_uses_the_application_save_callback(monkeypatch):
    import src.ai.scheduler_agent as scheduler_agent

    config = ConfigurationController().new_configuration()
    saved_names = []
    monkeypatch.setattr(scheduler_agent, "validate_config", lambda _config: [])
    tools = _tools(
        SchedulerAgentState(config),
        save_configuration=saved_names.append,
    )

    result = tools["save_configuration"].invoke({"config_name": "Fall 2026"})

    assert result == "Configuration saved as 'Fall 2026.json'."
    assert saved_names == ["Fall 2026"]


def test_generate_schedules_uses_the_active_configuration(monkeypatch):
    import src.ai.scheduler_agent as scheduler_agent
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
    monkeypatch.setattr(scheduler_agent, "validate_config", lambda _config: [])
    generator = ScheduleGeneratorController(ScheduleGeneratorModel())
    state = SchedulerAgentState(config, schedule_generator=generator)

    result = state.generate_schedules()
    viewer = ScheduleController(generator=generator)

    assert "Generated 1 schedule(s), 1 valid." in result
    assert "Schedule Viewer tab" in result
    assert "CS 101.01" not in result
    assert viewer.sync_generated()
    assert viewer.current.records[0]["course"] == "CS 101.01"
