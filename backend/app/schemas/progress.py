from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class WeakTopicResponse(BaseModel):
    topic: str
    subject: str
    accuracy_rate: float
    attempts: int
    recommendation: str

class ProgressSummary(BaseModel):
    total_lessons: int
    completed_lessons: int
    completion_percentage: float
    total_xp: int
    current_streak: int
    enrolled_courses: int

class ProgressHistoryItem(BaseModel):
    lesson_title: str
    course_title: str
    completed_at: Optional[datetime] = None
    status: str
