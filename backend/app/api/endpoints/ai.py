import uuid
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.database.base import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.agents.orchestrator import AIAgentOrchestrator
from app.agents.tools.tutor_tool import get_tutor_explanation
from app.agents.tools.weakness_tool import analyze_weaknesses
from app.agents.tools.study_plan_tool import generate_study_plan
from app.services.ai_persistence_service import AIPersistenceService
from app.services.signing_key_service import signing_key_service
from app.schemas.ai import (
    ChatRequest, HintRequest, AnalyzeRequest, StudyPlanRequest,
    ConversationCreateRequest, ConversationRenameRequest,
    ConversationResponse, ConversationListResponse,
    ConversationHistoryResponse, MessageResponse
)
from app.core.config import settings
from app.core.ai_client import get_genai_client

router = APIRouter(prefix="/ai", tags=["ai"])

# ---------------------------------------------------------------------------
# Conversation Management Endpoints
# ---------------------------------------------------------------------------
@router.post("/conversations", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
def create_conversation(
    request: ConversationCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Creates a new AI chat conversation for the authenticated student."""
    persistence = AIPersistenceService(db)
    ctx_id = None
    if request.context_id:
        try:
            ctx_id = uuid.UUID(request.context_id)
        except ValueError:
            pass

    conv = persistence.create_conversation(
        student_id=current_user.id,
        title=request.title,
        context_type=request.context_type,
        context_id=ctx_id
    )

    return {
        "success": True,
        "data": {
            "id": str(conv.id),
            "student_id": str(conv.student_id),
            "title": conv.title,
            "context_type": conv.context_type,
            "context_id": str(conv.context_id) if conv.context_id else None,
            "last_sequence_number": conv.last_sequence_number,
            "last_turn_number": conv.last_turn_number,
            "created_at": conv.created_at.isoformat(),
            "updated_at": conv.updated_at.isoformat()
        }
    }

@router.get("/conversations", response_model=Dict[str, Any])
def list_conversations(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lists conversations for the authenticated student with pagination."""
    persistence = AIPersistenceService(db)
    items, total = persistence.list_conversations(
        student_id=current_user.id,
        limit=limit,
        offset=offset
    )

    return {
        "success": True,
        "data": {
            "items": [
                {
                    "id": str(c.id),
                    "student_id": str(c.student_id),
                    "title": c.title,
                    "context_type": c.context_type,
                    "context_id": str(c.context_id) if c.context_id else None,
                    "last_sequence_number": c.last_sequence_number,
                    "last_turn_number": c.last_turn_number,
                    "created_at": c.created_at.isoformat(),
                    "updated_at": c.updated_at.isoformat()
                }
                for c in items
            ],
            "total": total,
            "limit": limit,
            "offset": offset
        }
    }

@router.get("/conversations/{conversation_id}", response_model=Dict[str, Any])
def get_conversation_history(
    conversation_id: str,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieves conversation details and paginated message history."""
    try:
        conv_uuid = uuid.UUID(conversation_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid conversation ID format")

    persistence = AIPersistenceService(db)
    conv, messages, total_messages, has_more = persistence.get_conversation_history(
        student_id=current_user.id,
        conversation_id=conv_uuid,
        limit=limit,
        offset=offset
    )

    return {
        "success": True,
        "data": {
            "conversation": {
                "id": str(conv.id),
                "student_id": str(conv.student_id),
                "title": conv.title,
                "context_type": conv.context_type,
                "context_id": str(conv.context_id) if conv.context_id else None,
                "last_sequence_number": conv.last_sequence_number,
                "last_turn_number": conv.last_turn_number,
                "created_at": conv.created_at.isoformat(),
                "updated_at": conv.updated_at.isoformat()
            },
            "messages": [
                {
                    "id": str(m.id),
                    "conversation_id": str(m.conversation_id),
                    "role": m.role,
                    "content": m.content,
                    "sequence_number": m.sequence_number,
                    "turn_id": str(m.turn_id) if m.turn_id else None,
                    "created_at": m.created_at.isoformat()
                }
                for m in messages
            ],
            "total_messages": total_messages,
            "has_more": has_more
        }
    }

@router.patch("/conversations/{conversation_id}", response_model=Dict[str, Any])
def rename_conversation(
    conversation_id: str,
    request: ConversationRenameRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Renames an existing conversation with ownership validation."""
    try:
        conv_uuid = uuid.UUID(conversation_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid conversation ID format")

    persistence = AIPersistenceService(db)
    conv = persistence.rename_conversation(
        student_id=current_user.id,
        conversation_id=conv_uuid,
        new_title=request.title
    )

    return {
        "success": True,
        "data": {
            "id": str(conv.id),
            "title": conv.title,
            "updated_at": conv.updated_at.isoformat()
        }
    }

@router.delete("/conversations/{conversation_id}", response_model=Dict[str, Any])
def delete_conversation(
    conversation_id: str,
    token_data: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Deletes a conversation and cascades all messages, turns, and idempotency records.

    Security model: A valid signed deletion token is REQUIRED. Obtain one via
    POST /ai/conversations/{id}/deletion-token. The token binds student_id,
    conversation_id, nonce, iat/exp and an HMAC signature. verify_and_consume_token()
    enforces single-use nonce replay protection and 60-second expiry. Ownership
    is verified before the token is issued, and CSRF protection (double-submit)
    additionally guards browser clients.
    """
    try:
        conv_uuid = uuid.UUID(conversation_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid conversation ID format")

    persistence = AIPersistenceService(db)
    persistence.delete_conversation(
        student_id=current_user.id,
        conversation_id=conv_uuid,
        token_data=token_data
    )

    return {"success": True, "message": "Conversation deleted successfully"}

@router.post("/turns/{turn_id}/retry", response_model=Dict[str, Any])
def retry_turn(
    turn_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retries a failed turn with attempt version increment."""
    try:
        turn_uuid = uuid.UUID(turn_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid turn ID format")

    persistence = AIPersistenceService(db)
    retry_result = persistence.retry_turn(
        student_id=current_user.id,
        turn_id=turn_uuid
    )

    # Re-execute AI generation for the existing retried turn (without re-initiating or creating new messages)
    orchestrator = AIAgentOrchestrator(db, current_user.id)
    chat_result = orchestrator.execute_existing_turn(
        conversation_id=uuid.UUID(retry_result["conversation_id"]),
        turn_id=turn_uuid,
        user_message=retry_result["user_message"],
        idempotency_record_id=uuid.UUID(retry_result["idempotency_record_id"]),
        worker_token=retry_result["worker_token"]
    )

    return {"success": True, "data": chat_result}

@router.post("/admin/cleanup", response_model=Dict[str, Any])
def cleanup_expired_records(
    batch_size: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Administrative / maintenance endpoint: purges expired terminal idempotency records and used nonces.
    """
    persistence = AIPersistenceService(db)
    result = persistence.cleanup_expired_records(batch_size=batch_size)
    return {"success": True, "data": result}


@router.post(
    "/conversations/{conversation_id}/deletion-token",
    response_model=Dict[str, Any],
)
def generate_deletion_token(
    conversation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Issues a signed, short-lived (60s) deletion authorization token for a
    conversation owned by the authenticated student.

    Security model: DELETE /ai/conversations/{id} requires either:
      (a) a valid signed deletion token (recommended for all clients), or
      (b) ownership + CSRF protection for browser clients (enforced by
          get_current_user's double-submit CSRF validation).

    The token binds student_id, conversation_id, nonce, iat/exp and an
    HMAC signature. verify_and_consume_token() enforces single-use nonce
    replay protection and 60-second expiry.
    """
    try:
        conv_uuid = uuid.UUID(conversation_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid conversation ID format")

    # Verify ownership before issuing a token
    persistence = AIPersistenceService(db)
    conv = persistence.get_conversation_ownership(current_user.id, conv_uuid)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found or unauthorized")

    token_data = signing_key_service.generate_deletion_token(
        student_id=current_user.id,
        conversation_id=conv_uuid,
        db=db,
    )
    return {"success": True, "data": token_data}


# ---------------------------------------------------------------------------
# Core Chat & Tutoring Endpoints
# ---------------------------------------------------------------------------
@router.post("/chat")
def chat(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Sends a message in an existing or new conversation with idempotency protection."""
    orchestrator = AIAgentOrchestrator(db, current_user.id)
    result = orchestrator.run(
        user_message=request.message,
        context=request.context,
        conversation_id=request.conversation_id,
        idempotency_key=request.idempotency_key
    )
    return {"success": True, "data": result}

@router.post("/hint")
def get_hint(request: HintRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = get_tutor_explanation(
        db, current_user.id,
        concept=f"Hint for question {request.question_id}",
        question_id=request.question_id,
        student_misconception=request.student_answer
    )
    if result.get("error") and not result.get("explanation"):
        return {
            "success": True,
            "data": {
                "hint": "Analyze the core definitions involved in this question. Check if each given constraint is satisfied step-by-step!"
            }
        }
    return {"success": True, "data": {"hint": result.get("explanation", "")}}

@router.post("/analyze")
def analyze(request: AnalyzeRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = analyze_weaknesses(db, current_user.id, request.time_period_days)
    return {"success": True, "data": result}

@router.post("/study-plan")
def create_study_plan(request: StudyPlanRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    weaknesses = analyze_weaknesses(db, current_user.id)
    weak_topics = [t["topic"] for t in weaknesses.get("weak_topics", [])]
    
    result = generate_study_plan(
        db, current_user.id,
        goal=request.goal,
        available_hours_per_day=request.available_hours_per_day,
        duration_days=request.duration_days,
        weak_topics=weak_topics
    )
    
    summary_text = None
    if request.goal:
        client = get_genai_client()
        if client:
            try:
                prompt = f"Provide a motivating 2-sentence summary for a student working toward: {request.goal}"
                res = client.models.generate_content(
                    model=settings.GROQ_MODEL,
                    contents=prompt
                )
                summary_text = res.text
            except Exception:
                pass
    
    if not summary_text:
        summary_text = f"Structured {request.duration_days}-day study plan tailored to your goal: '{request.goal}'. Follow the recommended daily sessions to systematically build topic mastery."
    
    result["ai_summary"] = summary_text
    
    return {"success": True, "data": result}

@router.get("/study-plan/current")
def get_current_study_plan(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    from app.models.progress import StudyPlan
    from sqlalchemy import desc
    import json
    
    plan = (
        db.query(StudyPlan)
        .filter(StudyPlan.student_id == current_user.id)
        .order_by(desc(StudyPlan.created_at))
        .first()
    )
    if not plan:
        return {"success": True, "data": None}
    
    plan_dict = {}
    if plan.plan_data:
        try:
            plan_dict = json.loads(plan.plan_data)
        except Exception:
            plan_dict = {}
            
    return {
        "success": True,
        "data": {
            "plan_id": str(plan.id),
            "title": plan.title,
            "description": plan.description,
            "plan_type": plan.plan_type,
            "plan_data": plan_dict,
            "ai_summary": plan.description or f"Active {plan.plan_type.replace('_', ' ')} study plan.",
            "created_at": plan.created_at.isoformat() if plan.created_at else None,
            "starts_at": plan.starts_at.isoformat() if plan.starts_at else None,
            "ends_at": plan.ends_at.isoformat() if plan.ends_at else None,
        }
    }

@router.post("/generate-questions")
def gen_questions(request: dict, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    from app.agents.tools.question_generator import generate_questions
    result = generate_questions(db, current_user.id, **request)
    return {"success": True, "data": result}
