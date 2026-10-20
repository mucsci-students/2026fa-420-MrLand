from src.ai.scheduler_agent import SchedulerAgentState, get_tool_list
from src.controllers.configuration_controller import ConfigurationController
from src.models.configuration_model import ValidationProblem


def test_scheduler_tools_edit_the_active_configuration_through_controller():
    controller = ConfigurationController()
    config = controller.new_configuration()
    tools = {
        tool.name: tool
        for tool in get_tool_list(
            SchedulerAgentState(config),
            apply_change=controller.apply_change,
        )
    }

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
