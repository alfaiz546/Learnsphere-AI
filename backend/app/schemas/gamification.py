from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class AchievementResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    icon: Optional[str] = None
    xp_reward: int
    earned: bool = False
    earned_at: Optional[datetime] = None
    
    model_config = {"from_attributes": True}

class GamificationResponse(BaseModel):
    xp_total: int
    current_streak: int
    longest_streak: int
    achievements_earned: int
    achievements: List[AchievementResponse] = []
