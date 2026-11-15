from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.progress import LearningProgress, LearningPath
from app.models.assessment import Assessment, StudentAnswer
from app.models.question import Question
from app.models.subject import Subject
from app.models.user import StudentProfile
from app.models.gamification import XPTransaction
from datetime import datetime, timedelta
import logging
import json

logger = logging.getLogger(__name__)

def get_topic_analysis(db: Session, student_id, days: int = 30) -> dict:
    since = datetime.utcnow() - timedelta(days=days)
    
    answers = (
        db.query(StudentAnswer, Question)
        .join(Question, StudentAnswer.question_id == Question.id)
        .join(Assessment, StudentAnswer.assessment_id == Assessment.id)
        .filter(Assessment.student_id == student_id, StudentAnswer.created_at >= since)
        .all()
    )
    
    # Preload subjects
    subjects = {str(s.id): s.name for s in db.query(Subject).all()}
    
    topic_stats = {}
    for sa, q in answers:
        tags = q.tags or "[]"
        try:
            tag_list = json.loads(tags)
        except Exception:
            tag_list = ["General"]
        
        subject_name = subjects.get(str(q.subject_id), "General") if q.subject_id else "General"
        
        for tag in tag_list:
            if tag not in topic_stats:
                topic_stats[tag] = {"correct": 0, "total": 0, "subject": subject_name}
            topic_stats[tag]["total"] += 1
            if sa.is_correct:
                topic_stats[tag]["correct"] += 1
    
    strong = []
    weak = []
    moderate = []
    
    for topic, stats in topic_stats.items():
        if stats["total"] > 0:
            accuracy = stats["correct"] / stats["total"]
            pct = round(accuracy * 100, 1)
            item = {
                "topic": topic,
                "subject": stats["subject"],
                "accuracy_rate": pct,
                "attempts": stats["total"],
                "correct": stats["correct"]
            }
            if accuracy >= 0.75:
                item["recommendation"] = f"Strong grasp in {topic}! Ready for advanced problem sets."
                item["status"] = "mastered"
                strong.append(item)
            elif accuracy < 0.60:
                item["recommendation"] = f"Review foundational principles and practice more {topic} questions."
                item["status"] = "needs_practice"
                weak.append(item)
            else:
                item["recommendation"] = f"Solid foundation in {topic}; practice higher difficulty questions to reach mastery."
                item["status"] = "in_progress"
                moderate.append(item)
    
    strong.sort(key=lambda x: x["accuracy_rate"], reverse=True)
    weak.sort(key=lambda x: x["accuracy_rate"])
    moderate.sort(key=lambda x: x["accuracy_rate"], reverse=True)
    
    return {
        "strong_topics": strong,
        "weak_topics": weak,
        "moderate_topics": moderate,
        "total_evaluated_topics": len(topic_stats)
    }

def get_weak_topics(db: Session, student_id, days: int = 30) -> list:
    analysis = get_topic_analysis(db, student_id, days)
    # If weak is empty but moderate exists, return moderate as areas to improve
    return analysis["weak_topics"] if analysis["weak_topics"] else analysis["moderate_topics"][:5]

def get_progress_summary(db: Session, student_id) -> dict:
    profile = db.query(StudentProfile).filter(StudentProfile.user_id == student_id).first()
    total = db.query(LearningProgress).filter(LearningProgress.student_id == student_id).count()
    completed = db.query(LearningProgress).filter(LearningProgress.student_id == student_id, LearningProgress.status == "completed").count()
    enrolled = db.query(LearningPath).filter(LearningPath.student_id == student_id).count()
    
    return {
        "total_lessons": total,
        "completed_lessons": completed,
        "completion_percentage": round(completed / total * 100, 1) if total > 0 else 0.0,
        "total_xp": profile.xp_total if profile else 0,
        "current_streak": profile.current_streak if profile else 0,
        "enrolled_courses": enrolled
    }

def get_weekly_xp(db: Session, student_id) -> list:
    result = []
    for i in range(6, -1, -1):
        day = datetime.utcnow().date() - timedelta(days=i)
        day_start = datetime(day.year, day.month, day.day)
        day_end = day_start + timedelta(days=1)
        xp = db.query(func.sum(XPTransaction.amount)).filter(
            XPTransaction.student_id == student_id,
            XPTransaction.created_at >= day_start,
            XPTransaction.created_at < day_end
        ).scalar() or 0
        result.append({"date": day.strftime("%a"), "xp": int(xp)})
    return result
