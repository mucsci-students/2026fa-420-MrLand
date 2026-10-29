import asyncio

import pytest
from nicegui.testing import user_simulation

from src.controllers.configuration_controller import ConfigurationController
from src.views.ai_assistant import scheduler_ai_assistant


@pytest.mark.parametrize(
    ("combination_name", "emoji"),
    [
        ("top_hat", "🎩"),
        ("baseball_cap", "🧢"),
        ("flower_crown", "👑"),
        ("new_combination", "🪄"),
    ],
)
def test_unlock_assistant_displays_combination_hat(combination_name, emoji):
    unlock_callbacks = []

    def root():
        unlock_callbacks.append(
            scheduler_ai_assistant(
                ConfigurationController(),
                lambda *_args, **_kwargs: None,
                lambda: True,
            )
        )

    async def simulate():
        async with user_simulation(root=root) as user:
            await user.open("/")
            with user.client:
                unlock_callbacks[0](combination_name, emoji)
            await user.should_see(emoji)

    asyncio.run(simulate())


def test_unlocking_another_combination_updates_the_hat():
    unlock_callbacks = []

    def root():
        unlock_callbacks.append(
            scheduler_ai_assistant(
                ConfigurationController(),
                lambda *_args, **_kwargs: None,
                lambda: True,
            )
        )

    async def simulate():
        async with user_simulation(root=root) as user:
            await user.open("/")
            with user.client:
                unlock_callbacks[0]("top_hat", "🎩")
            await user.should_see("🎩")
            with user.client:
                unlock_callbacks[0]("baseball_cap", "🧢")
            await user.should_see("🧢")
            await user.should_not_see("🎩")

    asyncio.run(simulate())
