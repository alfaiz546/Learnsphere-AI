import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, Integer, Float, DateTime, Text, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database.base import Base

class LearningProgress(Base):
    __tablename__ = "learning_progress"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    lesson_id = Column(UUID(as_uuid=True), ForeignKey("lessons.id"), nullable=False)
    status = Column(Enum("not_started", "in_progress", "completed", name="progress_status"), default="not_started", nullable=False)
    completion_percentage = Column(Float, default=0.0, nullable=False)
    time_spent_minutes = Column(Integer, default=0, nullable=False)
    last_accessed_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    student = relationship("User")
    lesson = relationship("Lesson", back_populates="progress")

class LearningPath(Base):
    __tablename__ = "learning_paths"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    course_id = Column(UUID(as_uuid=True), ForeignKey("courses.id"), nullable=False)
    is_enrolled = Column(Boolean, default=True, nullable=False)
    enrolled_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    
    student = relationship("User")
    course = relationship("Course", back_populates="learning_paths")

class StudyPlan(Base):
    __tablename__ = "study_plans"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    plan_type = Column(Enum("7_day", "30_day", "custom", name="plan_type"), default="7_day", nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    plan_data = Column(Text, nullable=False)  # JSON string
    is_approved = Column(Boolean, default=False, nullable=False)
    starts_at = Column(DateTime, nullable=True)
    ends_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    student = relationship("User")
