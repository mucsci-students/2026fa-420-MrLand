"""Tests for the Scheduler AI friendly error messages."""

import httpx2
import openai
import pytest
from langchain_core.exceptions import LangChainException

from src.ai.api_errors import MISSING_KEY_MESSAGE, friendly_error_message

REQUEST = httpx2.Request("POST", "https://api.openai.com/v1/responses")


def status_error(error_class, status_code, message="error", body=None):
    """Build an OpenAI status error the same way the OpenAI client does."""
    response = httpx2.Response(status_code, request=REQUEST)
    return error_class(message, response=response, body=body)


@pytest.mark.parametrize(
    ("exc", "expected"),
    [
        (status_error(openai.AuthenticationError, 401), "key was rejected"),
        (status_error(openai.PermissionDeniedError, 403), "doesn't have permission"),
        (status_error(openai.RateLimitError, 429), "Too many requests"),
        (
            status_error(openai.RateLimitError, 429, body={"code": "insufficient_quota"}),
            "out of credits",
        ),
        (status_error(openai.NotFoundError, 404), "isn't available"),
        (status_error(openai.InternalServerError, 500), "having problems"),
        (status_error(openai.BadRequestError, 400), "rephrasing"),
        (status_error(openai.APIStatusError, 418), "status 418"),
        (openai.APITimeoutError(request=REQUEST), "too long"),
        (openai.APIConnectionError(request=REQUEST), "internet connection"),
        (openai.OpenAIError("boom"), "talking to OpenAI"),
        (LangChainException("bad output"), "trouble handling"),
        (RuntimeError("anything else"), "Something went wrong with the assistant"),
    ],
)
def test_friendly_messages(exc, expected):
    assert expected in friendly_error_message(exc)


def test_missing_key_value_error():
    exc = ValueError("OPENAI_API_KEY is not set. Add it to the .env file.")
    assert friendly_error_message(exc) == MISSING_KEY_MESSAGE


def test_other_value_error_is_generic():
    message = friendly_error_message(ValueError("some unrelated problem"))
    assert message == "Something went wrong with the assistant. Try again."


def test_api_key_is_never_shown():
    exc = status_error(
        openai.AuthenticationError,
        401,
        message="Incorrect API key provided: sk-secret123456",
    )
    assert "sk-secret" not in friendly_error_message(exc)
