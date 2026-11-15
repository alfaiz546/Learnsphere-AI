from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class LessonBrief(BaseModel):
    id: str
    title: str
    lesson_type: str
    estimated_minutes: int
    display_order: int
    
    model_config = {"from_attributes": True}

class ModuleResponse(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    display_order: int
    lessons: List[LessonBrief] = []
    
    model_config = {"from_attributes": True}

class CourseResponse(BaseModel):
    id: str
    subject_id: str
    title: str
    slug: str
    description: Optional[str] = None
    difficulty: str
    estimated_hours: float
    is_published: bool
    thumbnail_color: Optional[str] = None
    lesson_count: int = 0
    subject_name: str = ""
    
    model_config = {"from_attributes": True}

class CourseDetailResponse(BaseModel):
    id: str
    subject_id: str
    title: str
    slug: str
    description: Optional[str] = None
    difficulty: str
    estimated_hours: float
    modules: List[ModuleResponse] = []
    is_enrolled: bool = False
    subject_name: str = ""
    
    model_config = {"from_attributes": True}

class CreateCourseRequest(BaseModel):
    subject_id: str
    title: str
    description: Optional[str] = None
    difficulty: str = "beginner"
    estimated_hours: float = 0.0
