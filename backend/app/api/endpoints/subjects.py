from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from app.database.base import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.services.course_service import get_all_subjects, get_all_courses, get_course_detail, enroll_course

router = APIRouter(tags=["subjects"])

@router.get("/subjects")
def list_subjects(
    exam_slug: Optional[str] = Query(default=None),
    db: Session = Depends(get_db)
):
    if exam_slug and exam_slug not in ("jee", "neet"):
        raise HTTPException(status_code=404, detail="Exam category not found")

    subjects = get_all_subjects(db, exam_slug=exam_slug)
    return {"success": True, "data": subjects}

@router.get("/subjects/{subject_id}")
def get_subject(subject_id: str, db: Session = Depends(get_db)):
    subjects = get_all_subjects(db)
    subject = next((s for s in subjects if s["id"] == subject_id), None)
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    return {"success": True, "data": subject}

@router.get("/courses")
def list_courses(subject_id: Optional[str] = Query(default=None), db: Session = Depends(get_db)):
    courses = get_all_courses(db, subject_id)
    return {"success": True, "data": courses}

@router.get("/courses/{course_id}")
def get_course(course_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    data = get_course_detail(db, course_id, current_user.id)
    return {"success": True, "data": data}

@router.post("/courses/{course_id}/enroll")
def enroll(course_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = enroll_course(db, current_user.id, course_id)
    return {"success": True, "message": result["message"]}
