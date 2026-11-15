from pydantic import BaseModel
from typing import Optional, List

class StartAssessmentRequest(BaseModel):
    lesson_id: Optional[str] = None
    course_id: Optional[str] = None

class AnswerSubmit(BaseModel):
    question_id: str
    student_answer: str
    time_taken_seconds: int = 0

class SubmitAssessmentRequest(BaseModel):
    assessment_id: str
    answers: List[AnswerSubmit]

class AnswerResult(BaseModel):
    question_id: str
    is_correct: bool
    score: float
    correct_answer: str
    explanation: Optional[str] = None

class AssessmentResultResponse(BaseModel):
    assessment_id: str
    total_questions: int
    correct_answers: int
    score_percentage: float
    xp_earned: int
    answers: List[AnswerResult] = []
