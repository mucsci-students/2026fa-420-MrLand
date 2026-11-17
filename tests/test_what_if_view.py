import asyncio

from nicegui import ElementFilter, ui
from nicegui.elements.upload_files import SmallFileUpload
from nicegui.testing import user_simulation

from src.views.schedule_analysis.schedule_analysis_gui import schedule_analysis
from src.views.schedule_analysis.what_if_tab import WhatIfTab, build_what_if_tab
from tests.conftest import active_client
from tests.test_configuration import make_valid_config


def test_what_if_tab_loads_configuration_from_the_users_device():
    async def simulate():
        async with user_simulation(root=build_what_if_tab) as user:
            await user.open("/")
            await user.should_see("What-If Configuration")
            await user.should_see("No configuration loaded.")

            user.find("Load configuration").click()
            await user.should_see("Choose configuration file")
            await user.should_see("Select a JSON configuration file from your computer.")
            await user.should_not_see("Temporary Configuration Editor")

    asyncio.run(simulate())


def test_leaving_what_if_does_not_prompt_when_there_are_no_editor_changes():
    async def simulate():
        async with user_simulation(root=schedule_analysis) as user:
            await user.open("/")
            user.find("What-If Analysis").click()
            user.find("Statistics").click()
            await user.should_see("Statistics")

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
                assert not dialog.value

    asyncio.run(simulate())


def test_what_if_edits_are_temporary_and_can_be_reset():
    config = make_valid_config()
    what_if_tab = WhatIfTab()

    async def simulate():
        async with user_simulation(root=what_if_tab.build) as user:
            await user.open("/")
            user.find("Load configuration").click()
            with active_client(user):
                upload = next(iter(ElementFilter(kind=ui.upload)))
                await upload.handle_uploads(
                    [
                        SmallFileUpload(
                            "demo.json",
                            "application/json",
                            config.model_dump_json().encode(),
                        )
                    ]
                )

            await user.should_see("Reset temporary edits")
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
                generation_limit.value = config.limit + 1
            user.find("Save settings").click()

            assert what_if_tab._session is not None
            assert what_if_tab._session.configuration.limit == config.limit + 1
            assert config.limit != what_if_tab._session.configuration.limit
            assert what_if_tab.has_unsaved_changes()
            await user.should_see("What-If changes will be lost")

            user.find("Reset temporary edits").click()
            assert what_if_tab._session.configuration.limit == config.limit
            assert not what_if_tab.has_unsaved_changes()
            await user.should_see("No What-If changes")

    asyncio.run(simulate())


def test_leaving_with_what_if_edits_prompts_before_discarding():
    config = make_valid_config()

    async def simulate():
        async with user_simulation(root=schedule_analysis) as user:
            await user.open("/")
            user.find("What-If Analysis").click()
            user.find("Load configuration").click()
            with active_client(user):
                config_dialog = next(
                    dialog
                    for dialog in ElementFilter(kind=ui.dialog)
                    if next(
                        iter(
                            ElementFilter(
                                kind=ui.label,
                                content="Select a JSON configuration file from your computer.",
                            ).within(instance=dialog)
                        ),
                        None,
                    )
                )
                upload = next(iter(ElementFilter(kind=ui.upload).within(instance=config_dialog)))
                await upload.handle_uploads(
                    [
                        SmallFileUpload(
                            "demo.json",
                            "application/json",
                            config.model_dump_json().encode(),
                        )
                    ]
                )
            await user.should_see("Reset temporary edits")

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
                generation_limit.value = config.limit + 1
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
