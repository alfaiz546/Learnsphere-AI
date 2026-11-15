import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Integer, Text, ForeignKey, UniqueConstraint, Index, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database.base import Base

class AITurn(Base):
    __tablename__ = "ai_turns"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("ai_conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    turn_number = Column(Integer, nullable=False)
    status = Column(String(32), default="generating", nullable=False)  # 'generating', 'completed', 'failed'
    user_message_id = Column(UUID(as_uuid=True), ForeignKey("ai_messages.id", ondelete="RESTRICT"), nullable=False)
    assistant_message_id = Column(UUID(as_uuid=True), ForeignKey("ai_messages.id", ondelete="SET NULL"), nullable=True)
    idempotency_record_id = Column(UUID(as_uuid=True), ForeignKey("ai_idempotency_records.id", ondelete="SET NULL", deferrable=True, initially="DEFERRED"), nullable=True)
    attempt_version = Column(Integer, default=1, nullable=False)
    error_code = Column(String(64), nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    __table_args__ = (
        UniqueConstraint("conversation_id", "turn_number", name="uq_ai_turns_conv_turn"),
        Index(
            "uq_ai_turns_single_generating",
            "conversation_id",
            unique=True,
            postgresql_where=text("status = 'generating'"),
            sqlite_where=text("status = 'generating'")
        ),
    )
    
    conversation = relationship("AIConversation", back_populates="turns")
    user_message = relationship("AIMessage", foreign_keys=[user_message_id])
    assistant_message = relationship("AIMessage", foreign_keys=[assistant_message_id])
    idempotency_record = relationship("AIIdempotencyRecord", foreign_keys=[idempotency_record_id], back_populates="turns")
    messages = relationship("AIMessage", foreign_keys="AIMessage.turn_id", back_populates="turn")
