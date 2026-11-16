"""Shared execution guards for scheduler-agent tools."""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

from scheduler.config import CombinedConfig

from src.ai.scheduler_agent_state import SchedulerAgentState


class _RejectedToolMutation(Exception):
    def __init__(self, result: dict[str, Any]) -> None:
        super().__init__(result["message"])
        self.result = result


class AgentToolGuards:
    def __init__(
        self,
        state: SchedulerAgentState,
        apply_change: Callable[[Callable[[], Any]], tuple[bool, list[Any]]],
        on_tool_result: Callable[[dict[str, Any]], None] | None = None,
    ) -> None:
        self.state = state
        self.apply_change = apply_change
        self.on_tool_result = on_tool_result

    def report(self, result: dict[str, Any]) -> dict[str, Any]:
        if self.on_tool_result is not None:
            self.on_tool_result(result)
        return result

    def mutation(
        self,
        operation: Callable[..., dict[str, Any]],
        *,
        needs_confirmation: bool = False,
    ) -> Callable[..., dict[str, Any]]:
        def guarded_operation(**arguments: Any) -> dict[str, Any]:
            if not self.state.has_active_configuration:
                return self.report(
                    self.state._result(False, self.state.configuration_required_message())
                )
            if needs_confirmation:
                key = arguments["item_key"]
                if self.state._confirm_action is None or not self.state._confirm_action(
                    f"Delete {arguments['area']} item '{key}'?"
                ):
                    return self.report(
                        self.state._result(False, "Deletion cancelled; no item was changed.")
                    )
            result: list[dict[str, Any]] = []

            def apply_operation() -> None:
                outcome = operation(**arguments)
                if not outcome["success"]:
                    raise _RejectedToolMutation(outcome)
                result.append(outcome)

            try:
                accepted, problems = self.apply_change(apply_operation)
            except _RejectedToolMutation as rejected:
                return self.report(rejected.result)
            if not accepted:
                details = "\n".join(
                    f"- {problem.area}: {problem.item or 'overall'}: {problem.message}"
                    for problem in problems
                )
                return self.report(
                    self.state._result(
                        False,
                        f"Change rejected by scheduler validation:\n{details}",
                        errors=[
                            {
                                "area": problem.area,
                                "item": problem.item,
                                "message": problem.message,
                            }
                            for problem in problems
                        ],
                    )
                )
            if not result:
                raise RuntimeError(
                    "The configuration controller accepted a mutation without running it."
                )
            outcome = result[0]
            if problems:
                details = "\n".join(
                    f"- {problem.area}: {problem.item or 'overall'}: {problem.message}"
                    for problem in problems
                )
                outcome = {
                    **outcome,
                    "message": outcome["message"]
                    + f"\nThe draft still has validation issues:\n{details}",
                    "warnings": [
                        {
                            "area": problem.area,
                            "item": problem.item,
                            "message": problem.message,
                        }
                        for problem in problems
                    ],
                }
            return self.report(outcome)

        return guarded_operation

    def configuration(
        self, operation: Callable[..., dict[str, Any]]
    ) -> Callable[..., dict[str, Any]]:
        def guarded_operation(**arguments: Any) -> dict[str, Any]:
            if not self.state.has_active_configuration:
                return self.report(
                    self.state._result(False, self.state.configuration_required_message())
                )
            outcome = operation(**arguments)
            self.report(outcome)
            return outcome

        return guarded_operation

    def informational(
        self, operation: Callable[..., dict[str, Any]]
    ) -> Callable[..., dict[str, Any]]:
        def reported_operation(**arguments: Any) -> dict[str, Any]:
            return self.report(operation(**arguments))

        return reported_operation

    def history(
        self,
        operation: Callable[[], CombinedConfig | None] | None,
        action: str,
    ) -> Callable[[], dict[str, Any]]:
        def guarded_operation() -> dict[str, Any]:
            if not self.state.has_active_configuration:
                return self.report(
                    self.state._result(False, self.state.configuration_required_message())
                )
            if operation is None:
                return self.report(
                    self.state._result(
                        False, f"{action.capitalize()} is unavailable in this context."
                    )
                )
            updated_configuration = operation()
            if updated_configuration is None:
                return self.report(
                    self.state._result(
                        False,
                        f"There is no configuration change available to {action}.",
                    )
                )
            self.state.config = updated_configuration
            verb = "undone" if action == "undo" else "redone"
            return self.report(self.state._result(True, f"Configuration change {verb}."))

        return guarded_operation

    def validation_error(self, error: list[Any]) -> str:
        result = self.report(self.state._result(False, f"Invalid tool arguments: {error}"))
        return json.dumps(result, default=str)
