from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models.user import User
from app.models.progress import LearningProgress, LearningPath
from app.models.assessment import Assessment, AssessmentResult
from app.models.course import Course
from app.models.lesson import Lesson
from app.services.progress_service import get_topic_analysis, get_weekly_xp

def get_dashboard_data(db: Session, student: User) -> dict:
    profile = student.profile
    
    paths = db.query(LearningPath).filter(LearningPath.student_id == student.id).all()
    enrolled = []
    for path in paths:
        course = db.query(Course).filter(Course.id == path.course_id).first()
        if course:
            total_lessons = sum(len(m.lessons) for m in course.modules)
            completed = db.query(LearningProgress).filter(
                LearningProgress.student_id == student.id,
                LearningProgress.status == "completed"
            ).join(Lesson, LearningProgress.lesson_id == Lesson.id).filter(
                Lesson.module.has(course_id=course.id)
            ).count()
            enrolled.append({
                "id": str(course.id),
                "title": course.title,
                "total_lessons": total_lessons,
                "completed_lessons": completed,
                "progress_pct": round(completed / total_lessons * 100) if total_lessons else 0,
                "color": course.thumbnail_color or "#6366f1"
            })
    
    recent_assessments = db.query(Assessment, AssessmentResult).join(
        AssessmentResult, Assessment.id == AssessmentResult.assessment_id
    ).filter(Assessment.student_id == student.id).order_by(desc(Assessment.completed_at)).limit(5).all()
    
    recent_results = []
    for assessment, result in recent_assessments:
        lesson_title = ""
        if assessment.lesson_id:
            lesson = db.query(Lesson).filter(Lesson.id == assessment.lesson_id).first()
            lesson_title = lesson.title if lesson else ""
        recent_results.append({
            "assessment_id": str(assessment.id),
            "lesson_title": lesson_title,
            "score": result.score_percentage,
            "xp_earned": result.xp_earned,
            "completed_at": assessment.completed_at.isoformat() if assessment.completed_at else None
        })
    
    topic_analysis = get_topic_analysis(db, student.id)
    weekly_xp = get_weekly_xp(db, student.id)
    
    return {
        "user": {
            "id": str(student.id),
            "username": student.username,
            "full_name": student.full_name or student.username,
            "email": student.email,
            "profile": {
                "current_class": profile.current_class if profile else None,
                "board": profile.board if profile else None,
                "current_marks": profile.current_marks if profile else None,
                "target_exam": profile.target_exam if profile else None,
                "career_goal": profile.career_goal if profile else None,
                "target_year": profile.target_year if profile else None,
                "category": profile.category if profile else None,
            }
        },
        "stats": {
            "xp_total": profile.xp_total if profile else 0,
            "current_streak": profile.current_streak if profile else 0,
            "longest_streak": profile.longest_streak if profile else 0,
            "daily_goal_minutes": profile.daily_goal_minutes if profile else 30,
            "lessons_completed": db.query(LearningProgress).filter(
                LearningProgress.student_id == student.id, LearningProgress.status == "completed"
            ).count(),
            "courses_enrolled": len(paths)
        },
        "enrolled_courses": enrolled,
        "recent_results": recent_results,
        "weak_topics": topic_analysis.get("weak_topics", []),
        "strong_topics": topic_analysis.get("strong_topics", []),
        "weekly_xp": weekly_xp
    }
