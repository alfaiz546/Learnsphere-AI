import uuid
from datetime import datetime
from sqlalchemy import Column, String, Enum, DateTime, Text, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database.base import Base

class AgentExecutionLog(Base):
    __tablename__ = "agent_execution_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    session_id = Column(String(255), nullable=True)
    tool_name = Column(String(100), nullable=False)
    input_data = Column(Text, default="{}", nullable=False)
    output_data = Column(Text, default="{}", nullable=False)
    status = Column(Enum("started", "success", "failed", "timeout", name="log_status"), default="started", nullable=False)
    execution_time_ms = Column(Integer, default=0, nullable=False)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    student = relationship("User")
