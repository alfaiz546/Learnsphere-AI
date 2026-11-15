from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.base import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.services.student_service import get_dashboard_data
from app.schemas.user import UpdateProfileRequest
import json

router = APIRouter(prefix="/student", tags=["student"])

@router.get("/profile")
def get_profile(current_user: User = Depends(get_current_user)):
    profile = current_user.profile
    return {
        "success": True,
        "data": {
            "id": str(current_user.id),
            "email": current_user.email,
            "username": current_user.username,
            "full_name": current_user.full_name,
            "role": current_user.role,
            "profile": {
                "xp_total": profile.xp_total if profile else 0,
                "current_streak": profile.current_streak if profile else 0,
                "longest_streak": profile.longest_streak if profile else 0,
                "daily_goal_minutes": profile.daily_goal_minutes if profile else 30,
                "subjects_of_interest": json.loads(profile.subjects_of_interest) if profile and profile.subjects_of_interest else [],
                "current_class": getattr(profile, "current_class", None) if profile else None,
                "board": getattr(profile, "board", None) if profile else None,
                "current_marks": getattr(profile, "current_marks", None) if profile else None,
                "target_exam": getattr(profile, "target_exam", None) if profile else None,
                "career_goal": getattr(profile, "career_goal", None) if profile else None,
                "target_year": getattr(profile, "target_year", None) if profile else None,
                "category": getattr(profile, "category", "General") if profile else "General"
            }
        }
    }

@router.put("/profile")
def update_profile(request: UpdateProfileRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if request.full_name is not None:
        current_user.full_name = request.full_name
    if current_user.profile:
        if request.daily_goal_minutes is not None:
            current_user.profile.daily_goal_minutes = request.daily_goal_minutes
        if request.subjects_of_interest is not None:
            current_user.profile.subjects_of_interest = json.dumps(request.subjects_of_interest)
        if request.current_class is not None:
            current_user.profile.current_class = request.current_class
        if request.board is not None:
            current_user.profile.board = request.board
        if request.current_marks is not None:
            current_user.profile.current_marks = request.current_marks
        if request.target_exam is not None:
            current_user.profile.target_exam = request.target_exam
        if request.career_goal is not None:
            current_user.profile.career_goal = request.career_goal
        if request.target_year is not None:
            current_user.profile.target_year = request.target_year
        if request.category is not None:
            current_user.profile.category = request.category
    db.commit()
    return {"success": True, "message": "Profile updated"}

@router.get("/dashboard")
def get_dashboard(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    data = get_dashboard_data(db, current_user)
    return {"success": True, "data": data}
