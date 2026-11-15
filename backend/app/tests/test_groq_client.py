import json
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import httpx
import pytest

from app.core.ai_client import (
    GroqAPIError,
    _GroqChat,
    _GroqModels,
    _GroqClient,
    get_genai_client,
)
from app.core.config import settings


@pytest.fixture
def groq_settings(monkeypatch):
    monkeypatch.setattr(settings, "AI_PROVIDER", "groq")
    monkeypatch.setattr(settings, "GROQ_API_KEY", "test-key")
    monkeypatch.setattr(settings, "GROQ_MODEL", "openai/gpt-oss-120b")
    monkeypatch.setattr(settings, "AI_TIMEOUT_SECONDS", 10)


def mock_response(payload, status_code=200):
    response = MagicMock()
    response.status_code = status_code
    response.json.return_value = payload
    response.raise_for_status.return_value = None
    return response


def test_get_client_returns_none_without_api_key(monkeypatch):
    monkeypatch.setattr(settings, "AI_PROVIDER", "groq")
    monkeypatch.setattr(settings, "GROQ_API_KEY", "")

    assert get_genai_client() is None


def test_get_client_rejects_unsupported_provider(monkeypatch):
    monkeypatch.setattr(settings, "AI_PROVIDER", "unsupported")
    monkeypatch.setattr(settings, "GROQ_API_KEY", "test-key")

    assert get_genai_client() is None


def test_models_generate_content_sends_groq_request(groq_settings):
    response = mock_response({
        "choices": [{"message": {"content": "Hello from Groq"}}]
    })

    with patch("app.core.ai_client.httpx.post", return_value=response) as post:
        result = _GroqModels().generate_content(
            model="openai/gpt-oss-120b",
            contents="Hello",
        )

    assert result.text == "Hello from Groq"
    args, kwargs = post.call_args
    assert args[0] == "https://api.groq.com/openai/v1/chat/completions"
    assert kwargs["headers"]["Authorization"] == "Bearer test-key"
    assert kwargs["json"]["model"] == "openai/gpt-oss-120b"
    assert kwargs["json"]["messages"] == [{"role": "user", "content": "Hello"}]


def test_chat_sends_system_prompt_and_user_message(groq_settings):
    response = mock_response({
        "choices": [{"message": {"content": "A helpful answer"}}]
    })
    config = SimpleNamespace(
        system_instruction="You are a tutor",
        tools=None,
    )
    chat = _GroqChat("openai/gpt-oss-120b", config)

    with patch("app.core.ai_client.httpx.post", return_value=response) as post:
        result = chat.send_message("Explain Python")

    assert result.text == "A helpful answer"
    messages = post.call_args.kwargs["json"]["messages"]
    assert messages[0] == {"role": "system", "content": "You are a tutor"}
    assert messages[1] == {"role": "user", "content": "Explain Python"}


def test_chat_parses_tool_calls(groq_settings):
    response = mock_response({
        "choices": [{
            "message": {
                "content": None,
                "tool_calls": [{
                    "id": "call_123",
                    "type": "function",
                    "function": {
                        "name": "calculate",
                        "arguments": '{"a": 2, "b": 3}',
                    },
                }],
            }
        }]
    })
    config = SimpleNamespace(
        system_instruction="You are a tutor",
        tools=[{"type": "function", "function": {"name": "calculate"}}],
    )
    chat = _GroqChat("openai/gpt-oss-120b", config)

    with patch("app.core.ai_client.httpx.post", return_value=response) as post:
        result = chat.send_message("Calculate 2 + 3")

    assert result.function_calls[0].id == "call_123"
    assert result.function_calls[0].name == "calculate"
    assert result.function_calls[0].args == {"a": 2, "b": 3}
    payload = post.call_args.kwargs["json"]
    assert payload["tool_choice"] == "auto"
    assert payload["tools"] == config.tools


def test_chat_sends_tool_response_with_correct_role(groq_settings):
    response = mock_response({
        "choices": [{"message": {"content": "The answer is 5."}}]
    })
    chat = _GroqChat("openai/gpt-oss-120b", None)

    with patch("app.core.ai_client.httpx.post", return_value=response) as post:
        result = chat.send_message([{
            "tool_call_id": "call_123",
            "content": json.dumps({"result": 5}),
        }])

    assert result.text == "The answer is 5."
    messages = post.call_args.kwargs["json"]["messages"]
    assert messages[0]["role"] == "tool"
    assert messages[0]["tool_call_id"] == "call_123"


def test_chat_rejects_invalid_tool_response():
    chat = _GroqChat("openai/gpt-oss-120b", None)

    with pytest.raises(ValueError, match="Unsupported tool response"):
        chat.send_message([{"content": "invalid"}])


def test_chat_requires_api_key(monkeypatch):
    monkeypatch.setattr(settings, "GROQ_API_KEY", "")
    chat = _GroqChat("openai/gpt-oss-120b", None)

    with pytest.raises(GroqAPIError, match="GROQ_API_KEY"):
        chat.send_message("Hello")


def test_models_requires_api_key(monkeypatch):
    monkeypatch.setattr(settings, "GROQ_API_KEY", "")

    with pytest.raises(GroqAPIError, match="GROQ_API_KEY"):
        _GroqModels().generate_content(contents="Hello")


def test_groq_http_error_preserves_status_code(groq_settings):
    request = httpx.Request(
        "POST",
        "https://api.groq.com/openai/v1/chat/completions",
    )
    response = httpx.Response(
        429,
        request=request,
        json={"error": {"message": "Rate limit reached"}},
    )
    error = httpx.HTTPStatusError(
        "Rate limit",
        request=request,
        response=response,
    )

    with patch("app.core.ai_client.httpx.post") as post:
        post.return_value.raise_for_status.side_effect = error

        with pytest.raises(GroqAPIError) as exc:
            _GroqModels._request(
                "openai/gpt-oss-120b",
                [{"role": "user", "content": "Hello"}],
            )

    assert exc.value.status_code == 429
    assert "Rate limit reached" in str(exc.value)


def test_groq_connection_error_is_wrapped(groq_settings):
    request = httpx.Request(
        "POST",
        "https://api.groq.com/openai/v1/chat/completions",
    )

    with patch(
        "app.core.ai_client.httpx.post",
        side_effect=httpx.ConnectError("Connection failed", request=request),
    ):
        with pytest.raises(GroqAPIError, match="Could not connect to Groq"):
            _GroqModels._request(
                "openai/gpt-oss-120b",
                [{"role": "user", "content": "Hello"}],
            )
