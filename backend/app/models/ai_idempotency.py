import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Integer, Text, ForeignKey, UniqueConstraint, Index, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database.base import Base

class AIIdempotencyRecord(Base):
    __tablename__ = "ai_idempotency_records"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("ai_conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    turn_id = Column(UUID(as_uuid=True), ForeignKey("ai_turns.id", ondelete="SET NULL", deferrable=True, initially="DEFERRED"), nullable=True)
    idempotency_key = Column(String(128), nullable=False)
    request_hash = Column(String(64), nullable=False)
    status = Column(String(32), default="IN_PROGRESS", nullable=False)  # 'IN_PROGRESS', 'COMPLETED', 'FAILED'
    owner_token = Column(String(64), nullable=True)
    lease_expires_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    attempt_version = Column(Integer, default=1, nullable=False)
    response_body = Column(JSON, nullable=True)
    error_code = Column(String(64), nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    __table_args__ = (
        UniqueConstraint("student_id", "idempotency_key", name="uq_ai_idempotency_student_key"),
        Index("ix_ai_idempotency_lease", "status", "lease_expires_at"),
    )
    
    conversation = relationship("AIConversation", back_populates="idempotency_records")
    student = relationship("User")
    turn = relationship("AITurn", foreign_keys=[turn_id])
    turns = relationship("AITurn", foreign_keys="AITurn.idempotency_record_id", back_populates="idempotency_record")
