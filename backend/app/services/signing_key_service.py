import time
import secrets
import hmac
import hashlib
import uuid
import re
from datetime import datetime, timedelta
from typing import Optional, Tuple, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import text
from fastapi import HTTPException
from app.models.signing_key import SigningKey, UsedNonce

KEY_ID_REGEX = re.compile(r"^[a-zA-Z0-9_-]{1,32}$")
NONCE_REGEX = re.compile(r"^[0-9a-fA-F]{64}$")

class SigningKeyService:
    CACHE_TTL_SECONDS = 15.0  # Strict ceiling for in-memory cache

    def __init__(self):
        self._cached_key_id: Optional[str] = None
        self._cached_secret: Optional[bytes] = None
        self._cached_signing_expires_at: Optional[datetime] = None
        self._cache_deadline: float = 0.0

    def clear_cache(self):
        """For testing and rotation synchronization."""
        self._cached_key_id = None
        self._cached_secret = None
        self._cached_signing_expires_at = None
        self._cache_deadline = 0.0

    def get_signing_key(self, db: Session) -> Tuple[str, bytes]:
        """
        Retrieves active signing key enforcing strict 15s cache TTL.
        Fails closed with HTTP 503 if DB is unavailable and cache expired.
        """
        now_mono = time.monotonic()
        now_utc = datetime.utcnow()

        # Cache Hit: check monotonic deadline AND signing eligibility
        if (
            self._cached_secret
            and now_mono < self._cache_deadline
            and self._cached_signing_expires_at
            and self._cached_signing_expires_at > now_utc
        ):
            return self._cached_key_id, self._cached_secret

        # Cache Miss or Expired: Fetch from database
        try:
            key_row = db.query(SigningKey).filter(
                SigningKey.status == "ACTIVE",
                SigningKey.signing_expires_at > now_utc
            ).first()

            if not key_row:
                # If no active key exists in DB (e.g. initial setup), create default genesis key
                genesis_key_id = f"key_{secrets.token_hex(8)}"
                genesis_secret = secrets.token_bytes(32)
                key_row = SigningKey(
                    key_id=genesis_key_id,
                    key_secret=genesis_secret,
                    algorithm="sha256",
                    status="ACTIVE",
                    created_at=now_utc,
                    signing_expires_at=now_utc + timedelta(days=30),
                    verification_expires_at=now_utc + timedelta(days=30)
                )
                db.add(key_row)
                db.commit()
                db.refresh(key_row)

            # Store in cache with strict 15s deadline
            self._cached_key_id = key_row.key_id
            self._cached_secret = bytes(key_row.key_secret)
            self._cached_signing_expires_at = key_row.signing_expires_at
            self._cache_deadline = now_mono + self.CACHE_TTL_SECONDS
            return self._cached_key_id, self._cached_secret

        except Exception as exc:
            # DATABASE OUTAGE: If cache expired and DB unreachable -> fail closed!
            self.clear_cache()
            raise HTTPException(
                status_code=503,
                detail="Security signing authorization unavailable due to database outage. Token issuance suspended."
            ) from exc

    def generate_deletion_token(
        self,
        student_id: uuid.UUID,
        conversation_id: uuid.UUID,
        db: Session
    ) -> Dict[str, Any]:
        """Generates an HMAC-signed deletion authorization token."""
        key_id, key_secret = self.get_signing_key(db)
        nonce = secrets.token_hex(32)
        iat = int(datetime.utcnow().timestamp())
        exp = iat + 60  # Strict 60-second lifetime
        action = "delete_conversation"

        payload = (
            f"v1:{len(key_id)}:{key_id}:"
            f"{len(action)}:{action}:"
            f"{len(str(student_id))}:{student_id}:"
            f"{len(str(conversation_id))}:{conversation_id}:"
            f"{len(nonce)}:{nonce}:"
            f"{iat}:{exp}"
        )

        signature = hmac.new(
            key_secret,
            payload.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()

        return {
            "key_id": key_id,
            "action": action,
            "student_id": str(student_id),
            "conversation_id": str(conversation_id),
            "nonce": nonce,
            "iat": iat,
            "exp": exp,
            "signature": signature
        }

    def verify_and_consume_token(
        self,
        token_data: Dict[str, Any],
        student_id: uuid.UUID,
        conversation_id: uuid.UUID,
        db: Session
    ) -> bool:
        """
        Verifies HMAC token inside Python/PostgreSQL with timing-safe comparison,
        single-use nonce recording, and 85-second retired-key grace window.
        """
        now = int(datetime.utcnow().timestamp())
        key_id = token_data.get("key_id", "")
        nonce = token_data.get("nonce", "")
        iat = token_data.get("iat", 0)
        exp = token_data.get("exp", 0)
        signature = token_data.get("signature", "")
        action = token_data.get("action", "delete_conversation")

        # 1. Format validation
        if not KEY_ID_REGEX.match(key_id):
            raise HTTPException(status_code=400, detail="Invalid key_id format")
        if not NONCE_REGEX.match(nonce):
            raise HTTPException(status_code=400, detail="Invalid nonce format")

        # 2. Timing validation
        if exp <= iat:
            raise HTTPException(status_code=400, detail="Security token invalid: exp must be greater than iat")
        if (exp - iat) > 60:
            raise HTTPException(status_code=400, detail="Security token lifetime exceeds 60-second limit")
        if iat > (now + 5):
            raise HTTPException(status_code=400, detail="Security token issued in future (clock skew exceeded)")
        if now >= exp:
            raise HTTPException(status_code=400, detail="Security token has expired")

        # 3. Payload match validation
        if token_data.get("student_id") != str(student_id):
            raise HTTPException(status_code=403, detail="Security token student_id mismatch")
        if token_data.get("conversation_id") != str(conversation_id):
            raise HTTPException(status_code=403, detail="Security token conversation_id mismatch")

        # 4. Fetch key secret: must be ACTIVE or RETIRED with verification_expires_at > now
        now_dt = datetime.utcnow()
        key_row = db.query(SigningKey).filter(
            SigningKey.key_id == key_id,
            SigningKey.status.in_(["ACTIVE", "RETIRED"]),
            SigningKey.verification_expires_at > now_dt
        ).first()

        if not key_row:
            raise HTTPException(status_code=401, detail="Signing key unknown, revoked, or retired beyond grace period")

        # 5. Timing-safe signature comparison
        payload = (
            f"v1:{len(key_id)}:{key_id}:"
            f"{len(action)}:{action}:"
            f"{len(str(student_id))}:{student_id}:"
            f"{len(str(conversation_id))}:{conversation_id}:"
            f"{len(nonce)}:{nonce}:"
            f"{iat}:{exp}"
        )

        expected_sig = hmac.new(
            key_row.key_secret,
            payload.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(expected_sig, signature):
            raise HTTPException(status_code=401, detail="HMAC signature verification failed")

        # 6. Atomic Replay Prevention: Record nonce in database
        existing_nonce = db.query(UsedNonce).filter(UsedNonce.nonce == nonce).first()
        if existing_nonce:
            raise HTTPException(status_code=409, detail="Replay attack detected: nonce already consumed")

        used_nonce = UsedNonce(
            nonce=nonce,
            consumed_at=now_dt,
            expires_at=datetime.utcfromtimestamp(exp)
        )
        db.add(used_nonce)
        db.flush()
        return True

    def rotate_key(
        self,
        new_key_id: str,
        new_key_secret: bytes,
        db: Session
    ) -> None:
        """
        Rotates active signing key atomically:
        - Demotes active key to RETIRED (immediate signing cutoff, 85s verification grace).
        - Inserts new active key (30 days validity).
        """
        now = datetime.utcnow()
        # 1. Demote existing active key
        db.query(SigningKey).filter(SigningKey.status == "ACTIVE").update({
            "status": "RETIRED",
            "signing_expires_at": now,
            "verification_expires_at": now + timedelta(seconds=85)
        })

        # 2. Insert new active key
        new_key = SigningKey(
            key_id=new_key_id,
            key_secret=new_key_secret,
            algorithm="sha256",
            status="ACTIVE",
            created_at=now,
            signing_expires_at=now + timedelta(days=30),
            verification_expires_at=now + timedelta(days=30)
        )
        db.add(new_key)
        db.commit()
        self.clear_cache()

# Global singleton
signing_key_service = SigningKeyService()
