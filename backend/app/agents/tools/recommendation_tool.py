from sqlalchemy.orm import Session
from app.models.course import Course
from app.models.progress import LearningPath
import uuid

def get_recommendations(db: Session, student_id: uuid.UUID, limit: int = 5) -> dict:
    enrolled_ids = {str(lp.course_id) for lp in db.query(LearningPath).filter(LearningPath.student_id == student_id).all()}
    all_courses = db.query(Course).filter(Course.is_published == True).all()
    recommendations = []
    for course in all_courses:
        if str(course.id) not in enrolled_ids:
            recommendations.append({
                "course_id": str(course.id),
                "title": course.title,
                "difficulty": course.difficulty,
                "estimated_hours": course.estimated_hours,
                "subject": course.subject.name if course.subject else ""
            })
        if len(recommendations) >= limit:
            break
    return {"recommendations": recommendations, "count": len(recommendations)}
