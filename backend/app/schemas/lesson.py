from pydantic import BaseModel
from typing import Optional, List, Any

class QuestionOptionResponse(BaseModel):
    id: str
    option_text: str
    display_order: int
    
    model_config = {"from_attributes": True}

class QuestionResponse(BaseModel):
    id: str
    question_text: str
    question_type: str
    difficulty: str
    hint: Optional[str] = None
    options: List[QuestionOptionResponse] = []
    
    model_config = {"from_attributes": True}

class LessonDetailResponse(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    content: Optional[str] = None
    lesson_type: str
    estimated_minutes: int
    questions: List[QuestionResponse] = []
    
    model_config = {"from_attributes": True}

class CompleteLessonResponse(BaseModel):
    success: bool
    message: str
    xp_earned: int
