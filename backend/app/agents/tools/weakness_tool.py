from sqlalchemy.orm import Session
from app.services.progress_service import get_weak_topics
import uuid

def analyze_weaknesses(db: Session, student_id: uuid.UUID, time_period_days: int = 30) -> dict:
    weak_topics = get_weak_topics(db, student_id, time_period_days)
    return {
        "weak_topics": weak_topics,
        "analysis_period_days": time_period_days,
        "total_weak_topics": len(weak_topics),
        "summary": f"Found {len(weak_topics)} weak topics in the past {time_period_days} days"
    }
