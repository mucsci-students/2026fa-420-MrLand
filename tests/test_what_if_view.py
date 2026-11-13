import asyncio

from nicegui import ElementFilter, ui
from nicegui.testing import user_simulation

from src.views.schedule_analysis.schedule_analysis_gui import schedule_analysis
from src.views.schedule_analysis.what_if_tab import build_what_if_tab
from tests.conftest import active_client


def test_what_if_tab_offers_a_blank_unsaved_configuration():
    async def simulate():
        async with user_simulation(root=build_what_if_tab) as user:
            await user.open("/")
            await user.should_see("What-If Configuration")

            user.find("Create blank draft").click()
            await user.should_see("Temporary Configuration Editor")
            await user.should_see("Global settings")

            user.find("Generate Alternative Schedule").click()
            await user.should_see("Fix configuration issues")

    asyncio.run(simulate())


def test_leaving_edited_what_if_configuration_prompts_and_discards_on_confirm():
    async def simulate():
        async with user_simulation(root=schedule_analysis) as user:
            await user.open("/")
            user.find("What-If Analysis").click()
            await user.should_see("No temporary configuration is loaded.")
            user.find("Create blank draft").click()
            await user.should_see("Changes to a new blank draft")
            user.find("Global settings").click()

            with active_client(user):
                generation_limit = next(
                    iter(
                        ElementFilter(
                            kind=ui.number,
                            content="Generation limit",
                            only_visible=True,
                        )
                    )
                )
                generation_limit.value = 25
            user.find("Save settings").click()
            user.find("Statistics").click()
            await user.should_see("Unsaved What-If Changes")

            with active_client(user):
                dialog = next(
                    dialog
                    for dialog in ElementFilter(kind=ui.dialog)
                    if next(
                        iter(
                            ElementFilter(
                                kind=ui.label,
                                content="Unsaved What-If Changes",
                            ).within(instance=dialog)
                        ),
                        None,
                    )
                )
                assert dialog.value

            user.find("Leave and discard").click()
            await user.should_see("No What-If changes")

    asyncio.run(simulate())
