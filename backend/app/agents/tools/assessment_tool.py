from sqlalchemy.orm import Session
from app.models.question import Question
from app.services.assessment_service import _check_answer
import uuid

def assess_answer(db: Session, student_id: uuid.UUID, question_id: str, student_answer: str, assessment_id: str = None) -> dict:
    question = db.query(Question).filter(Question.id == uuid.UUID(question_id)).first()
    if not question:
        return {"error": "Question not found"}
    is_correct = _check_answer(question, student_answer)
    return {
        "question_id": question_id,
        "is_correct": is_correct,
        "correct_answer": question.correct_answer,
        "explanation": question.explanation,
        "hint": question.hint
    }
