"""Shared types for calendar rendering and meeting-detail components."""

from typing import Any, TypedDict

ScheduleRow = dict[str, Any]
OverlapCluster = list[tuple[ScheduleRow, int, int]]


class SelectedMeeting(TypedDict):
    row: ScheduleRow
    start: int
    end: int
    cluster: OverlapCluster
