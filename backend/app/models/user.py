import uuid
from datetime import datetime, date
from sqlalchemy import Column, String, Boolean, Enum, DateTime, Date, Integer, Text, ForeignKey, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database.base import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    role = Column(Enum("student", "admin", name="user_role"), default="student", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    profile = relationship("StudentProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    conversations = relationship("AIConversation", back_populates="student", cascade="all, delete-orphan")

class StudentProfile(Base):
    __tablename__ = "student_profiles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False)
    xp_total = Column(Integer, default=0, nullable=False)
    current_streak = Column(Integer, default=0, nullable=False)
    longest_streak = Column(Integer, default=0, nullable=False)
    last_active_date = Column(Date, nullable=True)
    daily_goal_minutes = Column(Integer, default=30, nullable=False)
    subjects_of_interest = Column(Text, default="[]", nullable=False)
    # Track 4 Option 2 Academic Profile
    current_class = Column(String(50), nullable=True)        # e.g., Class 10, Class 11, Class 12, Undergraduate
    board = Column(String(50), nullable=True)                # e.g., CBSE, ICSE, State Board, IB
    current_marks = Column(Float, nullable=True)             # e.g., 88.5 (% or GPA)
    target_exam = Column(String(100), nullable=True)         # e.g., JEE Main, NEET, CUET, BITSAT
    career_goal = Column(String(150), nullable=True)         # e.g., Computer Science & AI, Medicine, Civil Services
    target_year = Column(Integer, nullable=True)             # e.g., 2025, 2026
    category = Column(String(20), default="General", nullable=False) # General, OBC-NCL, SC, ST, EWS
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    user = relationship("User", back_populates="profile")
