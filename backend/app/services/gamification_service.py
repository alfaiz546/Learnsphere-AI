from datetime import date, datetime
from zoneinfo import ZoneInfo
from sqlalchemy.orm import Session
from app.models.user import StudentProfile
from app.models.gamification import Achievement, StudentAchievement, XPTransaction
import logging
import json

logger = logging.getLogger(__name__)

def award_xp(db: Session, student_id, amount: int, reason: str, reference_id=None):
    profile = db.query(StudentProfile).filter(StudentProfile.user_id == student_id).first()
    if not profile:
        profile = StudentProfile(user_id=student_id)
        db.add(profile)
        db.flush()
    profile.xp_total += amount
    tx = XPTransaction(student_id=student_id, amount=amount, reason=reason, reference_id=reference_id)
    db.add(tx)
    db.commit()
    logger.info(f"Awarded {amount} XP to student {student_id}: {reason}")

def update_streak(db: Session, student_id):
    profile = db.query(StudentProfile).filter(StudentProfile.user_id == student_id).first()
    if not profile:
        profile = StudentProfile(user_id=student_id)
        db.add(profile)
        db.flush()
    today = datetime.now(ZoneInfo("Asia/Kolkata")).date()
    if profile.last_active_date == today:
        return
    if profile.last_active_date and (today - profile.last_active_date).days == 1:
        profile.current_streak += 1
    else:
        profile.current_streak = 1
    profile.last_active_date = today
    if profile.current_streak > profile.longest_streak:
        profile.longest_streak = profile.current_streak
    db.commit()

def check_and_award_achievements(db: Session, student_id):
    profile = db.query(StudentProfile).filter(StudentProfile.user_id == student_id).first()
    if not profile:
        return
    earned_ids = {sa.achievement_id for sa in db.query(StudentAchievement).filter(StudentAchievement.student_id == student_id).all()}
    all_achievements = db.query(Achievement).all()
    
    for ach in all_achievements:
        if ach.id in earned_ids:
            continue
        criteria = json.loads(ach.criteria or "{}")
        earned = False
        if criteria.get("type") == "streak" and profile.current_streak >= criteria.get("value", 0):
            earned = True
        elif criteria.get("type") == "xp" and profile.xp_total >= criteria.get("value", 0):
            earned = True
        elif criteria.get("type") == "first_lesson":
            from app.models.progress import LearningProgress
            if db.query(LearningProgress).filter(LearningProgress.student_id == student_id, LearningProgress.status == "completed").count() >= 1:
                earned = True
        
        if earned:
            sa = StudentAchievement(student_id=student_id, achievement_id=ach.id)
            db.add(sa)
            award_xp(db, student_id, ach.xp_reward, f"Achievement: {ach.name}", ach.id)
            logger.info(f"Student {student_id} earned achievement: {ach.name}")
    db.commit()
