import asyncio
from pathlib import Path

from nicegui import ElementFilter, ui
from nicegui.elements.upload_files import SmallFileUpload
from nicegui.testing import user_simulation

import src.views.schedule_generation_progress as progress_view
import src.views.schedule_generator as generator
from src.controllers.schedule_generator_controller import ScheduleGeneratorController
from src.models.schedule_generator_model import ScheduleGenerationState
from tests.conftest import active_client
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
            with active_client(user):
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

            with active_client(user):
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
    editor_config_controller = type("EditorController", (), {"configuration": config})()
    monkeypatch.setattr(generator, "editor_controller", editor_config_controller)
    generation_calls = []

    def start_generation(*args):
        generation_calls.append(args)
        return config.limit, None

    monkeypatch.setattr(generator.controller, "start_generation", start_generation)

    async def simulate():
        async with user_simulation(root=generator.schedule_generator) as user:
            await user.open("/")
            with active_client(user):
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

            with active_client(user):
                assert not load_button.enabled
                limit_override_inputs = list(
                    ElementFilter(
                        kind=ui.input,
                        content="Temporary Generation Limit Override",
                    )
                )
                assert len(limit_override_inputs) == 1
                limit_override_inputs[0].value = "25"

            user.find("Generate Schedules").click()
            assert generation_calls
            assert generation_calls[0][0] == "current configuration"
            assert generation_calls[0][1] == "25"
            assert generation_calls[0][-1] is config

    asyncio.run(simulate())


def test_progress_display_recovers_for_retries_after_no_solution(monkeypatch):
    controller = ScheduleGeneratorController()
    monkeypatch.setattr(generator, "controller", controller)

    class TestConfigurationController:
        def load_uploaded_configuration(self, _content):
            return controller.load_config("not_working")

    monkeypatch.setattr(generator, "ConfigurationController", TestConfigurationController)

    async def simulate():
        config_path = Path(generator.__file__).resolve().parents[1] / "configs" / "not_working.json"
        content = config_path.read_bytes()
        async with user_simulation(root=generator.schedule_generator) as user:
            await user.open("/")
            user.find("Load configuration").click()
            await user.should_see("Load Configuration")
            with active_client(user):
                upload = next(iter(ElementFilter(kind=ui.upload)))
                await upload.handle_uploads(
                    [SmallFileUpload("not_working.json", "application/json", content)]
                )
            await user.should_see("Loaded: not_working")

            for _ in range(2):
                generation_id = controller.state_snapshot().generation_id
                user.find("Generate Schedules").click()
                deadline = asyncio.get_running_loop().time() + 30
                while asyncio.get_running_loop().time() < deadline:
                    state = controller.state_snapshot()
                    if state.generation_id > generation_id and state.finished:
                        break
                    await asyncio.sleep(0.1)
                else:
                    raise TimeoutError("no-solution generation did not finish")
                await user.should_see(
                    "No valid schedule could be generated for this configuration.",
                    retries=10,
                )
                assert state.generation_id > generation_id
                assert state.finished
                assert not state.running
                assert state.generated == 0
                with active_client(user):
                    spinner = next(iter(ElementFilter(kind=ui.spinner)))
                    assert not spinner.visible

    asyncio.run(simulate())


def test_diagnosis_cancel_button_appears_after_sixty_seconds_and_allows_retry(monkeypatch):
    config = make_valid_config()
    clock = [100.0]
    monkeypatch.setattr(progress_view, "monotonic", lambda: clock[0])
    monkeypatch.setattr(
        generator,
        "editor_controller",
        type("EditorController", (), {"configuration": None})(),
    )

    class DiagnosisController:
        def __init__(self):
            self.generation_id = 0
            self.state = ScheduleGenerationState()

        def state_snapshot(self):
            return self.state

        def start_generation(self, *args):
            self.generation_id += 1
            self.state = ScheduleGenerationState(
                running=True,
                diagnosing=True,
                requested=config.limit,
                message="No schedules found. Analyzing constraints...",
                generation_id=self.generation_id,
            )
            return config.limit, None

        def cancel_diagnosis(self):
            self.state = ScheduleGenerationState(
                finished=True,
                diagnosis_cancelled=True,
                requested=config.limit,
                message="No valid schedules could be generated.",
                generation_id=self.generation_id,
            )
            return True

    controller = DiagnosisController()
    monkeypatch.setattr(generator, "controller", controller)

    class TestConfigurationController:
        def load_uploaded_configuration(self, _content):
            return config

    monkeypatch.setattr(generator, "ConfigurationController", TestConfigurationController)

    async def simulate():
        content = config.model_dump_json().encode()
        async with user_simulation(root=generator.schedule_generator) as user:
            await user.open("/")
            user.find("Load configuration").click()
            await user.should_see("Load Configuration")
            with active_client(user):
                upload = next(iter(ElementFilter(kind=ui.upload)))
                await upload.handle_uploads(
                    [SmallFileUpload("cancel-test.json", "application/json", content)]
                )
            await user.should_see("Loaded: cancel-test")
            user.find("Generate Schedules").click()
            await user.should_see("Analyzing schedule constraints...", retries=10)

            with active_client(user):
                cancel_button = next(
                    iter(
                        ElementFilter(
                            kind=ui.button,
                            content="Stop analysis and show no-solution result",
                        )
                    )
                )
                assert not cancel_button.visible

            clock[0] = 159.9
            await asyncio.sleep(0.3)
            assert not cancel_button.visible
            clock[0] = 160.1
            await user.should_see(
                kind=ui.button,
                content="Stop analysis and show no-solution result",
                retries=10,
            )
            assert cancel_button.visible
            user.find("Stop analysis and show no-solution result").click()
            await user.should_see("Constraint diagnosis was stopped.", retries=10)
            assert controller.state.finished
            assert not controller.state.running
            assert controller.state.diagnosis_cancelled

            user.find("Generate Schedules").click()
            assert controller.generation_id == 2

    asyncio.run(simulate())
