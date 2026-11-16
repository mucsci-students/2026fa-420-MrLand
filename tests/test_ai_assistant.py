import asyncio
from types import SimpleNamespace

import pytest
from nicegui.testing import user_simulation

from src.controllers.configuration_controller import ConfigurationController
from src.views import ai_assistant_conversation
from src.views.ai_assistant import scheduler_ai_assistant
from src.views.ai_assistant_conversation import AssistantConversation, AssistantConversationView
from tests.conftest import active_client


def _conversation_view(query):
    async def scroll():
        return None

    return AssistantConversationView(
        message_input=SimpleNamespace(value=query, disable=lambda: None, enable=lambda: None),
        send_button=SimpleNamespace(disable=lambda: None, enable=lambda: None),
        refresh_transcript=lambda: None,
        scroll_transcript_to_latest=scroll,
        progress_display=SimpleNamespace(reset=lambda: None, update=lambda _state: "complete"),
        confirmation_state={"future": None},
        confirmation_prompt=SimpleNamespace(set_text=lambda _text: None),
        confirmation_dialog=SimpleNamespace(open=lambda: None, close=lambda: None),
    )


def _conversation(controller):
    return AssistantConversation(
        controller,
        lambda **_kwargs: None,
        lambda: True,
        lambda name: name,
        None,
        None,
        None,
        None,
        None,
    )


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
                lambda name: name,
            )
        )

    async def simulate():
        async with user_simulation(root=root) as user:
            await user.open("/")
            with active_client(user):
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
                lambda name: name,
            )
        )

    async def simulate():
        async with user_simulation(root=root) as user:
            await user.open("/")
            with active_client(user):
                unlock_callbacks[0]("top_hat", "🎩")
            await user.should_see("🎩")
            with active_client(user):
                unlock_callbacks[0]("baseball_cap", "🧢")
            await user.should_see("🧢")
            await user.should_not_see("🎩")

    asyncio.run(simulate())


def test_assistant_conversation_ignores_empty_prompts():
    conversation = _conversation(ConfigurationController())
    view = _conversation_view("  ")

    asyncio.run(conversation.send_prompt("  ", view))

    assert conversation.messages == []


def test_assistant_conversation_reports_missing_api_key(monkeypatch):
    notices = []
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setattr(
        "src.views.ai_assistant_conversation.ui.notify",
        lambda *args, **kwargs: notices.append((args, kwargs)),
    )
    conversation = _conversation(ConfigurationController())

    asyncio.run(conversation.send_prompt("hello", _conversation_view("hello")))

    assert notices[0][0][0].startswith("No OpenAI API key found.")
    assert notices[0][1]["type"] == "warning"
    assert conversation.messages == []


def test_assistant_conversation_sends_query_and_displays_response(monkeypatch):
    captured = {}
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    def invoke(**kwargs):
        captured.update(kwargs)
        return {"messages": [SimpleNamespace(type="ai", text="Hello from scheduler AI")]}

    monkeypatch.setattr(ai_assistant_conversation, "invoke_scheduler_agent", invoke)
    conversation = _conversation(ConfigurationController())

    asyncio.run(conversation.send_prompt("hello", _conversation_view("hello")))

    assert captured["query"] == "hello"
    assert conversation.messages == [
        ("user", "hello"),
        ("assistant", "Hello from scheduler AI"),
    ]
