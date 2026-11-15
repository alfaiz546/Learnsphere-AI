from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.base import get_db
from app.core.dependencies import get_current_admin
from app.models.user import User
from app.models.subject import Subject
from app.models.course import Course
from app.models.lesson import Lesson
from app.models.question import Question, QuestionOption
from app.cache.cache_manager import cache
from pydantic import BaseModel
from typing import Optional, List
import uuid

router = APIRouter(prefix="/admin", tags=["admin"])

class CreateSubjectRequest(BaseModel):
    name: str
    description: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    slug: str

class CreateCourseRequest(BaseModel):
    subject_id: str
    title: str
    slug: str
    description: Optional[str] = None
    difficulty: str = "beginner"
    estimated_hours: float = 0.0

class CreateLessonRequest(BaseModel):
    module_id: str
    title: str
    description: Optional[str] = None
    content: Optional[str] = None
    lesson_type: str = "concept"
    estimated_minutes: int = 15

class CreateQuestionRequest(BaseModel):
    lesson_id: Optional[str] = None
    subject_id: Optional[str] = None
    question_text: str
    question_type: str
    difficulty: str = "beginner"
    correct_answer: str
    explanation: Optional[str] = None
    hint: Optional[str] = None
    options: Optional[List[dict]] = None

@router.post("/subjects", status_code=201)
def create_subject(req: CreateSubjectRequest, db: Session = Depends(get_db), admin: User = Depends(get_current_admin)):
    s = Subject(name=req.name, slug=req.slug, description=req.description, icon=req.icon, color=req.color)
    db.add(s)
    db.commit()
    cache.invalidate_prefix("subjects")
    return {"success": True, "data": {"id": str(s.id)}}

@router.post("/courses", status_code=201)
def create_course(req: CreateCourseRequest, db: Session = Depends(get_db), admin: User = Depends(get_current_admin)):
    c = Course(subject_id=uuid.UUID(req.subject_id), title=req.title, slug=req.slug, description=req.description,
               difficulty=req.difficulty, estimated_hours=req.estimated_hours)
    db.add(c)
    db.commit()
    return {"success": True, "data": {"id": str(c.id)}}

@router.post("/lessons", status_code=201)
def create_lesson(req: CreateLessonRequest, db: Session = Depends(get_db), admin: User = Depends(get_current_admin)):
    l = Lesson(module_id=uuid.UUID(req.module_id), title=req.title, description=req.description,
               content=req.content, lesson_type=req.lesson_type, estimated_minutes=req.estimated_minutes)
    db.add(l)
    db.commit()
    return {"success": True, "data": {"id": str(l.id)}}

@router.post("/questions", status_code=201)
def create_question(req: CreateQuestionRequest, db: Session = Depends(get_db), admin: User = Depends(get_current_admin)):
    q = Question(
        lesson_id=uuid.UUID(req.lesson_id) if req.lesson_id else None,
        subject_id=uuid.UUID(req.subject_id) if req.subject_id else None,
        question_text=req.question_text,
        question_type=req.question_type,
        difficulty=req.difficulty,
        correct_answer=req.correct_answer,
        explanation=req.explanation,
        hint=req.hint
    )
    db.add(q)
    db.flush()
    if req.options:
        for i, opt in enumerate(req.options):
            o = QuestionOption(question_id=q.id, option_text=opt["text"], is_correct=opt.get("is_correct", False), display_order=i)
            db.add(o)
    db.commit()
    return {"success": True, "data": {"id": str(q.id)}}

@router.get("/stats")
def get_stats(db: Session = Depends(get_db), admin: User = Depends(get_current_admin)):
    from app.models.assessment import Assessment
    from app.models.progress import LearningProgress
    return {
        "success": True,
        "data": {
            "total_users": db.query(User).count(),
            "total_courses": db.query(Course).count(),
            "total_lessons": db.query(Lesson).count(),
            "total_assessments": db.query(Assessment).count(),
            "total_completions": db.query(LearningProgress).filter(LearningProgress.status == "completed").count()
        }
    }
