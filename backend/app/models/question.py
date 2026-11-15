import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, Integer, DateTime, Text, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database.base import Base

class Question(Base):
    __tablename__ = "questions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lesson_id = Column(UUID(as_uuid=True), ForeignKey("lessons.id"), nullable=True)
    subject_id = Column(UUID(as_uuid=True), ForeignKey("subjects.id"), nullable=True)
    question_text = Column(Text, nullable=False)
    question_type = Column(Enum("multiple_choice", "true_false", "numerical", "fill_blank", "coding", name="question_type"), nullable=False)
    difficulty = Column(Enum("beginner", "intermediate", "advanced", name="q_difficulty"), default="beginner", nullable=False)
    correct_answer = Column(Text, nullable=False)
    explanation = Column(Text, nullable=True)
    hint = Column(Text, nullable=True)
    tags = Column(Text, default="[]", nullable=True)
    is_ai_generated = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    lesson = relationship("Lesson", back_populates="questions")
    options = relationship("QuestionOption", back_populates="question", order_by="QuestionOption.display_order", cascade="all, delete-orphan")
    student_answers = relationship("StudentAnswer", back_populates="question")

class QuestionOption(Base):
    __tablename__ = "question_options"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    question_id = Column(UUID(as_uuid=True), ForeignKey("questions.id"), nullable=False)
    option_text = Column(Text, nullable=False)
    is_correct = Column(Boolean, default=False, nullable=False)
    display_order = Column(Integer, default=0, nullable=False)
    
    question = relationship("Question", back_populates="options")
