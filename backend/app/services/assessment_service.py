from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.assessment import Assessment, StudentAnswer, AssessmentResult
from app.models.question import Question
from app.models.subject import Subject
from app.schemas.assessment import StartAssessmentRequest, SubmitAssessmentRequest
from app.services.gamification_service import award_xp, update_streak, check_and_award_achievements
from datetime import datetime, timedelta
import uuid
import json
import logging

logger = logging.getLogger(__name__)

def start_assessment(db: Session, student_id, request: StartAssessmentRequest) -> dict:
    assessment = Assessment(
        student_id=student_id,
        lesson_id=uuid.UUID(request.lesson_id) if request.lesson_id else None,
        course_id=uuid.UUID(request.course_id) if request.course_id else None,
        status="in_progress"
    )
    db.add(assessment)
    db.commit()
    db.refresh(assessment)
    return {"assessment_id": str(assessment.id)}

def submit_assessment(db: Session, student_id, request: SubmitAssessmentRequest) -> dict:
    assessment = db.query(Assessment).filter(
        Assessment.id == uuid.UUID(request.assessment_id),
        Assessment.student_id == student_id
    ).first()
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    if assessment.status == "completed":
        raise HTTPException(status_code=400, detail="Assessment already completed")
    
    answers_result = []
    correct_count = 0
    
    for ans in request.answers:
        question = db.query(Question).filter(Question.id == uuid.UUID(ans.question_id)).first()
        if not question:
            continue
        
        is_correct = _check_answer(question, ans.student_answer)
        score = 1.0 if is_correct else 0.0
        if is_correct:
            correct_count += 1
        
        existing = db.query(StudentAnswer).filter(
            StudentAnswer.assessment_id == assessment.id,
            StudentAnswer.question_id == question.id
        ).first()
        
        attempt_num = existing.attempt_number + 1 if existing else 1
        
        student_answer = StudentAnswer(
            assessment_id=assessment.id,
            question_id=question.id,
            student_answer=ans.student_answer,
            is_correct=is_correct,
            score=score,
            time_taken_seconds=ans.time_taken_seconds,
            attempt_number=attempt_num
        )
        db.add(student_answer)
        
        answers_result.append({
            "question_id": str(question.id),
            "is_correct": is_correct,
            "score": score,
            "correct_answer": question.correct_answer,
            "explanation": question.explanation
        })
    
    total = len(request.answers)
    score_pct = (correct_count / total * 100) if total > 0 else 0.0
    xp_earned = _calculate_xp(score_pct, total)
    
    assessment.status = "completed"
    assessment.completed_at = datetime.utcnow()
    
    result = AssessmentResult(
        assessment_id=assessment.id,
        total_questions=total,
        correct_answers=correct_count,
        score_percentage=score_pct,
        xp_earned=xp_earned
    )
    db.add(result)
    db.commit()
    
    award_xp(db, student_id, xp_earned, "Assessment completed", assessment.id)
    update_streak(db, student_id)
    check_and_award_achievements(db, student_id)
    
    return {
        "assessment_id": str(assessment.id),
        "total_questions": total,
        "correct_answers": correct_count,
        "score_percentage": score_pct,
        "xp_earned": xp_earned,
        "answers": answers_result
    }

def _check_answer(question: Question, student_answer: str) -> bool:
    correct = question.correct_answer.strip().lower()
    given = student_answer.strip().lower()
    if question.question_type == "multiple_choice":
        if given == correct:
            return True
        letters = ["a", "b", "c", "d", "e"]
        for opt in question.options:
            opt_letter = letters[opt.display_order] if opt.display_order < len(letters) else ""
            if given == str(opt.id).lower() or given == opt.option_text.strip().lower() or given == opt_letter:
                if opt.is_correct or opt_letter == correct:
                    return True
        return False
    elif question.question_type == "true_false":
        return given in ["true", "false"] and given == correct
    elif question.question_type == "numerical":
        try:
            return abs(float(given) - float(correct)) < 0.01
        except ValueError:
            return False
    elif question.question_type == "fill_blank":
        return given == correct
    return False

def _calculate_xp(score_pct: float, total_questions: int) -> int:
    base = total_questions * 10
    if score_pct >= 90:
        return int(base * 1.5)
    elif score_pct >= 70:
        return int(base * 1.0)
    elif score_pct >= 50:
        return int(base * 0.6)
    else:
        return int(base * 0.2)
