from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime, date
import uuid

class StudentProfileData(BaseModel):
    xp_total: int
    current_streak: int
    longest_streak: int
    last_active_date: Optional[date]
    daily_goal_minutes: int
    subjects_of_interest: List[str]
    current_class: Optional[str] = None
    board: Optional[str] = None
    current_marks: Optional[float] = None
    target_exam: Optional[str] = None
    career_goal: Optional[str] = None
    target_year: Optional[int] = None
    category: Optional[str] = "General"
    
    model_config = {"from_attributes": True}

class UserResponse(BaseModel):
    id: str
    email: str
    username: str
    full_name: Optional[str]
    role: str
    is_active: bool
    created_at: datetime
    profile: Optional[StudentProfileData]
    
    model_config = {"from_attributes": True}

class UpdateProfileRequest(BaseModel):
    full_name: Optional[str] = None
    daily_goal_minutes: Optional[int] = None
    subjects_of_interest: Optional[List[str]] = None
    current_class: Optional[str] = None
    board: Optional[str] = None
    current_marks: Optional[float] = None
    target_exam: Optional[str] = None
    career_goal: Optional[str] = None
    target_year: Optional[int] = None
    category: Optional[str] = None

class DashboardResponse(BaseModel):
    success: bool
    data: dict
