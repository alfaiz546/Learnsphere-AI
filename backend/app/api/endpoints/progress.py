from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.base import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.services.progress_service import get_weak_topics, get_progress_summary, get_topic_analysis
from app.models.progress import LearningProgress
from app.models.lesson import Lesson
from sqlalchemy import desc

router = APIRouter(prefix="/progress", tags=["progress"])

@router.get("")
def get_progress(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    summary = get_progress_summary(db, current_user.id)
    return {"success": True, "data": summary}

@router.get("/weak-topics")
def weak_topics(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    topics = get_weak_topics(db, current_user.id)
    return {"success": True, "data": topics}

@router.get("/topic-analysis")
def topic_analysis(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    analysis = get_topic_analysis(db, current_user.id)
    return {"success": True, "data": analysis}

@router.get("/history")
def history(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    progresses = db.query(LearningProgress).filter(
        LearningProgress.student_id == current_user.id
    ).order_by(desc(LearningProgress.last_accessed_at)).limit(50).all()
    
    result = []
    for p in progresses:
        lesson = db.query(Lesson).filter(Lesson.id == p.lesson_id).first()
        if lesson:
            result.append({
                "lesson_id": str(lesson.id),
                "lesson_title": lesson.title,
                "status": p.status,
                "completion_percentage": p.completion_percentage,
                "last_accessed_at": p.last_accessed_at.isoformat() if p.last_accessed_at else None,
                "completed_at": p.completed_at.isoformat() if p.completed_at else None
            })
    return {"success": True, "data": result}
