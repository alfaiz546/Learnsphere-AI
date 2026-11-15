import uuid
import secrets
import hashlib
import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import text, func, and_
from fastapi import HTTPException
from app.models.ai_conversation import AIConversation, AIMessage
from app.models.ai_turn import AITurn
from app.models.ai_idempotency import AIIdempotencyRecord
from app.services.signing_key_service import signing_key_service

logger = logging.getLogger(__name__)

def compute_request_hash(message: str, context: Optional[Dict] = None) -> str:
    """Computes SHA-256 hash of normalized request payload."""
    normalized = json.dumps(
        {"message": message.strip(), "context": context or {}},
        sort_keys=True
    )
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

class AIPersistenceService:
    def __init__(self, db: Session):
        self.db = db

    # -------------------------------------------------------------------------
    # Conversation CRUD & Ownership
    # -------------------------------------------------------------------------
    def create_conversation(
        self,
        student_id: uuid.UUID,
        title: Optional[str] = None,
        context_type: str = "general",
        context_id: Optional[uuid.UUID] = None
    ) -> AIConversation:
        """Creates a new conversation owned by the student."""
        conv = AIConversation(
            student_id=student_id,
            title=title or "New Learning Session",
            context_type=context_type,
            context_id=context_id,
            last_sequence_number=0,
            last_turn_number=0,
            lock_version=1
        )
        self.db.add(conv)
        self.db.commit()
        self.db.refresh(conv)
        return conv

    def list_conversations(
        self,
        student_id: uuid.UUID,
        limit: int = 20,
        offset: int = 0
    ) -> Tuple[List[AIConversation], int]:
        """Lists conversations for a student with pagination and total count."""
        query = self.db.query(AIConversation).filter(
            AIConversation.student_id == student_id
        )
        total = query.count()
        items = query.order_by(AIConversation.updated_at.desc()).offset(offset).limit(limit).all()
        return items, total

    def get_conversation_history(
        self,
        student_id: uuid.UUID,
        conversation_id: uuid.UUID,
        limit: int = 50,
        offset: int = 0
    ) -> Tuple[AIConversation, List[AIMessage], int, bool]:
        """
        Retrieves conversation and its paginated message history.
        Enforces strict student ownership.
        """
        conv = self.db.query(AIConversation).filter(
            AIConversation.id == conversation_id,
            AIConversation.student_id == student_id
        ).first()

        if not conv:
            raise HTTPException(status_code=404, detail="Conversation not found or unauthorized")

        total_messages = self.db.query(AIMessage).filter(
            AIMessage.conversation_id == conversation_id
        ).count()

        messages = self.db.query(AIMessage).filter(
            AIMessage.conversation_id == conversation_id
        ).order_by(AIMessage.sequence_number.asc()).offset(offset).limit(limit).all()

        has_more = (offset + len(messages)) < total_messages
        return conv, messages, total_messages, has_more

    def get_conversation_ownership(
        self,
        student_id: uuid.UUID,
        conversation_id: uuid.UUID,
    ) -> Optional[AIConversation]:
        """
        Returns the conversation if it exists and is owned by the student.
        Used by the deletion-token endpoint to verify ownership before
        issuing a signed deletion token.
        """
        return self.db.query(AIConversation).filter(
            AIConversation.id == conversation_id,
            AIConversation.student_id == student_id
        ).first()

    def rename_conversation(
        self,
        student_id: uuid.UUID,
        conversation_id: uuid.UUID,
        new_title: str
    ) -> AIConversation:
        """Renames conversation with ownership check."""
        conv = self.db.query(AIConversation).filter(
            AIConversation.id == conversation_id,
            AIConversation.student_id == student_id
        ).first()

        if not conv:
            raise HTTPException(status_code=404, detail="Conversation not found or unauthorized")

        conv.title = new_title.strip()
        conv.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(conv)
        return conv

    def delete_conversation(
        self,
        student_id: uuid.UUID,
        conversation_id: uuid.UUID,
        token_data: Dict[str, Any]
    ) -> None:
        """
        Deletes a conversation and all dependent records in proven safe topological order:
        1. Validates HMAC deletion token (REQUIRED).
        2. Locks parent conversation row (Level 1) with FOR UPDATE.
        3. Severs circular foreign keys (turn <-> idempotency record, message <-> turn).
        4. Deletes ai_turns first (satisfying user_message_id RESTRICT constraint).
        5. Deletes ai_idempotency_records second.
        6. Deletes ai_messages third (now free of foreign key references).
        7. Deletes ai_conversations finally and commits atomically.
        """
        # Token verification is REQUIRED - rejects replayed, expired, or invalid tokens
        signing_key_service.verify_and_consume_token(
            token_data, student_id, conversation_id, self.db
        )

        try:
            # 1. Lock parent conversation row (Level 1)
            conv = self.db.query(AIConversation).filter(
                AIConversation.id == conversation_id,
                AIConversation.student_id == student_id
            ).with_for_update().first()

            if not conv:
                raise HTTPException(status_code=404, detail="Conversation not found or unauthorized")

            # 2. Break circular / cross-table foreign key references
            self.db.query(AITurn).filter(
                AITurn.conversation_id == conversation_id
            ).update({"idempotency_record_id": None}, synchronize_session=False)

            self.db.query(AIIdempotencyRecord).filter(
                AIIdempotencyRecord.conversation_id == conversation_id
            ).update({"turn_id": None}, synchronize_session=False)

            self.db.query(AIMessage).filter(
                AIMessage.conversation_id == conversation_id
            ).update({"turn_id": None}, synchronize_session=False)

            # 3. Delete dependent turns first (resolving user_message_id RESTRICT FK before deleting messages)
            self.db.query(AITurn).filter(
                AITurn.conversation_id == conversation_id
            ).delete(synchronize_session=False)

            # 4. Delete idempotency records
            self.db.query(AIIdempotencyRecord).filter(
                AIIdempotencyRecord.conversation_id == conversation_id
            ).delete(synchronize_session=False)

            # 5. Delete messages (now guaranteed to have zero referencing turns)
            self.db.query(AIMessage).filter(
                AIMessage.conversation_id == conversation_id
            ).delete(synchronize_session=False)

            # 6. Delete parent conversation
            self.db.delete(conv)
            self.db.commit()

        except HTTPException:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error during safe conversation deletion: {e}")
            raise HTTPException(status_code=500, detail="Failed to delete conversation")

    # -------------------------------------------------------------------------
    # Concurrency-Safe Turn Lifecycle adhering to Universal Lock Hierarchy:
    # Level 1: ai_conversations -> Level 2: ai_messages -> Level 3: ai_turns -> Level 4: ai_idempotency_records
    # -------------------------------------------------------------------------
    def initiate_turn(
        self,
        student_id: uuid.UUID,
        conversation_id: uuid.UUID,
        user_message_text: str,
        idempotency_key: str,
        context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Initiates a turn atomically:
        - Locks ai_conversations (Level 1)
        - Enforces single generating turn constraint
        - Handles durable idempotency checking & replay
        - Inserts user message (Level 2)
        - Inserts generating turn (Level 3)
        - Inserts in-progress idempotency record (Level 4)

        idempotency_key is REQUIRED. The caller must supply a stable key per
        logical chat submission and reuse it for retries. Missing keys are
        rejected with HTTP 400 to prevent silent bypass of exactly-once
        semantics.
        """
        if not idempotency_key or not idempotency_key.strip():
            raise HTTPException(
                status_code=400,
                detail="idempotency_key is required for chat submissions"
            )
        now = datetime.now(timezone.utc)
        req_hash = compute_request_hash(user_message_text, context)
        key = idempotency_key.strip()

        try:
            # 1. Lock parent conversation (Level 1)
            conv = self.db.query(AIConversation).filter(
                AIConversation.id == conversation_id,
                AIConversation.student_id == student_id
            ).with_for_update().first()

            if not conv:
                raise HTTPException(status_code=404, detail="Conversation not found or unauthorized")

            # 2. Invariant Check: Enforce single generating turn
            active_turn = self.db.query(AITurn).filter(
                AITurn.conversation_id == conversation_id,
                AITurn.status == "generating"
            ).first()

            if active_turn:
                raise HTTPException(
                    status_code=409,
                    detail="A turn is currently generating in this conversation. Please wait for completion or failure before sending another message."
                )

            # 3. Idempotency Check
            existing_record = self.db.query(AIIdempotencyRecord).filter(
                AIIdempotencyRecord.student_id == student_id,
                AIIdempotencyRecord.idempotency_key == key
            ).with_for_update().first()

            if existing_record:
                # Payload mismatch check
                if existing_record.request_hash != req_hash:
                    raise HTTPException(
                        status_code=422,
                        detail="Idempotency key already exists with a different request payload."
                    )
                # Completed replay
                if existing_record.status == "COMPLETED" and existing_record.response_body:
                    return {
                        "is_replay": True,
                        "response_data": existing_record.response_body,
                        "conversation_id": str(conversation_id),
                        "turn_id": str(existing_record.turn_id) if existing_record.turn_id else None
                    }
                # Active in-progress check
                if existing_record.status == "IN_PROGRESS":
                    if existing_record.lease_expires_at and existing_record.lease_expires_at > now:
                        raise HTTPException(
                            status_code=409,
                            detail="A request with this idempotency key is currently being processed."
                        )

            # 4. Sequence and Turn Allocation
            s_user = conv.last_sequence_number + 1
            t_num = conv.last_turn_number + 1
            user_msg_id = uuid.uuid4()
            turn_id = uuid.uuid4()
            rec_id = existing_record.id if existing_record else uuid.uuid4()
            worker_token = secrets.token_hex(16)

            # 5. Insert User Message (Level 2) - turn_id initially None to satisfy FK graph before turn exists
            user_msg = AIMessage(
                id=user_msg_id,
                conversation_id=conversation_id,
                role="user",
                content=user_message_text,
                sequence_number=s_user,
                turn_id=None,
                created_at=now
            )
            self.db.add(user_msg)
            self.db.flush()

            # 6. Insert Generating Turn (Level 3) referencing now-persisted user_msg_id
            turn = AITurn(
                id=turn_id,
                conversation_id=conversation_id,
                turn_number=t_num,
                status="generating",
                user_message_id=user_msg_id,
                assistant_message_id=None,
                idempotency_record_id=rec_id,
                attempt_version=1,
                created_at=now,
                updated_at=now
            )
            self.db.add(turn)
            self.db.flush()

            # Link user message to created turn
            user_msg.turn_id = turn_id

            # 7. Insert or Update Idempotency Record (Level 4)
            if existing_record:
                existing_record.turn_id = turn_id
                existing_record.status = "IN_PROGRESS"
                existing_record.owner_token = worker_token
                existing_record.lease_expires_at = now + timedelta(seconds=30)
                existing_record.attempt_version += 1
                existing_record.updated_at = now
            else:
                idemp_rec = AIIdempotencyRecord(
                    id=rec_id,
                    conversation_id=conversation_id,
                    student_id=student_id,
                    turn_id=turn_id,
                    idempotency_key=key,
                    request_hash=req_hash,
                    status="IN_PROGRESS",
                    owner_token=worker_token,
                    lease_expires_at=now + timedelta(seconds=30),
                    expires_at=now + timedelta(hours=24),
                    attempt_version=1,
                    created_at=now,
                    updated_at=now
                )
                self.db.add(idemp_rec)

            # 8. Advance Conversation Counters
            conv.last_sequence_number = s_user
            conv.last_turn_number = t_num
            conv.updated_at = now

            self.db.commit()

            return {
                "is_replay": False,
                "conversation_id": str(conversation_id),
                "turn_id": str(turn_id),
                "user_message_id": str(user_msg_id),
                "idempotency_record_id": str(rec_id),
                "worker_token": worker_token,
                "sequence_number": s_user,
                "turn_number": t_num,
                "attempt_version": 1
            }

        except HTTPException:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            # Catch database unique constraint violation if concurrent request won the race
            if "uq_ai_turns_single_generating" in str(e):
                raise HTTPException(
                    status_code=409,
                    detail="A turn is currently generating in this conversation."
                )
            logger.error(f"Error initiating turn: {e}")
            raise HTTPException(status_code=500, detail="Failed to initiate AI turn")

    def complete_turn(
        self,
        conversation_id: uuid.UUID,
        turn_id: uuid.UUID,
        assistant_response_text: str,
        idempotency_record_id: uuid.UUID,
        worker_token: str,
        tools_used: List[str] = []
    ) -> Dict[str, Any]:
        """
        Completes turn atomically:
        - Locks ai_conversations (Level 1)
        - Allocates assistant sequence number
        - Inserts assistant message (Level 2)
        - Updates turn to 'completed' (Level 3)
        - Updates idempotency record to 'COMPLETED' (Level 4)
        """
        now = datetime.now(timezone.utc)
        try:
            # 1. Lock conversation (Level 1)
            conv = self.db.query(AIConversation).filter(
                AIConversation.id == conversation_id
            ).with_for_update().first()

            if not conv:
                raise HTTPException(status_code=404, detail="Conversation not found")

            # 2. Sequence Allocation for Assistant Message
            s_asst = conv.last_sequence_number + 1
            asst_msg_id = uuid.uuid4()

            # 3. Insert Assistant Message First (Level 2) and flush so assistant_message_id FK is valid
            asst_msg = AIMessage(
                id=asst_msg_id,
                conversation_id=conversation_id,
                role="assistant",
                content=assistant_response_text,
                sequence_number=s_asst,
                turn_id=turn_id,
                created_at=now
            )
            self.db.add(asst_msg)
            self.db.flush()

            # 4. Update Turn (Level 3) with rowcount assertion
            turn_count = self.db.query(AITurn).filter(
                AITurn.id == turn_id,
                AITurn.status == "generating"
            ).update({
                "assistant_message_id": asst_msg_id,
                "status": "completed",
                "updated_at": now
            })

            if turn_count != 1:
                self.db.rollback()
                raise HTTPException(status_code=409, detail="Turn completion conflict: turn not in generating state")

            # 5. Update Idempotency Record (Level 4)
            response_payload = {
                "response": assistant_response_text,
                "tools_used": tools_used,
                "conversation_id": str(conversation_id),
                "turn_id": str(turn_id),
                "sequence_number": s_asst
            }

            rec_count = self.db.query(AIIdempotencyRecord).filter(
                AIIdempotencyRecord.id == idempotency_record_id,
                AIIdempotencyRecord.status == "IN_PROGRESS"
            ).update({
                "status": "COMPLETED",
                "response_body": response_payload,
                "owner_token": None,
                "lease_expires_at": None,
                "updated_at": now
            })

            if rec_count != 1:
                self.db.rollback()
                raise HTTPException(status_code=409, detail="Idempotency completion conflict")

            # 6. Update Conversation Counters
            conv.last_sequence_number = s_asst
            conv.updated_at = now

            self.db.commit()

            return response_payload

        except HTTPException:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error completing turn: {e}")
            raise HTTPException(status_code=500, detail="Failed to complete AI turn")

    def fail_turn(
        self,
        conversation_id: uuid.UUID,
        turn_id: uuid.UUID,
        idempotency_record_id: uuid.UUID,
        error_code: str,
        error_message: str
    ) -> None:
        """
        Fails turn atomically without burning sequence numbers:
        - Locks conversation (Level 1)
        - Updates turn to 'failed' (Level 3)
        - Updates idempotency record to 'FAILED' (Level 4)
        """
        now = datetime.now(timezone.utc)
        try:
            # 1. Lock conversation (Level 1)
            conv = self.db.query(AIConversation).filter(
                AIConversation.id == conversation_id
            ).with_for_update().first()

            # 2. Update Turn (Level 3)
            turn_count = self.db.query(AITurn).filter(
                AITurn.id == turn_id,
                AITurn.status == "generating"
            ).update({
                "status": "failed",
                "error_code": error_code,
                "error_message": error_message,
                "updated_at": now
            })

            # 3. Update Idempotency Record (Level 4)
            rec_count = self.db.query(AIIdempotencyRecord).filter(
                AIIdempotencyRecord.id == idempotency_record_id,
                AIIdempotencyRecord.status == "IN_PROGRESS"
            ).update({
                "status": "FAILED",
                "error_code": error_code,
                "error_message": error_message,
                "owner_token": None,
                "lease_expires_at": None,
                "updated_at": now
            })

            if turn_count != 1 or rec_count != 1:
                logger.warning(f"Unexpected rowcount in fail_turn: turn={turn_count}, rec={rec_count}")

            self.db.commit()

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error marking turn failed: {e}")

    def retry_turn(
        self,
        student_id: uuid.UUID,
        turn_id: uuid.UUID
    ) -> Dict[str, Any]:
        """
        Retries a failed turn with version fencing:
        - Verifies turn is 'failed' and linked idempotency record is 'FAILED'
        - Increments attempt_version on both rows atomically
        - Sets status back to 'generating' / 'IN_PROGRESS'
        """
        now = datetime.now(timezone.utc)
        try:
            # Find turn
            turn = self.db.query(AITurn).filter(AITurn.id == turn_id).first()
            if not turn:
                raise HTTPException(status_code=404, detail="Turn not found")

            # Lock parent conversation (Level 1)
            conv = self.db.query(AIConversation).filter(
                AIConversation.id == turn.conversation_id,
                AIConversation.student_id == student_id
            ).with_for_update().first()

            if not conv:
                raise HTTPException(status_code=404, detail="Conversation not found or unauthorized")

            # Check no other turn is generating
            active_turn = self.db.query(AITurn).filter(
                AITurn.conversation_id == turn.conversation_id,
                AITurn.status == "generating"
            ).first()

            if active_turn:
                raise HTTPException(
                    status_code=409,
                    detail="Another turn is currently generating in this conversation."
                )

            if turn.status != "failed":
                raise HTTPException(status_code=400, detail="Only failed turns can be retried")

            expected_version = turn.attempt_version
            new_version = expected_version + 1
            new_worker_token = secrets.token_hex(16)

            # Update Turn (Level 3)
            turn_count = self.db.query(AITurn).filter(
                AITurn.id == turn_id,
                AITurn.status == "failed",
                AITurn.attempt_version == expected_version
            ).update({
                "status": "generating",
                "attempt_version": new_version,
                "error_code": None,
                "error_message": None,
                "updated_at": now
            })

            if turn_count != 1:
                self.db.rollback()
                raise HTTPException(status_code=409, detail="Turn retry conflict: attempt version mismatch")

            # Update Idempotency Record (Level 4)
            rec_count = self.db.query(AIIdempotencyRecord).filter(
                AIIdempotencyRecord.id == turn.idempotency_record_id,
                AIIdempotencyRecord.status == "FAILED",
                AIIdempotencyRecord.attempt_version == expected_version
            ).update({
                "status": "IN_PROGRESS",
                "owner_token": new_worker_token,
                "lease_expires_at": now + timedelta(seconds=30),
                "attempt_version": new_version,
                "error_code": None,
                "error_message": None,
                "updated_at": now
            })

            if rec_count != 1:
                self.db.rollback()
                raise HTTPException(status_code=409, detail="Idempotency record retry conflict")

            self.db.commit()

            # Retrieve user message text for re-execution
            user_msg = self.db.query(AIMessage).filter(AIMessage.id == turn.user_message_id).first()

            return {
                "turn_id": str(turn_id),
                "conversation_id": str(turn.conversation_id),
                "idempotency_record_id": str(turn.idempotency_record_id),
                "user_message": user_msg.content if user_msg else "",
                "attempt_version": new_version,
                "worker_token": new_worker_token
            }

        except HTTPException:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error retrying turn: {e}")
            raise HTTPException(status_code=500, detail="Failed to retry AI turn")

    def recover_abandoned_turn(self) -> Optional[Tuple[str, str]]:
        """
        Background maintenance sweep for abandoned turns.
        Strictly locks Level 3 (ai_turns) via SKIP LOCKED, then Level 4 (ai_idempotency_records).
        """
        now = datetime.now(timezone.utc)
        try:
            # Step 1: Lock Turn (Level 3) using SKIP LOCKED
            turn = (
                self.db.query(AITurn)
                .join(AIIdempotencyRecord, AIIdempotencyRecord.id == AITurn.idempotency_record_id)
                .filter(
                    AITurn.status == "generating",
                    AIIdempotencyRecord.status == "IN_PROGRESS",
                    AIIdempotencyRecord.lease_expires_at < now,
                    AIIdempotencyRecord.expires_at > now
                )
                .with_for_update(skip_locked=True)
                .first()
            )

            if not turn:
                return None

            turn_id = turn.id
            rec_id = turn.idempotency_record_id
            expected_version = turn.attempt_version

            # Step 2: Lock Idempotency Record (Level 4)
            rec = (
                self.db.query(AIIdempotencyRecord)
                .filter(AIIdempotencyRecord.id == rec_id)
                .with_for_update()
                .first()
            )

            if (
                not rec
                or rec.status != "IN_PROGRESS"
                or (rec.lease_expires_at and rec.lease_expires_at >= now)
                or rec.attempt_version != expected_version
            ):
                self.db.rollback()
                return None

            # Step 3: Transition Turn (Level 3)
            turn_count = self.db.query(AITurn).filter(
                AITurn.id == turn_id,
                AITurn.status == "generating",
                AITurn.attempt_version == expected_version
            ).update({
                "status": "failed",
                "error_code": "LEASE_TIMEOUT_ABANDONED",
                "error_message": "Worker lease expired without completion",
                "updated_at": now
            })

            # Step 4: Transition Idempotency Record (Level 4)
            rec_count = self.db.query(AIIdempotencyRecord).filter(
                AIIdempotencyRecord.id == rec_id,
                AIIdempotencyRecord.status == "IN_PROGRESS",
                AIIdempotencyRecord.attempt_version == expected_version,
                AIIdempotencyRecord.lease_expires_at < now
            ).update({
                "status": "FAILED",
                "error_code": "LEASE_TIMEOUT_ABANDONED",
                "error_message": "Worker lease expired without completion",
                "owner_token": None,
                "lease_expires_at": None,
                "updated_at": now
            })

            if turn_count != 1 or rec_count != 1:
                self.db.rollback()
                return None

            self.db.commit()
            return str(rec_id), str(turn_id)

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error during abandoned recovery: {e}")
            return None

    def cleanup_expired_records(self, batch_size: int = 100) -> Dict[str, int]:
        """
        Safely purges expired terminal idempotency records and expired used nonces.
        Invariants strictly enforced:
        - Never purges IN_PROGRESS records or records with active leases.
        - Never purges records associated with generating turns.
        - Only purges terminal status records ('COMPLETED', 'FAILED') where expires_at <= now.
        - Severs foreign key references from ai_turns prior to deletion.
        - Employs bounded batches and SKIP LOCKED to prevent contention.
        - Safe, idempotent, observable (returns purge counts without logging sensitive data).
        """
        from app.models.signing_key import UsedNonce

        now = datetime.now(timezone.utc)
        idemp_deleted = 0
        nonces_deleted = 0

        try:
            # 1. Select candidate expired terminal idempotency records using SKIP LOCKED
            candidate_records = (
                self.db.query(AIIdempotencyRecord)
                .filter(
                    AIIdempotencyRecord.status.in_(["COMPLETED", "FAILED"]),
                    AIIdempotencyRecord.expires_at <= now,
                    (AIIdempotencyRecord.lease_expires_at == None) | (AIIdempotencyRecord.lease_expires_at <= now)
                )
                .with_for_update(skip_locked=True)
                .limit(batch_size)
                .all()
            )

            if candidate_records:
                record_ids = [r.id for r in candidate_records]

                # Ensure none of these are referenced by a generating turn
                generating_turn_refs = (
                    self.db.query(AITurn.idempotency_record_id)
                    .filter(
                        AITurn.idempotency_record_id.in_(record_ids),
                        AITurn.status == "generating"
                    )
                    .all()
                )
                active_ids = {r[0] for r in generating_turn_refs if r[0]}
                safe_ids = [rid for rid in record_ids if rid not in active_ids]

                if safe_ids:
                    # Sever foreign keys in ai_turns first
                    self.db.query(AITurn).filter(
                        AITurn.idempotency_record_id.in_(safe_ids)
                    ).update({"idempotency_record_id": None}, synchronize_session=False)

                    # Delete safe expired records
                    idemp_deleted = (
                        self.db.query(AIIdempotencyRecord)
                        .filter(AIIdempotencyRecord.id.in_(safe_ids))
                        .delete(synchronize_session=False)
                    )

            # 2. Purge expired nonces
            try:
                candidate_nonces = (
                    self.db.query(UsedNonce)
                    .filter(UsedNonce.expires_at <= now)
                    .with_for_update(skip_locked=True)
                    .limit(batch_size)
                    .all()
                )
                if candidate_nonces:
                    nonce_vals = [n.nonce for n in candidate_nonces]
                    nonces_deleted = (
                        self.db.query(UsedNonce)
                        .filter(UsedNonce.nonce.in_(nonce_vals))
                        .delete(synchronize_session=False)
                    )
            except Exception as nonce_err:
                logger.warning(f"Nonce cleanup skipped or failed: {nonce_err}")

            self.db.commit()

            logger.info(
                f"Expired record cleanup completed: {idemp_deleted} idempotency records purged, "
                f"{nonces_deleted} nonces purged"
            )
            return {
                "idempotency_records_purged": idemp_deleted,
                "nonces_purged": nonces_deleted
            }

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error during expired record cleanup: {e}")
            return {
                "idempotency_records_purged": 0,
                "nonces_purged": 0
            }
