"""AI helpers for the scheduler application.

This package contains a LangChain-based agent that wraps the scheduler's
configuration model. The agent is intentionally thin: it interprets natural
language requests and delegates all real scheduling constraints to the scheduler
objects and validation functions that already exist in the project.
"""

from .scheduler_agent import SchedulerAgentState, build_scheduler_agent

__all__ = ["SchedulerAgentState", "build_scheduler_agent"]
