from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.base import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.assessment import Assessment, AssessmentResult
from app.models.question import Question
from app.models.subject import Subject
from app.schemas.assessment import StartAssessmentRequest, SubmitAssessmentRequest
from app.services.assessment_service import start_assessment, submit_assessment
from sqlalchemy import desc
import uuid
import json

router = APIRouter(prefix="/assessments", tags=["assessments"])

@router.get("/diagnostic")
def get_diagnostic_assessment(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    assessment = Assessment(
        student_id=current_user.id,
        status="in_progress"
    )
    db.add(assessment)
    db.commit()
    db.refresh(assessment)

    subjects = db.query(Subject).all()
    selected_questions = []
    letters = ["a", "b", "c", "d", "e"]
    labels = ["A", "B", "C", "D", "E"]
    
    for subj in subjects:
        q_list = db.query(Question).filter(Question.subject_id == subj.id).limit(3).all()
        selected_questions.extend(q_list)
        
    if len(selected_questions) < 5:
        selected_questions = db.query(Question).limit(10).all()

    subj_map = {s.id: s.name for s in subjects}

    questions_payload = []
    for q in selected_questions:
        tags = []
        if q.tags:
            try:
                tags = json.loads(q.tags)
            except Exception:
                tags = [q.tags]
                
        opts = []
        for o in q.options:
            letter = letters[o.display_order] if o.display_order < len(letters) else str(o.display_order)
            label = labels[o.display_order] if o.display_order < len(labels) else str(o.display_order + 1)
            opts.append({
                "id": str(o.id),
                "option_text": o.option_text,
                "label": label,
                "letter": letter,
                "display_order": o.display_order
            })
            
        questions_payload.append({
            "id": str(q.id),
            "subject_name": subj_map.get(q.subject_id, "General"),
            "question_text": q.question_text,
            "question_type": q.question_type,
            "difficulty": q.difficulty,
            "hint": q.hint,
            "tags": tags,
            "options": opts
        })

    return {
        "success": True,
        "data": {
            "assessment_id": str(assessment.id),
            "title": "Comprehensive Skill Diagnostic Assessment",
            "total_questions": len(questions_payload),
            "questions": questions_payload
        }
    }

@router.post("/start", status_code=201)
def start(request: StartAssessmentRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = start_assessment(db, current_user.id, request)
    return {"success": True, "data": result}

@router.post("/submit")
def submit(request: SubmitAssessmentRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = submit_assessment(db, current_user.id, request)
    return {"success": True, "data": result}

@router.get("/results/{assessment_id}")
def get_result(assessment_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = db.query(AssessmentResult).join(Assessment).filter(
        Assessment.id == uuid.UUID(assessment_id),
        Assessment.student_id == current_user.id
    ).first()
    if not result:
        raise HTTPException(status_code=404, detail="Result not found")
    return {"success": True, "data": {
        "assessment_id": assessment_id,
        "total_questions": result.total_questions,
        "correct_answers": result.correct_answers,
        "score_percentage": result.score_percentage,
        "xp_earned": result.xp_earned,
        "completed_at": result.completed_at.isoformat()
    }}

@router.get("/history")
def get_history(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    assessments = db.query(Assessment).filter(
        Assessment.student_id == current_user.id,
        Assessment.status == "completed"
    ).order_by(desc(Assessment.completed_at)).limit(20).all()
    result = []
    for a in assessments:
        if a.result:
            result.append({
                "assessment_id": str(a.id),
                "lesson_id": str(a.lesson_id) if a.lesson_id else None,
                "score_percentage": a.result.score_percentage,
                "xp_earned": a.result.xp_earned,
                "completed_at": a.completed_at.isoformat() if a.completed_at else None
            })
    return {"success": True, "data": result}
