import asyncio

from nicegui import ElementFilter, ui
from nicegui.testing import user_simulation

from src.views.schedule_analysis.statistics_tab import build_statistics_tab
from tests.conftest import active_client


def test_statistics_overview_and_score_breakdown_show_requested_metrics():
    async def simulate():
        async with user_simulation(root=lambda: build_statistics_tab(lambda: None)) as user:
            await user.open("/")

            with active_client(user):
                overview = next(
                    card
                    for card in ElementFilter(kind=ui.card)
                    if next(
                        iter(
                            ElementFilter(
                                kind=ui.label,
                                content="Schedule Overview",
                            ).within(instance=card)
                        ),
                        None,
                    )
                )
                overview_labels = {
                    label.text for label in ElementFilter(kind=ui.label).within(instance=overview)
                }
                assert "Unscheduled Courses" not in overview_labels

                breakdown = next(
                    expansion
                    for expansion in ElementFilter(kind=ui.expansion)
                    if "Faculty Gaps"
                    in {
                        label.text
                        for label in ElementFilter(kind=ui.label).within(instance=expansion)
                    }
                )
                breakdown_labels = {
                    label.text for label in ElementFilter(kind=ui.label).within(instance=breakdown)
                }
                assert "Conflict Avoidance" not in breakdown_labels
                assert "Scheduled Courses" not in breakdown_labels
                assert "Faculty Workload Balance" in breakdown_labels
                assert "Weekday Course Balance" in breakdown_labels

    asyncio.run(simulate())
