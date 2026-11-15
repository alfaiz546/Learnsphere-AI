import logging
from typing import Optional
from app.core.config import settings

logger = logging.getLogger(__name__)

# Attempt to import the official Google Generative AI library.
try:
    import google.generativeai as genai
except Exception as e:  # pragma: no cover – import may fail in test environments.
    logger.warning(f"google.generativeai import failed: {e}. Falling back to a mock client.")
    genai = None

# Simple mock implementation that satisfies the minimal interface used by the orchestrator.
class _MockChat:
    def send_message(self, *args, **kwargs):
        class _Resp:
            text = "Mock AI response"
            function_calls = None
        return _Resp()

class _RealGenAIClient:
    """Adapter for the real google.generativeai SDK to match the expected interface.
    Provides a ``chats.create`` method that returns a chat session with ``send_message``.
    ``config`` is a ``types.GenerateContentConfig`` instance; we extract the system instruction
    and ignore tools/temperature for now (tools are not required for the basic verification).
    """
    def __init__(self, *args, **kwargs):
        pass

    class _Chats:
        def __init__(self, genai_module):
            self.genai = genai_module

        def create(self, *, model: str, config=None):
            # Extract system instruction if provided
            system_instruction = None
            if config is not None:
                system_instruction = getattr(config, "system_instruction", None)
            # Initialize the GenerativeModel with optional system instruction
            generative_model = self.genai.GenerativeModel(
                model_name=model,
                system_instruction=system_instruction,
            )
            chat = generative_model.start_chat()
            return _RealGenAIClient._ChatWrapper(chat)

    @property
    def chats(self):
        return _RealGenAIClient._Chats(genai)

    class _ChatWrapper:
        def __init__(self, chat_session):
            self.chat = chat_session

        def send_message(self, content):
            # Content may be a string or a list of Parts; convert to a string for simplicity
            if isinstance(content, list):
                # Convert each Part to its string representation
                try:
                    content_str = "".join(str(part) for part in content)
                except Exception:
                    content_str = " ".join(str(part) for part in content)
            else:
                content_str = content
            response = self.chat.send_message(content_str)
            # Wrap response to expose .text and .function_calls attributes expected by orchestrator
            class _ResponseWrapper:
                def __init__(self, resp):
                    self.text = getattr(resp, "text", None)
                    self.function_calls = getattr(resp, "function_calls", None)
            return _ResponseWrapper(response)



_genai_client: Optional[object] = None

def get_genai_client() -> Optional[object]:
    """Return a singleton instance of the Google Generative AI client (or a mock).

    The orchestrator only needs a ``chats.create`` method that returns an object with a
    ``send_message`` method. If the real library cannot be imported or the API key is not
    configured, a lightweight mock client is provided so that the rest of the backend can
    operate without raising import errors.
    """
    global _genai_client
    # If a real API key is provided and the library is available, attempt to configure it.
    if settings.GEMINI_API_KEY and genai is not None:
        if _genai_client is None:
            try:
                genai.configure(api_key=settings.GEMINI_API_KEY)
                _genai_client = _RealGenAIClient()
            except Exception as e:
                logger.error(f"Failed to initialize Google GenerativeAI client: {e}")
                _genai_client = _MockGenAIClient()
        return _genai_client
    # Fallback to mock client when no key or library unavailable.
    if _genai_client is None:
        _genai_client = _MockGenAIClient()
    return _genai_client
