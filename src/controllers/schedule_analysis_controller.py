"""Coordinate analysis of the schedule selected in the Schedule Viewer."""

from src.controllers.schedule_controller import ScheduleController, schedule_controller
from src.models.schedule_analysis_model import ScheduleAnalysis, ScheduleAnalysisModel
from src.models.schedule_viewer_model import ScheduleEntry


class ScheduleAnalysisController:
    """Provide analysis for the currently selected schedule."""

    def __init__(
        self,
        model: ScheduleAnalysisModel | None = None,
        schedules: ScheduleController | None = None,
    ) -> None:
        self.model = model or ScheduleAnalysisModel()
        self.schedules = schedules or schedule_controller

    def analyze_selected_schedule(self) -> ScheduleAnalysis | None:
        """Analyze the selected schedule, or return ``None`` if none is available."""
        return self.analyze_schedule(self.schedules.current)

    def analyze_schedule(self, entry: ScheduleEntry | None) -> ScheduleAnalysis | None:
        """Analyze a schedule entry without changing the viewer's selection."""
        return self.model.analyze(entry)


schedule_analysis_controller = ScheduleAnalysisController()
