"""Friendly error messages for the Scheduler AI assistant.

Raw exception text from OpenAI can include request details or part of the API
key (for example "Incorrect API key provided: sk-ab***xyz"), so the GUI shows
these short messages instead. The full error is still written to the server log
so developers can debug it.
"""

from __future__ import annotations

import logging

import openai
from langchain_core.exceptions import LangChainException

logger = logging.getLogger(__name__)

MISSING_KEY_MESSAGE = (
    "No OpenAI API key found. Add OPENAI_API_KEY to the .env file in the "
    "project root, then restart the app."
)


def friendly_error_message(exc: BaseException) -> str:
    """Return a short, user-safe message describing why an AI request failed."""
    logger.error("Scheduler AI request failed", exc_info=exc)

    # OpenAI errors. Order matters: more specific classes come first
    # (APITimeoutError is a subclass of APIConnectionError, and all the
    # status errors are subclasses of APIStatusError).
    if isinstance(exc, openai.AuthenticationError):
        return (
            "The OpenAI API key was rejected. Check that the key in your .env "
            "file is correct and still active."
        )
    if isinstance(exc, openai.PermissionDeniedError):
        return "This OpenAI API key doesn't have permission to use the assistant's model."
    if isinstance(exc, openai.RateLimitError):
        if getattr(exc, "code", None) == "insufficient_quota":
            return "The OpenAI account is out of credits. Check the account's billing."
        return "Too many requests to OpenAI right now. Wait a moment and try again."
    if isinstance(exc, openai.NotFoundError):
        return "The AI model the assistant uses isn't available for this API key."
    if isinstance(exc, openai.APITimeoutError):
        return "OpenAI took too long to respond. Try again."
    if isinstance(exc, openai.APIConnectionError):
        return "Couldn't reach OpenAI. Check your internet connection and try again."
    if isinstance(exc, openai.InternalServerError):
        return "OpenAI is having problems right now. Try again in a few minutes."
    if isinstance(exc, openai.BadRequestError):
        return "OpenAI couldn't process that request. Try rephrasing your message."
    if isinstance(exc, openai.APIStatusError):
        return f"OpenAI returned an error (status {exc.status_code}). Try again."
    if isinstance(exc, openai.OpenAIError):
        return "Something went wrong talking to OpenAI. Try again."

    # Raised by build_scheduler_agent when no key is set.
    if isinstance(exc, ValueError) and "OPENAI_API_KEY" in str(exc):
        return MISSING_KEY_MESSAGE

    if isinstance(exc, LangChainException):
        return "The assistant had trouble handling the AI's response. Try again or rephrase."

    return "Something went wrong with the assistant. Try again."