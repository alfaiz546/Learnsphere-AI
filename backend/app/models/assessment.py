import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, Integer, Float, DateTime, Text, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database.base import Base

class Assessment(Base):
    __tablename__ = "assessments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    lesson_id = Column(UUID(as_uuid=True), ForeignKey("lessons.id"), nullable=True)
    course_id = Column(UUID(as_uuid=True), ForeignKey("courses.id"), nullable=True)
    status = Column(Enum("in_progress", "completed", "abandoned", name="assessment_status"), default="in_progress", nullable=False)
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    
    student = relationship("User")
    lesson = relationship("Lesson", back_populates="assessments")
    course = relationship("Course", back_populates="assessments")
    answers = relationship("StudentAnswer", back_populates="assessment", cascade="all, delete-orphan")
    result = relationship("AssessmentResult", back_populates="assessment", uselist=False, cascade="all, delete-orphan")

class StudentAnswer(Base):
    __tablename__ = "student_answers"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    assessment_id = Column(UUID(as_uuid=True), ForeignKey("assessments.id"), nullable=False)
    question_id = Column(UUID(as_uuid=True), ForeignKey("questions.id"), nullable=False)
    student_answer = Column(Text, nullable=False)
    is_correct = Column(Boolean, default=False, nullable=False)
    score = Column(Float, default=0.0, nullable=False)
    time_taken_seconds = Column(Integer, default=0, nullable=False)
    attempt_number = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    assessment = relationship("Assessment", back_populates="answers")
    question = relationship("Question", back_populates="student_answers")

class AssessmentResult(Base):
    __tablename__ = "assessment_results"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    assessment_id = Column(UUID(as_uuid=True), ForeignKey("assessments.id"), unique=True, nullable=False)
    total_questions = Column(Integer, default=0, nullable=False)
    correct_answers = Column(Integer, default=0, nullable=False)
    score_percentage = Column(Float, default=0.0, nullable=False)
    xp_earned = Column(Integer, default=0, nullable=False)
    completed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    assessment = relationship("Assessment", back_populates="result")
