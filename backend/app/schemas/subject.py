from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class SubjectResponse(BaseModel):
    id: str
    name: str
    slug: str
    description: Optional[str]
    icon: Optional[str]
    color: Optional[str]
    display_order: int
    course_count: int = 0
    
    model_config = {"from_attributes": True}

class SubjectListResponse(BaseModel):
    success: bool
    data: List[SubjectResponse]
