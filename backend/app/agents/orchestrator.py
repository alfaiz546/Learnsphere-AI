import logging
import json
import uuid
import time
from typing import Optional, Dict, Any, List
from fastapi import HTTPException
from sqlalchemy.orm import Session
from types import SimpleNamespace
from app.agents.tool_registry import ToolRegistry
from app.core.config import settings
from app.core.ai_client import get_genai_client
from app.models.ai_conversation import AIConversation, AIMessage
from app.models.user import StudentProfile
from app.services.ai_persistence_service import AIPersistenceService
from app.services.progress_service import get_topic_analysis

logger = logging.getLogger(__name__)


def _is_ai_rate_limit_error(error: Exception) -> bool:
    status_code = getattr(error, "status_code", None)
    if status_code is None:
        status_code = getattr(error, "code", None)
    if callable(status_code):
        try:
            status_code = status_code()
        except Exception:
            pass

    message = str(error).lower()
    return (
        status_code == 429
        or "rate limit" in message
        or "rate_limit" in message
        or "quota" in message
        or "resource_exhausted" in message
    )

class AIAgentOrchestrator:
    def __init__(self, db: Session, student_id: uuid.UUID):
        self.db = db
        self.student_id = student_id
        self.tool_registry = ToolRegistry(db, student_id)
        self.persistence = AIPersistenceService(db)
        self.max_iterations = 5
        self.history_context_limit = 10  # Context budget: last 10 messages

    def run(
        self,
        user_message: str,
        context: Optional[Dict[str, Any]] = None,
        conversation_id: Optional[str] = None,
        idempotency_key: str = None
    ) -> Dict[str, Any]:
        """
        Orchestrates persistent, concurrency-safe AI chat interaction:
        - Resolves or creates conversation
        - Initiates turn transactionally (allocating user sequence number)
        - Injects historical conversation context within budget
        - Calls the configured AI provider with tool schemas
        - Completes turn transactionally (allocating assistant sequence number)
        - On failure, marks turn failed without burning sequence numbers

        idempotency_key is REQUIRED. The caller must supply a stable key per
        logical chat submission and reuse it for retries.
        """
        if not idempotency_key or not idempotency_key.strip():
            raise HTTPException(
                status_code=400,
                detail="idempotency_key is required for chat submissions"
            )
        # 1. Resolve or create conversation
        conv_uuid = None
        if conversation_id:
            try:
                conv_uuid = uuid.UUID(conversation_id)
            except ValueError:
                conv_uuid = None

        if conv_uuid:
            conv = self.db.query(AIConversation).filter(
                AIConversation.id == conv_uuid,
                AIConversation.student_id == self.student_id
            ).first()
            if not conv:
                conv = self.persistence.create_conversation(self.student_id, title=user_message[:50])
                conv_uuid = conv.id
        else:
            conv = self.persistence.create_conversation(self.student_id, title=user_message[:50])
            conv_uuid = conv.id

        # 2. Transactional Turn Initiation
        init_result = self.persistence.initiate_turn(
            student_id=self.student_id,
            conversation_id=conv_uuid,
            user_message_text=user_message,
            idempotency_key=idempotency_key,
            context=context
        )

        # Idempotent Replay shortcut
        if init_result.get("is_replay"):
            cached_data = init_result["response_data"]
            return {
                "response": cached_data.get("response", ""),
                "tools_used": cached_data.get("tools_used", []),
                "conversation_id": str(conv_uuid),
                "turn_id": init_result.get("turn_id"),
                "sequence_number": cached_data.get("sequence_number")
            }

        turn_id = uuid.UUID(init_result["turn_id"])
        rec_id = uuid.UUID(init_result["idempotency_record_id"])
        worker_token = init_result["worker_token"]

        return self._execute_turn_generation(
            conversation_id=conv_uuid,
            turn_id=turn_id,
            user_message=user_message,
            idempotency_record_id=rec_id,
            worker_token=worker_token,
            context=context
        )

    def execute_existing_turn(
        self,
        conversation_id: uuid.UUID,
        turn_id: uuid.UUID,
        user_message: str,
        idempotency_record_id: uuid.UUID,
        worker_token: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Executes AI generation for an existing (e.g., retried) turn.
        Reuses the existing turn ID, user message, idempotency record, and conversation.
        Does NOT call initiate_turn, avoiding duplicate messages or 409 generating-turn conflicts.
        """
        return self._execute_turn_generation(
            conversation_id=conversation_id,
            turn_id=turn_id,
            user_message=user_message,
            idempotency_record_id=idempotency_record_id,
            worker_token=worker_token,
            context=context
        )

    def _execute_turn_generation(
        self,
        conversation_id: uuid.UUID,
        turn_id: uuid.UUID,
        user_message: str,
        idempotency_record_id: uuid.UUID,
        worker_token: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Core turn execution:
        - Checks GenAI client availability
        - Fetches prior conversation history within budget (excluding current turn)
        - Executes AI chat session with tool calling
        - Completes turn transactionally on success
        - Marks turn failed transactionally on exception
        """
        # 3. Check AI client availability
        client = get_genai_client()
        if not client:
            error_msg = "⚠️ LearnSphere AI Tutor is ready, but GROQ_API_KEY is not configured yet. Please configure GROQ_API_KEY in your backend/.env file to enable live AI responses."
            self.persistence.fail_turn(
                conversation_id=conversation_id,
                turn_id=turn_id,
                idempotency_record_id=idempotency_record_id,
                error_code="GROQ_API_KEY_MISSING",
                error_message=error_msg
            )
            return {
                "response": error_msg,
                "tools_used": [],
                "conversation_id": str(conversation_id),
                "turn_id": str(turn_id),
                "error": "GROQ_API_KEY not configured",
                "is_placeholder": True,
            }

        # 4. Fetch prior conversation history within budget (excluding current message)
        prior_messages = (
            self.db.query(AIMessage)
            .filter(
                AIMessage.conversation_id == conversation_id,
                AIMessage.turn_id != turn_id  # Exclude current turn
            )
            .order_by(AIMessage.sequence_number.desc())
            .limit(self.history_context_limit)
            .all()
        )
        prior_messages.reverse()  # Chronological order

        system_prompt = self._build_system_prompt(context, prior_messages)
        tools_used = []
        final_response = ""

        # 5. AI Generation & Tool Execution with retry on 503
        max_retries = 3
        attempt = 0
        backoff = 0.5  # seconds
        while attempt < max_retries:
            try:
                tool_schemas = self.tool_registry.get_tool_schemas()
                groq_tools = self._convert_to_groq_tools(tool_schemas)

                config = SimpleNamespace(
                    system_instruction=system_prompt,
                    tools=groq_tools if groq_tools else None,
                    temperature=0.7
                )

                # Build multi-turn chat history for the AI provider
                chat = client.chats.create(
                    model=settings.GROQ_MODEL,
                    config=config
                )

                response = chat.send_message(user_message)
                iterations = 0
                while iterations < self.max_iterations:
                    iterations += 1

                    if response.function_calls:
                        tool_parts = []
                        for fc in response.function_calls:
                            tool_name = fc.name
                            tool_params = dict(fc.args) if fc.args else {}

                            logger.info(f"Agent executing tool: {tool_name} with params: {tool_params}")
                            tool_result = self.tool_registry.execute_tool(tool_name, tool_params)
                            tools_used.append(tool_name)

                            tool_parts.append({
                                "tool_call_id": fc.id,
                                "content": json.dumps({"result": tool_result}, default=str)
                            })

                        response = chat.send_message(tool_parts)
                        continue
                    else:
                        final_response = response.text if response.text else "I've reviewed your request and provided guidance."
                        break

                if not final_response:
                    final_response = "I've processed your request. Please check the results."

                # Successful turn – commit and return
                completion_data = self.persistence.complete_turn(
                    conversation_id=conversation_id,
                    turn_id=turn_id,
                    assistant_response_text=final_response,
                    idempotency_record_id=idempotency_record_id,
                    worker_token=worker_token,
                    tools_used=tools_used
                )
                return completion_data

            except Exception as e:
                # Detect HTTP status from the configured AI provider
                status_code = getattr(e, "code", None) or getattr(e, "status_code", None)
                if _is_ai_rate_limit_error(e):
                    friendly_msg = (
                        "Our AI Tutor has temporarily reached its usage limit. "
                        "Please try again later. Your learning progress is safe."
                    )
                    logger.warning("AI rate limit reached; no retry will be attempted.")
                    self.persistence.fail_turn(
                        conversation_id=conversation_id,
                        turn_id=turn_id,
                        idempotency_record_id=idempotency_record_id,
                        error_code="AI_RATE_LIMIT_EXCEEDED",
                        error_message=str(e),
                    )
                    return {
                        "response": friendly_msg,
                        "tools_used": tools_used,
                        "conversation_id": str(conversation_id),
                        "turn_id": str(turn_id),
                        "error": "AI rate limit exceeded",
                    }
                elif status_code == 503:
                    attempt += 1
                    if attempt >= max_retries:
                        # All retries exhausted – return a friendly placeholder response
                        friendly_msg = "Sorry, the AI service is temporarily unavailable. Please try again in a moment."
                        self.persistence.fail_turn(
                            conversation_id=conversation_id,
                            turn_id=turn_id,
                            idempotency_record_id=idempotency_record_id,
                            error_code="AI_SERVICE_UNAVAILABLE",
                            error_message=friendly_msg,
                        )
                        return {
                            "response": friendly_msg,
                            "tools_used": tools_used,
                            "conversation_id": str(conversation_id),
                            "turn_id": str(turn_id),
                            "error": "Service unavailable",
                        }
                    else:
                        logger.warning(f"AI service 503 encountered, retry {attempt}/{max_retries} after {backoff}s: {e}")
                        time.sleep(backoff)
                        backoff *= 2  # exponential backoff
                        continue
                else:
                    # Non‑retryable error – log and fail turn
                    logger.error(f"Agent turn exception (non‑retryable): {e}")
                    error_code = type(e).__name__
                    error_message = str(e)
                    self.persistence.fail_turn(
                        conversation_id=conversation_id,
                        turn_id=turn_id,
                        idempotency_record_id=idempotency_record_id,
                        error_code=error_code,
                        error_message=error_message,
                    )
                    return {
                        "response": f"I encountered an error processing your request: {error_message}",
                        "tools_used": tools_used,
                        "conversation_id": str(conversation_id),
                        "turn_id": str(turn_id),
                        "error": error_message,
                    }


    def _build_system_prompt(self, context: Optional[Dict] = None, prior_messages: Optional[List[AIMessage]] = None) -> str:
        base = """You are LearnSphere AI Mentor, an autonomous educational tutor inspired by Brilliant.org's interactive, problem-solving-based learning experience.
Your philosophy: 'Learn by Doing, Understand by Exploring, Improve with AI.'

Guidelines:
- Guide the student through discovery and reasoning rather than just blurting answers
- Give clear, concise, structured hints when requested
- Use analogies and step-by-step problem breakdown
- When the student asks to analyze their performance or generate a study plan, use your available tools
- Be warm, encouraging, and academically rigorous"""

        # Inject Student Academic Profile & Performance Context
        try:
            profile = self.db.query(StudentProfile).filter(StudentProfile.user_id == self.student_id).first()
            student_info = []
            if profile:
                if profile.current_class:
                    student_info.append(f"Current Class/Grade: {profile.current_class}")
                if profile.board:
                    student_info.append(f"Education Board: {profile.board}")
                if profile.current_marks:
                    student_info.append(f"Current Marks: {profile.current_marks}%")
                if profile.target_exam:
                    student_info.append(f"Target Exam: {profile.target_exam}")
                if profile.career_goal:
                    student_info.append(f"Career Goal: {profile.career_goal}")

            analysis = get_topic_analysis(self.db, self.student_id)
            if analysis.get("strong_topics"):
                strong_names = [f"{t['topic']} ({t['accuracy_rate']}%)" for t in analysis["strong_topics"][:3]]
                student_info.append(f"Mastered Topics: {', '.join(strong_names)}")
            if analysis.get("weak_topics"):
                weak_names = [f"{t['topic']} ({t['accuracy_rate']}%)" for t in analysis["weak_topics"][:3]]
                student_info.append(f"Weak Topics: {', '.join(weak_names)}")

            if student_info:
                base += "\n\nStudent Academic Profile & Performance State:\n" + "\n".join(student_info)
        except Exception as e:
            logger.warning(f"Failed to append student profile context: {e}")

        if context:
            ctx_parts = []
            if context.get("subject"):
                ctx_parts.append(f"Subject: {context['subject']}")
            if context.get("course"):
                ctx_parts.append(f"Course: {context['course']}")
            if context.get("lesson"):
                ctx_parts.append(f"Lesson: {context['lesson']}")
            if context.get("question"):
                ctx_parts.append(f"Current question: {context['question']}")
            if context.get("student_answer"):
                ctx_parts.append(f"Student's attempt: {context['student_answer']}")
            if ctx_parts:
                base += "\n\nCurrent Student Context:\n" + "\n".join(ctx_parts)

        if prior_messages:
            history_text = "\n\nRecent Conversation History:"
            for m in prior_messages:
                speaker = "Student" if m.role == "user" else "AI Mentor"
                history_text += f"\n- {speaker}: {m.content[:300]}"
            base += history_text

        return base

    def _convert_to_groq_tools(self, schemas: list) -> list:
        """Convert tool schemas to Groq's OpenAI-compatible format."""
        return [
            {
                "type": "function",
                "function": {
                    "name": schema["name"],
                    "description": schema["description"],
                    "parameters": schema.get("parameters", {
                        "type": "object",
                        "properties": {}
                    })
                }
            }
            for schema in schemas
        ]
