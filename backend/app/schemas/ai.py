from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class ConversationCreateRequest(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    context_type: str = Field("general", pattern="^(lesson|assessment|general)$")
    context_id: Optional[str] = None

class ConversationRenameRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)

class MessageResponse(BaseModel):
    id: str
    conversation_id: str
    role: str
    content: str
    sequence_number: int
    turn_id: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class ConversationResponse(BaseModel):
    id: str
    student_id: str
    title: Optional[str] = None
    context_type: str
    context_id: Optional[str] = None
    last_sequence_number: int
    last_turn_number: int
    created_at: datetime
    updated_at: datetime
    message_count: Optional[int] = None

    class Config:
        from_attributes = True

class ConversationListResponse(BaseModel):
    items: List[ConversationResponse]
    total: int
    limit: int
    offset: int

class ConversationHistoryResponse(BaseModel):
    conversation: ConversationResponse
    messages: List[MessageResponse]
    total_messages: int
    has_more: bool

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=10000)
    conversation_id: Optional[str] = None
    idempotency_key: Optional[str] = Field(None, min_length=1, max_length=128)
    context: Optional[Dict[str, Any]] = None

class ChatResponseData(BaseModel):
    response: str
    conversation_id: str
    turn_id: Optional[str] = None
    sequence_number: Optional[int] = None
    attempt_version: Optional[int] = 1
    tools_used: List[str] = []
    error: Optional[str] = None

class HintRequest(BaseModel):
    question_id: str
    lesson_id: Optional[str] = None
    student_answer: Optional[str] = None

class AnalyzeRequest(BaseModel):
    time_period_days: int = 30

class StudyPlanRequest(BaseModel):
    goal: str
    available_hours_per_day: float
    duration_days: int = 30
    subjects: Optional[List[str]] = None

class GenerateQuestionsRequest(BaseModel):
    subject_id: str
    topic: str
    difficulty: str = "beginner"
    count: int = 5

class AIResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    conversation_id: Optional[str] = None
