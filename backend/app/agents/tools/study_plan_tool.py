from sqlalchemy.orm import Session
from app.models.progress import StudyPlan
import uuid, json
from datetime import datetime, timedelta

def generate_study_plan(db: Session, student_id: uuid.UUID, goal: str, available_hours_per_day: float, duration_days: int, weak_topics: list = None) -> dict:
    plan_data = {
        "goal": goal,
        "hours_per_day": available_hours_per_day,
        "duration_days": duration_days,
        "weak_topics": weak_topics or [],
        "schedule": []
    }
    
    for day in range(1, duration_days + 1):
        day_plan = {
            "day": day,
            "date": (datetime.utcnow() + timedelta(days=day-1)).strftime("%Y-%m-%d"),
            "study_minutes": int(available_hours_per_day * 60),
            "activities": [
                f"Day {day}: Study core concepts and practice {weak_topics[day % len(weak_topics)] if weak_topics else 'problem-solving'}"
            ]
        }
        plan_data["schedule"].append(day_plan)
    
    plan_type = "7_day" if duration_days <= 7 else "30_day"
    study_plan = StudyPlan(
        student_id=student_id,
        plan_type=plan_type,
        title=f"{duration_days}-Day Plan: {goal[:50]}",
        description=f"Personalized {duration_days}-day plan for: {goal}",
        plan_data=json.dumps(plan_data),
        starts_at=datetime.utcnow(),
        ends_at=datetime.utcnow() + timedelta(days=duration_days)
    )
    db.add(study_plan)
    db.commit()
    db.refresh(study_plan)
    
    return {
        "plan_id": str(study_plan.id),
        "title": study_plan.title,
        "duration_days": duration_days,
        "plan_data": plan_data,
        "message": "Study plan created and saved successfully"
    }
