from sqlalchemy.orm import Session
from app.services.progress_service import get_progress_summary, get_weekly_xp
import uuid

def analyze_progress(db: Session, student_id: uuid.UUID) -> dict:
    summary = get_progress_summary(db, student_id)
    weekly = get_weekly_xp(db, student_id)
    return {
        "progress_summary": summary,
        "weekly_xp": weekly,
        "summary": f"Student has completed {summary['completed_lessons']} lessons with {summary['total_xp']} total XP"
    }
