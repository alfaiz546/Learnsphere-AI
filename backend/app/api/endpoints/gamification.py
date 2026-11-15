from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.base import get_db
from app.core.dependencies import get_current_user
from app.models.user import User, StudentProfile
from app.models.gamification import Achievement, StudentAchievement

router = APIRouter(prefix="/gamification", tags=["gamification"])

@router.get("")
def get_gamification(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    profile = db.query(StudentProfile).filter(StudentProfile.user_id == current_user.id).first()
    earned_count = db.query(StudentAchievement).filter(StudentAchievement.student_id == current_user.id).count()
    return {
        "success": True,
        "data": {
            "xp_total": profile.xp_total if profile else 0,
            "current_streak": profile.current_streak if profile else 0,
            "longest_streak": profile.longest_streak if profile else 0,
            "achievements_earned": earned_count
        }
    }

@router.get("/achievements")
def get_achievements(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    all_achievements = db.query(Achievement).all()
    earned = {sa.achievement_id: sa.earned_at for sa in db.query(StudentAchievement).filter(StudentAchievement.student_id == current_user.id).all()}
    
    result = []
    for ach in all_achievements:
        result.append({
            "id": str(ach.id),
            "name": ach.name,
            "description": ach.description,
            "icon": ach.icon,
            "xp_reward": ach.xp_reward,
            "earned": ach.id in earned,
            "earned_at": earned[ach.id].isoformat() if ach.id in earned else None
        })
    return {"success": True, "data": result}
