import uuid
from datetime import datetime
from sqlalchemy import Column, String, Enum, DateTime, Text, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database.base import Base

class AIConversation(Base):
    __tablename__ = "ai_conversations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=True)
    context_type = Column(Enum("lesson", "assessment", "general", name="context_type"), default="general", nullable=False)
    context_id = Column(UUID(as_uuid=True), nullable=True)
    last_sequence_number = Column(Integer, default=0, nullable=False)
    last_turn_number = Column(Integer, default=0, nullable=False)
    lock_version = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    student = relationship("User", back_populates="conversations")
    messages = relationship("AIMessage", back_populates="conversation", order_by="AIMessage.sequence_number", cascade="all, delete-orphan")
    turns = relationship("AITurn", back_populates="conversation", order_by="AITurn.turn_number", cascade="all, delete-orphan")
    idempotency_records = relationship("AIIdempotencyRecord", back_populates="conversation", cascade="all, delete-orphan")

class AIMessage(Base):
    __tablename__ = "ai_messages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("ai_conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    turn_id = Column(UUID(as_uuid=True), ForeignKey("ai_turns.id", ondelete="SET NULL"), nullable=True)
    role = Column(Enum("user", "assistant", "system", name="message_role"), nullable=False)
    content = Column(Text, nullable=False)
    sequence_number = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    
    __table_args__ = (
        UniqueConstraint("conversation_id", "sequence_number", name="uq_ai_messages_conv_seq"),
    )
    
    conversation = relationship("AIConversation", back_populates="messages")
    turn = relationship("AITurn", foreign_keys=[turn_id], back_populates="messages")
