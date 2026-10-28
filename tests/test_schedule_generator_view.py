import asyncio

from nicegui import ElementFilter, ui
from nicegui.elements.upload_files import SmallFileUpload
from nicegui.testing import user_simulation

import src.views.schedule_generator as generator
from tests.test_configuration import make_valid_config


def test_schedule_generator_loads_uploaded_configuration(monkeypatch):
    config = make_valid_config()
    content = config.model_dump_json().encode()

    class FakeConfigurationController:
        def __init__(self):
            self.uploaded_content = None

        def load_uploaded_configuration(self, uploaded_content):
            self.uploaded_content = uploaded_content
            return config

    config_controller = FakeConfigurationController()
    monkeypatch.setattr(
        generator,
        "ConfigurationController",
        lambda: config_controller,
    )

    async def simulate():
        async with user_simulation(root=generator.schedule_generator) as user:
            await user.open("/")
            with user.client:
                assert not list(ElementFilter(kind=ui.select))
            user.find("Load configuration").click()
            await user.should_see("Load Configuration")

            with user.client:
                upload = next(iter(ElementFilter(kind=ui.upload)))
                await upload.handle_uploads(
                    [SmallFileUpload("demo.json", "application/json", content)]
                )

            await user.should_see("Loaded: demo")
            assert config_controller.uploaded_content == content

    asyncio.run(simulate())
