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
        "editor_controller",
        type("EditorController", (), {"configuration": None})(),
    )
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
                current_config_checkbox = next(
                    iter(
                        ElementFilter(
                            kind=ui.checkbox,
                            content="Use current loaded configuration",
                        )
                    )
                )
                assert not current_config_checkbox.enabled
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


def test_current_editor_configuration_disables_upload_and_generates(
    monkeypatch,
):
    config = make_valid_config()
    editor_config_controller = type(
        "EditorController", (), {"configuration": config}
    )()
    monkeypatch.setattr(
        generator, "editor_controller", editor_config_controller
    )
    generation_calls = []

    def start_generation(*args):
        generation_calls.append(args)
        return config.limit, None

    monkeypatch.setattr(generator.controller, "start_generation", start_generation)

    async def simulate():
        async with user_simulation(root=generator.schedule_generator) as user:
            await user.open("/")
            with user.client:
                use_current_checkbox = next(
                    iter(
                        ElementFilter(
                            kind=ui.checkbox,
                            content="Use current loaded configuration",
                        )
                    )
                )
                load_button = next(
                    iter(
                        ElementFilter(
                            kind=ui.button,
                            content="Load configuration",
                        )
                    )
                )
                assert use_current_checkbox.enabled
                assert load_button.enabled

            user.find("Use current loaded configuration").click()

            with user.client:
                assert not load_button.enabled

            user.find("Generate Schedules").click()
            assert generation_calls
            assert generation_calls[0][0] == "current configuration"
            assert generation_calls[0][-1] is config

    asyncio.run(simulate())
