from datetime import datetime
from sqlalchemy import Column, String, DateTime, LargeBinary, Index, text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from app.database.base import Base

class SigningKey(Base):
    """
    Tracks active, retired, and revoked signing keys.
    Mapped to auth_security.signing_keys per the Phase 2.5 migration.
    """
    __tablename__ = "signing_keys"
    __table_args__ = {"schema": "auth_security"}

    key_id = Column(String(32), primary_key=True)
    key_secret = Column(LargeBinary, nullable=False)
    algorithm = Column(String(16), default="sha256", nullable=False)
    status = Column(String(16), default="ACTIVE", nullable=False)  # 'ACTIVE', 'RETIRED', 'REVOKED'
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    signing_expires_at = Column(DateTime(timezone=True), nullable=False)
    verification_expires_at = Column(DateTime(timezone=True), nullable=False)

class UsedNonce(Base):
    """
    Single-use nonce tracker for replay-protection of HMAC deletion tokens.
    Mapped to auth_security.used_nonces per the Phase 2.5 migration.
    """
    __tablename__ = "used_nonces"
    __table_args__ = {"schema": "auth_security"}

    nonce = Column(String(64), primary_key=True)
    consumed_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
