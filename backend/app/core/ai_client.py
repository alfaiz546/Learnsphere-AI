
import json
import logging
from types import SimpleNamespace

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class GroqAPIError(Exception):
    def __init__(self, message, status_code=None):
        super().__init__(message)
        self.status_code = status_code
        self.code = status_code


class _GroqModels:
    def generate_content(self, *, model=None, contents, **kwargs):
        response = self._request(
            model=model or settings.GROQ_MODEL,
            messages=[{"role": "user", "content": str(contents)}],
        )
        return SimpleNamespace(text=response.get("content") or "")

    @staticmethod
    def _request(model, messages):
        if not settings.GROQ_API_KEY:
            raise GroqAPIError("GROQ_API_KEY is not configured.")

        try:
            response = httpx.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.GROQ_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "messages": messages,
                    "temperature": 0.7,
                },
                timeout=settings.AI_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]

        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code
            try:
                detail = exc.response.json().get("error", {}).get("message", "")
            except Exception:
                detail = exc.response.text[:500]
            raise GroqAPIError(
                detail or f"Groq API returned HTTP {status}",
                status,
            ) from exc
        except httpx.RequestError as exc:
            raise GroqAPIError(f"Could not connect to Groq: {exc}") from exc


class _GroqChat:
    def __init__(self, model, config):
        self.model = model or settings.GROQ_MODEL
        self.messages = []
        self.tools = getattr(config, "tools", None) if config else None

        system_instruction = (
            getattr(config, "system_instruction", None) if config else None
        )
        if system_instruction:
            self.messages.append({
                "role": "system",
                "content": system_instruction,
            })

    def send_message(self, content):
        if isinstance(content, str):
            self.messages.append({"role": "user", "content": content})
        elif isinstance(content, list):
            for item in content:
                if isinstance(item, dict) and item.get("tool_call_id"):
                    self.messages.append({
                        "role": "tool",
                        "tool_call_id": item["tool_call_id"],
                        "content": str(item.get("content", "")),
                    })
                else:
                    raise ValueError("Unsupported tool response format.")
        else:
            raise ValueError("Message must be text or a list of tool responses.")

        payload = {
            "model": self.model,
            "messages": self.messages,
            "temperature": 0.7,
        }
        if self.tools:
            payload["tools"] = self.tools
            payload["tool_choice"] = "auto"

        if not settings.GROQ_API_KEY:
            raise GroqAPIError("GROQ_API_KEY is not configured.")

        try:
            response = httpx.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.GROQ_API_KEY}",
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=settings.AI_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
            data = response.json()
            message = data["choices"][0]["message"]

        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code
            try:
                detail = exc.response.json().get("error", {}).get("message", "")
            except Exception:
                detail = exc.response.text[:500]
            raise GroqAPIError(
                detail or f"Groq API returned HTTP {status}",
                status,
            ) from exc
        except httpx.RequestError as exc:
            raise GroqAPIError(f"Could not connect to Groq: {exc}") from exc

        self.messages.append(message)

        function_calls = []
        for call in message.get("tool_calls") or []:
            function = call.get("function", {})
            try:
                args = json.loads(function.get("arguments") or "{}")
            except json.JSONDecodeError:
                args = {}

            function_calls.append(SimpleNamespace(
                id=call.get("id"),
                name=function.get("name"),
                args=args,
            ))

        return SimpleNamespace(
            text=message.get("content") or "",
            function_calls=function_calls or None,
        )


class _GroqChats:
    def create(self, *, model=None, config=None):
        return _GroqChat(model, config)


class _GroqClient:
    def __init__(self):
        self.models = _GroqModels()
        self.chats = _GroqChats()


_groq_client = None


def get_genai_client():
    """Return the configured Groq client, or None if its API key is missing."""
    global _groq_client

    if settings.AI_PROVIDER.lower() != "groq":
        logger.error("Unsupported AI provider: %s", settings.AI_PROVIDER)
        return None

    if not settings.GROQ_API_KEY:
        logger.warning("GROQ_API_KEY is not configured.")
        return None

    if _groq_client is None:
        _groq_client = _GroqClient()

    return _groq_client
