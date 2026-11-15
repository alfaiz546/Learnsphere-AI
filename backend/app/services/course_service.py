from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.course import Course, Module
from app.models.subject import Subject
from app.models.lesson import Lesson
from app.models.progress import LearningPath, LearningProgress
from app.cache.cache_manager import cache
import uuid

def get_all_subjects(db: Session, exam_slug: str = None) -> list:
    from app.models.exam_category import ExamCategory

    cache_key = exam_slug or "all"
    cached = cache.get("subjects", cache_key)
    if cached is not None:
        return cached

    query = db.query(Subject).filter(Subject.is_active == True)

    if exam_slug:
        query = query.join(
            ExamCategory,
            Subject.exam_category_id == ExamCategory.id
        ).filter(
            ExamCategory.slug == exam_slug,
            ExamCategory.is_active == True
        )
    else:
        query = query.join(
            ExamCategory,
            Subject.exam_category_id == ExamCategory.id
        ).filter(
            ExamCategory.slug == "general-learning",
            ExamCategory.is_active == True
        )

    subjects = query.order_by(Subject.display_order).all()

    result = []
    for s in subjects:
        course_count = db.query(Course).filter(
            Course.subject_id == s.id,
            Course.is_published == True
        ).count()

        result.append({
            "id": str(s.id),
            "name": s.name,
            "slug": s.slug,
            "description": s.description,
            "icon": s.icon,
            "color": s.color,
            "display_order": s.display_order,
            "course_count": course_count
        })

    cache.set("subjects", result, cache_key, ttl=3600)
    return result

def get_all_courses(db: Session, subject_id: str = None) -> list:
    q = db.query(Course).filter(Course.is_published == True)
    if subject_id:
        q = q.filter(Course.subject_id == uuid.UUID(subject_id))
    courses = q.all()
    result = []
    for c in courses:
        lesson_count = sum(len(m.lessons) for m in c.modules)
        result.append({
            "id": str(c.id),
            "subject_id": str(c.subject_id),
            "title": c.title,
            "slug": c.slug,
            "description": c.description,
            "difficulty": c.difficulty,
            "estimated_hours": c.estimated_hours,
            "lesson_count": lesson_count,
            "subject_name": c.subject.name if c.subject else "",
            "thumbnail_color": c.thumbnail_color or "#6366f1",
            "is_published": c.is_published
        })
    return result

def get_course_detail(db: Session, course_id: str, student_id=None) -> dict:
    course = db.query(Course).filter(Course.id == uuid.UUID(course_id)).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    is_enrolled = False
    if student_id:
        is_enrolled = db.query(LearningPath).filter(
            LearningPath.student_id == student_id, LearningPath.course_id == course.id
        ).first() is not None
    
    modules_data = []
    for m in course.modules:
        lessons_data = []
        for l in m.lessons:
            lesson_status = "not_started"
            if student_id:
                prog = db.query(LearningProgress).filter(
                    LearningProgress.student_id == student_id, LearningProgress.lesson_id == l.id
                ).first()
                if prog:
                    lesson_status = prog.status
            lessons_data.append({
                "id": str(l.id),
                "title": l.title,
                "lesson_type": l.lesson_type,
                "estimated_minutes": l.estimated_minutes,
                "display_order": l.display_order,
                "status": lesson_status
            })
        modules_data.append({
            "id": str(m.id),
            "title": m.title,
            "description": m.description,
            "display_order": m.display_order,
            "lessons": lessons_data
        })
    
    return {
        "id": str(course.id),
        "subject_id": str(course.subject_id),
        "title": course.title,
        "slug": course.slug,
        "description": course.description,
        "difficulty": course.difficulty,
        "estimated_hours": course.estimated_hours,
        "modules": modules_data,
        "is_enrolled": is_enrolled,
        "subject_name": course.subject.name if course.subject else ""
    }

def enroll_course(db: Session, student_id, course_id: str) -> dict:
    course = db.query(Course).filter(Course.id == uuid.UUID(course_id)).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    existing = db.query(LearningPath).filter(
        LearningPath.student_id == student_id, LearningPath.course_id == course.id
    ).first()
    if existing:
        return {"message": "Already enrolled"}
    path = LearningPath(student_id=student_id, course_id=course.id)
    db.add(path)
    db.commit()
    return {"message": "Enrolled successfully"}
