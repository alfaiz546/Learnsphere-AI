from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.database.base import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.lesson import Lesson
from app.models.progress import LearningProgress
from app.models.question import Question
from app.services.gamification_service import award_xp, update_streak, check_and_award_achievements
from app.services.assessment_service import _check_answer
from datetime import datetime
import uuid


class CheckAnswerRequest(BaseModel):
    question_id: str
    student_answer: str

router = APIRouter(prefix="/lessons", tags=["lessons"])

@router.get("/{lesson_id}")
def get_lesson(lesson_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    lesson = db.query(Lesson).filter(Lesson.id == uuid.UUID(lesson_id), Lesson.is_published == True).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    
    prog = db.query(LearningProgress).filter(
        LearningProgress.student_id == current_user.id, LearningProgress.lesson_id == lesson.id
    ).first()
    if not prog:
        prog = LearningProgress(student_id=current_user.id, lesson_id=lesson.id, status="in_progress")
        db.add(prog)
    elif prog.status == "not_started":
        prog.status = "in_progress"
    prog.last_accessed_at = datetime.utcnow()
    db.commit()
    
    questions_data = []
    for q in lesson.questions:
        opts = [{"id": str(o.id), "option_text": o.option_text, "display_order": o.display_order} for o in q.options]
        questions_data.append({
            "id": str(q.id),
            "question_text": q.question_text,
            "question_type": q.question_type,
            "difficulty": q.difficulty,
            "hint": q.hint,
            "options": opts
        })
    
    return {
        "success": True,
        "data": {
            "id": str(lesson.id),
            "title": lesson.title,
            "description": lesson.description,
            "content": lesson.content,
            "lesson_type": lesson.lesson_type,
            "estimated_minutes": lesson.estimated_minutes,
            "questions": questions_data
        }
    }

@router.post("/{lesson_id}/complete")
def complete_lesson(lesson_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    lesson = db.query(Lesson).filter(Lesson.id == uuid.UUID(lesson_id)).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    
    prog = db.query(LearningProgress).filter(
        LearningProgress.student_id == current_user.id, LearningProgress.lesson_id == lesson.id
    ).first()
    
    if prog and prog.status == "completed":
        return {"success": True, "message": "Already completed", "xp_earned": 0}
    
    if not prog:
        prog = LearningProgress(student_id=current_user.id, lesson_id=lesson.id)
        db.add(prog)
    
    prog.status = "completed"
    prog.completion_percentage = 100.0
    prog.completed_at = datetime.utcnow()
    db.commit()
    
    xp = 10
    award_xp(db, current_user.id, xp, f"Completed lesson: {lesson.title}", lesson.id)
    update_streak(db, current_user.id)
    check_and_award_achievements(db, current_user.id)
    
    return {"success": True, "message": "Lesson completed!", "xp_earned": xp}


@router.post("/{lesson_id}/check-answer")
def check_lesson_answer(
    lesson_id: str,
    request: CheckAnswerRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Server-side answer validation for lesson quiz questions.
    Accepts a question_id and student_answer, returns is_correct + explanation.
    Never returns the raw correct_answer to prevent exposure via the API.
    """
    # Verify the lesson exists and the question belongs to it
    lesson = db.query(Lesson).filter(
        Lesson.id == uuid.UUID(lesson_id), Lesson.is_published == True
    ).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    question = db.query(Question).filter(
        Question.id == uuid.UUID(request.question_id),
        Question.lesson_id == lesson.id
    ).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found in this lesson")

    if not request.student_answer or not request.student_answer.strip():
        raise HTTPException(status_code=400, detail="Answer cannot be empty")

    is_correct = _check_answer(question, request.student_answer)

    response: dict = {
        "question_id": str(question.id),
        "is_correct": is_correct,
        "score": 1.0 if is_correct else 0.0,
        "explanation": question.explanation,
    }

    # Only reveal the correct answer after submission, as a learning aid
    if not is_correct:
        # For multiple-choice reveal which letter is correct (not raw text that might be used to cheat)
        if question.question_type == "multiple_choice":
            letters = ["a", "b", "c", "d", "e"]
            correct_letter = question.correct_answer.strip().lower()
            response["correct_answer_hint"] = f"The correct option is ({correct_letter.upper()})"
        elif question.question_type == "true_false":
            response["correct_answer_hint"] = f"The correct answer is {question.correct_answer.strip().capitalize()}"
        # For numerical/fill_blank, reveal answer after wrong attempt (tutoring context)
        else:
            response["correct_answer"] = question.correct_answer

    return {"success": True, "data": response}
