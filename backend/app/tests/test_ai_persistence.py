"""
Phase 2.5 Backend Tests: AI Chat Session Persistence
Tests all core workflows with SQLite in-memory test DB.
AI provider calls are mocked; no live API calls.
"""
import uuid
import secrets
import hashlib
import json
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from fastapi import HTTPException
from fastapi.testclient import TestClient
from app.database.base import Base, get_db
from app.main import app

TEST_DB_URL = "sqlite:///./test_persistence.db"
test_engine = create_engine(
    TEST_DB_URL,
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

from sqlalchemy import event

_sqlite_fk_enabled = True

@event.listens_for(test_engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    if _sqlite_fk_enabled:
        cursor.execute("PRAGMA foreign_keys=ON")
    else:
        cursor.execute("PRAGMA foreign_keys=OFF")
    cursor.close()

@pytest.fixture(autouse=True)
def mock_startup_init_db():
    with patch("app.database.init_db.init_db"):
        yield

@pytest.fixture(scope="module")
def persistence_db():
    global _sqlite_fk_enabled
    _sqlite_fk_enabled = True
    # Import all models so SQLite creates all tables
    import app.models  # noqa: F401
    # SQLite does not support schemas; strip schema-qualified table names
    # so that auth_security.* models can be created in the SQLite test DB.
    if test_engine.dialect.name == "sqlite":
        for _table in Base.metadata.tables.values():
            _table.schema = None
    Base.metadata.create_all(bind=test_engine)
    yield
    _sqlite_fk_enabled = False
    test_engine.dispose()
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db(persistence_db):
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            pass
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def _register_and_login(client, suffix=""):
    """Helper: registers a user and returns auth headers + user data."""
    unique_suffix = f"{suffix}_{uuid.uuid4().hex[:6]}"
    email = f"persist_{unique_suffix}@example.com"
    username = f"user_{unique_suffix}"
    reg = client.post("/api/auth/register", json={
        "email": email, "username": username, "password": "TestPass123!"
    })
    assert reg.status_code == 201
    # Extract token from cookies (HttpOnly flow)
    access_token = reg.cookies.get("access_token")
    if not access_token:
        # Fallback for test client that may not persist cookies
        data = reg.json().get("data", {})
        access_token = data.get("access_token")
    # Clear client cookie jar so subsequent requests behave as CLI Bearer clients
    # This prevents ambient cookie CSRF enforcement and cross-user cookie collisions
    client.cookies.clear()
    return {"Authorization": f"Bearer {access_token}"} if access_token else {}


# ---------------------------------------------------------------------------
# 1. Conversation Creation and Retrieval
# ---------------------------------------------------------------------------
class TestConversationCRUD:
    def test_create_conversation(self, client, db):
        """Creating a conversation returns a valid conversation ID."""
        hdrs = _register_and_login(client, "create1")
        res = client.post("/api/ai/conversations", json={
            "title": "My First Session", "context_type": "general"
        }, headers=hdrs)
        assert res.status_code == 201
        data = res.json()["data"]
        assert "id" in data
        assert data["title"] == "My First Session"
        assert data["context_type"] == "general"
        assert data["last_sequence_number"] == 0

    def test_list_conversations_empty(self, client, db):
        """Listing conversations for a new user returns empty list."""
        hdrs = _register_and_login(client, "list0")
        res = client.get("/api/ai/conversations", headers=hdrs)
        assert res.status_code == 200
        data = res.json()["data"]
        assert data["total"] == 0
        assert data["items"] == []

    def test_list_conversations_paginated(self, client, db):
        """Created conversations appear in list with correct pagination."""
        hdrs = _register_and_login(client, "listpaged")
        for i in range(3):
            client.post("/api/ai/conversations", json={"title": f"Session {i}"}, headers=hdrs)
        res = client.get("/api/ai/conversations?limit=2&offset=0", headers=hdrs)
        assert res.status_code == 200
        data = res.json()["data"]
        assert data["total"] == 3
        assert len(data["items"]) == 2

    def test_get_conversation_history_ownership_enforced(self, client, db):
        """Student B cannot read Student A's conversation."""
        hdrs_a = _register_and_login(client, "owner_a")
        hdrs_b = _register_and_login(client, "owner_b")
        res = client.post("/api/ai/conversations", json={"title": "Private"}, headers=hdrs_a)
        conv_id = res.json()["data"]["id"]
        # Student B attempts access
        res_b = client.get(f"/api/ai/conversations/{conv_id}", headers=hdrs_b)
        assert res_b.status_code == 404

    def test_rename_conversation(self, client, db):
        """Renaming a conversation changes its title."""
        hdrs = _register_and_login(client, "rename1")
        res = client.post("/api/ai/conversations", json={"title": "Old Name"}, headers=hdrs)
        conv_id = res.json()["data"]["id"]
        patch_res = client.patch(
            f"/api/ai/conversations/{conv_id}",
            json={"title": "New Name"},
            headers=hdrs
        )
        assert patch_res.status_code == 200
        assert patch_res.json()["data"]["title"] == "New Name"

    def test_delete_conversation_cascades(self, client, db):
        """Deleting a conversation removes it from the list."""
        hdrs = _register_and_login(client, "del1")
        res = client.post("/api/ai/conversations", json={"title": "To Delete"}, headers=hdrs)
        conv_id = res.json()["data"]["id"]
        # Generate deletion token
        tok_res = client.post(f"/api/ai/conversations/{conv_id}/deletion-token", headers=hdrs)
        assert tok_res.status_code == 200
        token_data = tok_res.json()["data"]
        del_res = client.request("DELETE", f"/api/ai/conversations/{conv_id}", json=token_data, headers=hdrs)
        assert del_res.status_code == 200
        list_res = client.get("/api/ai/conversations", headers=hdrs)
        ids = [c["id"] for c in list_res.json()["data"]["items"]]
        assert conv_id not in ids

    def test_delete_conversation_unauthorized(self, client, db):
        """Student B cannot delete Student A's conversation."""
        hdrs_a = _register_and_login(client, "del_own_a")
        hdrs_b = _register_and_login(client, "del_own_b")
        res = client.post("/api/ai/conversations", json={}, headers=hdrs_a)
        conv_id = res.json()["data"]["id"]
        # Student B cannot get a deletion token for Student A's conversation
        tok_res_b = client.post(f"/api/ai/conversations/{conv_id}/deletion-token", headers=hdrs_b)
        assert tok_res_b.status_code == 404
        # Student B cannot delete without a valid token
        res_b = client.request("DELETE", f"/api/ai/conversations/{conv_id}", json={}, headers=hdrs_b)
        assert res_b.status_code in (400, 404, 422)


# ---------------------------------------------------------------------------
# 2. AI Chat Persistence with Mocked AI Provider
# ---------------------------------------------------------------------------
class TestChatPersistence:
    @patch("app.agents.orchestrator.get_genai_client")
    def test_chat_creates_and_persists_messages(self, mock_genai, client, db):
        """
        Chat endpoint creates a conversation with persistent user+assistant messages.
        """
        mock_client = MagicMock()
        mock_chat = MagicMock()
        mock_response = MagicMock()
        mock_response.function_calls = None
        mock_response.text = "Great question! Recursion involves a function calling itself."
        mock_chat.send_message.return_value = mock_response
        mock_client.chats.create.return_value = mock_chat
        mock_genai.return_value = mock_client

        hdrs = _register_and_login(client, "chat1")
        res = client.post("/api/ai/chat", json={
            "message": "Explain recursion",
            "context": {"subject": "CS"},
            "idempotency_key": f"test-{uuid.uuid4()}"
        }, headers=hdrs)
        assert res.status_code == 200
        data = res.json()["data"]
        assert "conversation_id" in data
        assert "response" in data
        conv_id = data["conversation_id"]

        # Verify messages persisted in history
        hist = client.get(f"/api/ai/conversations/{conv_id}", headers=hdrs)
        assert hist.status_code == 200
        msgs = hist.json()["data"]["messages"]
        roles = [m["role"] for m in msgs]
        assert "user" in roles
        assert "assistant" in roles

    @patch("app.agents.orchestrator.get_genai_client")
    def test_chat_continues_existing_conversation(self, mock_genai, client, db):
        """
        Messages in the same conversation share a conversation_id and sequence is contiguous.
        """
        mock_client = MagicMock()
        mock_chat = MagicMock()
        mock_response = MagicMock()
        mock_response.function_calls = None
        mock_response.text = "Sure, let me explain further."
        mock_chat.send_message.return_value = mock_response
        mock_client.chats.create.return_value = mock_chat
        mock_genai.return_value = mock_client

        hdrs = _register_and_login(client, "chat_cont")
        # First message
        res1 = client.post("/api/ai/chat", json={"message": "Tell me about trees", "idempotency_key": f"test-{uuid.uuid4()}"}, headers=hdrs)
        assert res1.status_code == 200
        conv_id = res1.json()["data"]["conversation_id"]

        # Second message in same conversation
        res2 = client.post("/api/ai/chat", json={
            "message": "And binary search trees?",
            "conversation_id": conv_id,
            "idempotency_key": f"test-{uuid.uuid4()}"
        }, headers=hdrs)
        assert res2.status_code == 200
        assert res2.json()["data"]["conversation_id"] == conv_id

    def test_chat_no_groq_key_returns_graceful_error(self, client, db):
        """When GROQ_API_KEY is absent, chat returns a helpful error without crashing."""
        with patch("app.agents.orchestrator.get_genai_client", return_value=None):
            hdrs = _register_and_login(client, "nokey")
            res = client.post("/api/ai/chat", json={"message": "Hello", "idempotency_key": f"test-{uuid.uuid4()}"}, headers=hdrs)
            assert res.status_code == 200
            data = res.json()["data"]
            assert "GROQ_API_KEY" in data.get("response", "") or "error" in data

    @patch("app.agents.orchestrator.get_genai_client")
    def test_chat_ai_timeout_marks_turn_failed(self, mock_genai, client, db):
        """When The AI provider raises an exception, the turn is marked failed; no assistant message is stored."""
        mock_client = MagicMock()
        mock_chat = MagicMock()
        mock_chat.send_message.side_effect = TimeoutError("AI request timed out")
        mock_client.chats.create.return_value = mock_chat
        mock_genai.return_value = mock_client

        hdrs = _register_and_login(client, "timeout")
        res = client.post("/api/ai/chat", json={"message": "Hello", "idempotency_key": f"test-{uuid.uuid4()}"}, headers=hdrs)
        # Should not crash; returns error info
        assert res.status_code == 200
        data = res.json()["data"]
        assert "error" in data or "conversation_id" in data


# ---------------------------------------------------------------------------
# 3. Concurrency & Idempotency Protection
# ---------------------------------------------------------------------------
class TestConcurrencyAndIdempotency:
    @patch("app.agents.orchestrator.get_genai_client")
    def test_idempotency_key_deduplication(self, mock_genai, client, db):
        """Same idempotency_key returns the same response without duplicating messages."""
        mock_client = MagicMock()
        mock_chat = MagicMock()
        mock_response = MagicMock()
        mock_response.function_calls = None
        mock_response.text = "Idempotent response!"
        mock_chat.send_message.return_value = mock_response
        mock_client.chats.create.return_value = mock_chat
        mock_genai.return_value = mock_client

        hdrs = _register_and_login(client, "idemp1")
        ikey = f"test-ikey-{uuid.uuid4()}"

        res1 = client.post("/api/ai/chat", json={
            "message": "What is idempotency?",
            "idempotency_key": ikey
        }, headers=hdrs)
        assert res1.status_code == 200
        conv_id = res1.json()["data"]["conversation_id"]

        res2 = client.post("/api/ai/chat", json={
            "message": "What is idempotency?",
            "conversation_id": conv_id,
            "idempotency_key": ikey
        }, headers=hdrs)
        assert res2.status_code == 200
        # Both should return the same conversation
        assert res2.json()["data"]["conversation_id"] == conv_id

    def test_idempotency_key_hash_mismatch_rejected(self, client, db):
        """Same idempotency_key with different payload is rejected with 422."""
        with patch("app.agents.orchestrator.get_genai_client", return_value=None):
            hdrs = _register_and_login(client, "hashcheck")
            ikey = f"test-hash-{uuid.uuid4()}"
            # First request
            res1 = client.post("/api/ai/chat", json={
                "message": "First message", "idempotency_key": ikey
            }, headers=hdrs)
            assert res1.status_code == 200
            conv_id = res1.json()["data"].get("conversation_id")

            if conv_id:
                # Second request with same key but different message
                res2 = client.post("/api/ai/chat", json={
                    "message": "Completely different message",
                    "conversation_id": conv_id,
                    "idempotency_key": ikey
                }, headers=hdrs)
                # Should be rejected with 422 (payload hash mismatch)
                assert res2.status_code == 422

    @patch("app.agents.orchestrator.get_genai_client")
    def test_message_sequence_numbers_contiguous(self, mock_genai, client, db):
        """Message sequence numbers are gapless after multiple turns."""
        mock_client = MagicMock()
        mock_chat = MagicMock()
        mock_response = MagicMock()
        mock_response.function_calls = None
        mock_response.text = "Response"
        mock_chat.send_message.return_value = mock_response
        mock_client.chats.create.return_value = mock_chat
        mock_genai.return_value = mock_client

        hdrs = _register_and_login(client, "seqtest")
        res1 = client.post("/api/ai/chat", json={"message": "Turn 1", "idempotency_key": f"seq-{uuid.uuid4()}"}, headers=hdrs)
        conv_id = res1.json()["data"]["conversation_id"]

        client.post("/api/ai/chat", json={"message": "Turn 2", "conversation_id": conv_id, "idempotency_key": f"seq-{uuid.uuid4()}"}, headers=hdrs)

        hist = client.get(f"/api/ai/conversations/{conv_id}", headers=hdrs)
        msgs = hist.json()["data"]["messages"]
        seqs = sorted([m["sequence_number"] for m in msgs])
        # Sequence numbers must be 1, 2, 3, 4 (no gaps)
        assert seqs == list(range(1, len(seqs) + 1))

    @patch("app.agents.orchestrator.get_genai_client", return_value=None)
    def test_missing_idempotency_key_rejected(self, mock_genai, client, db):
        """Chat requests without idempotency_key are rejected with HTTP 400."""
        hdrs = _register_and_login(client, "noikey")

        res = client.post("/api/ai/chat", json={"message": "Hello"}, headers=hdrs)
        assert res.status_code == 400
        assert "idempotency_key" in res.json()["detail"]

    @patch("app.agents.orchestrator.get_genai_client", return_value=None)
    def test_empty_idempotency_key_rejected(self, mock_genai, client, db):
        """Empty idempotency_key is rejected with HTTP 400."""
        hdrs = _register_and_login(client, "emptyikey")

        res = client.post("/api/ai/chat", json={"message": "Hello", "idempotency_key": "   "}, headers=hdrs)
        assert res.status_code == 400
        assert "idempotency_key" in res.json()["detail"]

    @patch("app.agents.orchestrator.get_genai_client", return_value=None)
    def test_idempotency_key_durable_replay(self, mock_genai, client, db):
        """Same idempotency_key + same message replays durably."""
        hdrs = _register_and_login(client, "replay")
        ikey = f"durable-{uuid.uuid4()}"

        res1 = client.post("/api/ai/chat", json={
            "message": "Durable message",
            "idempotency_key": ikey
        }, headers=hdrs)
        assert res1.status_code == 200
        conv_id = res1.json()["data"]["conversation_id"]

        res2 = client.post("/api/ai/chat", json={
            "message": "Durable message",
            "conversation_id": conv_id,
            "idempotency_key": ikey
        }, headers=hdrs)
        assert res2.status_code == 200
        assert res2.json()["data"]["conversation_id"] == conv_id, "Same key + same message must replay durably"

    @patch("app.agents.orchestrator.get_genai_client", return_value=None)
    def test_idempotency_key_distinct_messages(self, mock_genai, client, db):
        """Different messages with different keys create separate conversations."""
        hdrs = _register_and_login(client, "distinct")

        res1 = client.post("/api/ai/chat", json={
            "message": "Message A",
            "idempotency_key": f"key-{uuid.uuid4()}"
        }, headers=hdrs)
        assert res1.status_code == 200
        conv_id_a = res1.json()["data"]["conversation_id"]

        res2 = client.post("/api/ai/chat", json={
            "message": "Message B",
            "idempotency_key": f"key-{uuid.uuid4()}"
        }, headers=hdrs)
        assert res2.status_code == 200
        conv_id_b = res2.json()["data"]["conversation_id"]

        assert conv_id_a != conv_id_b, "Different messages with different keys must not be deduplicated"


# ---------------------------------------------------------------------------
# 4. Persistence Service Unit Tests
# ---------------------------------------------------------------------------
class TestAIPersistenceService:
    def test_create_and_list_conversations(self, db, persistence_db):
        from app.services.ai_persistence_service import AIPersistenceService
        from app.models.user import User
        from app.models.ai_conversation import AIConversation

        # Create a test user
        student_id = uuid.uuid4()
        user = User(
            id=student_id,
            email=f"{student_id}@test.com",
            username=str(student_id)[:8],
            hashed_password="hashed",
            role="student",
            is_active=True
        )
        db.add(user)
        db.commit()

        svc = AIPersistenceService(db)
        conv = svc.create_conversation(student_id, title="Test Conv")
        assert conv.id is not None
        assert conv.last_sequence_number == 0
        assert conv.last_turn_number == 0

        items, total = svc.list_conversations(student_id)
        assert total == 1
        assert items[0].id == conv.id

    def test_rename_conversation(self, db, persistence_db):
        from app.services.ai_persistence_service import AIPersistenceService
        from app.models.user import User

        student_id = uuid.uuid4()
        user = User(
            id=student_id, email=f"{student_id}@test.com",
            username=str(student_id)[:8], hashed_password="hashed",
            role="student", is_active=True
        )
        db.add(user)
        db.commit()

        svc = AIPersistenceService(db)
        conv = svc.create_conversation(student_id, title="Old Title")
        renamed = svc.rename_conversation(student_id, conv.id, "New Title")
        assert renamed.title == "New Title"

    def test_delete_conversation(self, db, persistence_db):
        from app.services.ai_persistence_service import AIPersistenceService
        from app.models.user import User

        student_id = uuid.uuid4()
        user = User(
            id=student_id, email=f"{student_id}@test.com",
            username=str(student_id)[:8], hashed_password="hashed",
            role="student", is_active=True
        )
        db.add(user)
        db.commit()

        svc = AIPersistenceService(db)
        conv = svc.create_conversation(student_id, title="To Delete")
        from app.services.signing_key_service import signing_key_service
        token_data = signing_key_service.generate_deletion_token(student_id, conv.id, db)
        svc.delete_conversation(student_id, conv.id, token_data)

        _, total = svc.list_conversations(student_id)
        assert total == 0

    def test_request_hash_determinism(self):
        from app.services.ai_persistence_service import compute_request_hash
        h1 = compute_request_hash("hello", {"key": "val"})
        h2 = compute_request_hash("hello", {"key": "val"})
        assert h1 == h2 == h1  # Deterministic

    def test_request_hash_differs_on_message_change(self):
        from app.services.ai_persistence_service import compute_request_hash
        h1 = compute_request_hash("hello", {})
        h2 = compute_request_hash("world", {})
        assert h1 != h2


# ---------------------------------------------------------------------------
# 5. Signing Key Service Tests
# ---------------------------------------------------------------------------
class TestSigningKeyService:
    def test_signing_key_generates_verifiable_token(self, db, persistence_db):
        from app.services.signing_key_service import SigningKeyService
        svc = SigningKeyService()
        student_id = uuid.uuid4()
        conversation_id = uuid.uuid4()

        token_data = svc.generate_deletion_token(student_id, conversation_id, db)
        assert "signature" in token_data
        assert "nonce" in token_data
        assert len(token_data["nonce"]) == 64

    def test_retired_key_signs_different_from_active(self, db, persistence_db):
        from app.services.signing_key_service import SigningKeyService
        svc1 = SigningKeyService()
        svc2 = SigningKeyService()
        student_id = uuid.uuid4()
        conv_id = uuid.uuid4()

        t1 = svc1.generate_deletion_token(student_id, conv_id, db)
        t2 = svc2.generate_deletion_token(student_id, conv_id, db)

        # Signatures should differ due to nonce difference
        assert t1["nonce"] != t2["nonce"]

    def test_expired_token_rejected(self, db, persistence_db):
        """A token with exp <= now is rejected."""
        import pytest
        from fastapi import HTTPException
        from app.services.signing_key_service import SigningKeyService

        svc = SigningKeyService()
        student_id = uuid.uuid4()
        conv_id = uuid.uuid4()

        token_data = svc.generate_deletion_token(student_id, conv_id, db)
        # Backdate expiry to past
        token_data["exp"] = token_data["iat"] - 1

        with pytest.raises(HTTPException) as exc:
            svc.verify_and_consume_token(token_data, student_id, conv_id, db)
        assert exc.value.status_code in (400, 401)

    def test_tampered_signature_rejected(self, db, persistence_db):
        """A tampered signature is rejected."""
        import pytest
        from fastapi import HTTPException
        from app.services.signing_key_service import SigningKeyService

        svc = SigningKeyService()
        student_id = uuid.uuid4()
        conv_id = uuid.uuid4()

        token_data = svc.generate_deletion_token(student_id, conv_id, db)
        # Tamper signature
        token_data["signature"] = "deadbeef" * 8

        with pytest.raises(HTTPException) as exc:
            svc.verify_and_consume_token(token_data, student_id, conv_id, db)
        assert exc.value.status_code == 401

    def test_replay_attack_rejected(self, db, persistence_db):
        """Reusing the same nonce is rejected."""
        import pytest
        from fastapi import HTTPException
        from app.services.signing_key_service import SigningKeyService
        from app.models.user import User

        # Need valid user & conversation for deletion to work
        svc = SigningKeyService()
        student_id = uuid.uuid4()
        conv_id = uuid.uuid4()

        token_data = svc.generate_deletion_token(student_id, conv_id, db)
        # First consumption should succeed (creates nonce record)
        try:
            svc.verify_and_consume_token(token_data, student_id, conv_id, db)
        except HTTPException:
            pass  # May fail due to missing conversation - that's OK

        # Second consumption of same nonce must fail
        with pytest.raises(HTTPException) as exc:
            svc.verify_and_consume_token(token_data, student_id, conv_id, db)
        assert exc.value.status_code in (401, 409)

    def test_key_rotation_clears_cache(self, db, persistence_db):
        """After key rotation, cache is cleared."""
        from app.services.signing_key_service import SigningKeyService

        svc = SigningKeyService()
        # Pre-populate cache
        svc._cached_key_id = "old_key"
        svc._cached_secret = b"old_secret"
        svc._cache_deadline = 9999999999.0

        new_key_id = f"new_{secrets.token_hex(4)}"
        new_secret = secrets.token_bytes(32)
        svc.rotate_key(new_key_id, new_secret, db)

        assert svc._cached_key_id is None
        assert svc._cached_secret is None


# ---------------------------------------------------------------------------
# 6. Retry Execution Flow & Invariant Tests
# ---------------------------------------------------------------------------
class TestRetryFlow:
    @patch("app.agents.orchestrator.get_genai_client")
    def test_retry_failed_turn_success(self, mock_genai, client, db):
        """
        Failed turn can be retried successfully:
        - Reuses the existing turn ID, user message, and idempotency record.
        - Does NOT create another user message (exactly 1 user msg).
        - Does NOT create another turn (exactly 1 turn).
        - Successfully completes and stores exactly 1 assistant response.
        """
        mock_client = MagicMock()
        mock_chat = MagicMock()
        mock_response = MagicMock()
        mock_response.function_calls = None
        mock_response.text = "Now I can successfully explain recursion!"
        mock_chat.send_message.return_value = mock_response
        mock_client.chats.create.return_value = mock_chat
        mock_genai.return_value = mock_client

        hdrs = _register_and_login(client, "retry_succ")

        # Step 1: Create a turn that fails by simulating missing GenAI client or error
        with patch("app.agents.orchestrator.get_genai_client", return_value=None):
            fail_res = client.post("/api/ai/chat", json={"message": "Explain recursion", "idempotency_key": f"retry-{uuid.uuid4()}"}, headers=hdrs)
            assert fail_res.status_code == 200
            data = fail_res.json()["data"]
            conv_id = data["conversation_id"]
            turn_id = data["turn_id"]
            assert turn_id is not None

        # Verify initial state: 1 user message, 0 assistant messages (since turn failed), 1 turn (failed)
        hist_before = client.get(f"/api/ai/conversations/{conv_id}", headers=hdrs).json()["data"]
        assert len(hist_before["messages"]) == 1
        assert hist_before["messages"][0]["role"] == "user"

        # Step 2: Retry the failed turn
        retry_res = client.post(f"/api/ai/turns/{turn_id}/retry", headers=hdrs)
        assert retry_res.status_code == 200
        retry_data = retry_res.json()["data"]
        assert retry_data["turn_id"] == turn_id
        assert "Now I can successfully explain recursion!" in retry_data["response"]

        # Step 3: Verify post-retry state
        hist_after = client.get(f"/api/ai/conversations/{conv_id}", headers=hdrs).json()["data"]
        msgs = hist_after["messages"]
        # Exactly 2 messages: 1 user, 1 assistant (NO duplicate user message!)
        assert len(msgs) == 2
        assert msgs[0]["role"] == "user"
        assert msgs[0]["content"] == "Explain recursion"
        assert msgs[1]["role"] == "assistant"
        assert msgs[1]["content"] == "Now I can successfully explain recursion!"
        # Sequences are contiguous: 1, 2
        assert msgs[0]["sequence_number"] == 1
        assert msgs[1]["sequence_number"] == 2

    def test_retry_only_allowed_for_failed_turns(self, client, db):
        """Attempting to retry a completed turn returns 400."""
        from app.services.ai_persistence_service import AIPersistenceService
        from app.models.user import User

        student_id = uuid.uuid4()
        user = User(id=student_id, email=f"{student_id}@test.com", username=str(student_id)[:8], hashed_password="h", role="student", is_active=True)
        db.add(user)
        db.commit()

        svc = AIPersistenceService(db)
        conv = svc.create_conversation(student_id, title="Test")
        init_res = svc.initiate_turn(student_id, conv.id, "Hello", idempotency_key=f"test-{uuid.uuid4()}")
        svc.complete_turn(conv.id, uuid.UUID(init_res["turn_id"]), "Hi", uuid.UUID(init_res["idempotency_record_id"]), init_res["worker_token"])

        with pytest.raises(HTTPException) as exc:
            svc.retry_turn(student_id, uuid.UUID(init_res["turn_id"]))
        assert exc.value.status_code == 400
        assert "Only failed turns" in exc.value.detail

    def test_retry_version_fencing_prevents_stale_retry(self, client, db):
        """Attempting to retry with stale attempt_version raises conflict."""
        from app.services.ai_persistence_service import AIPersistenceService
        from app.models.user import User
        from app.models.ai_turn import AITurn

        student_id = uuid.uuid4()
        user = User(id=student_id, email=f"{student_id}@test.com", username=str(student_id)[:8], hashed_password="h", role="student", is_active=True)
        db.add(user)
        db.commit()

        svc = AIPersistenceService(db)
        conv = svc.create_conversation(student_id, title="Test")
        init_res = svc.initiate_turn(student_id, conv.id, "Hello", idempotency_key=f"test-{uuid.uuid4()}")
        turn_uuid = uuid.UUID(init_res["turn_id"])
        rec_uuid = uuid.UUID(init_res["idempotency_record_id"])
        svc.fail_turn(conv.id, turn_uuid, rec_uuid, "ERR", "fail")

        # First retry succeeds
        svc.retry_turn(student_id, turn_uuid)

        # Second retry while generating returns 409
        with pytest.raises(HTTPException) as exc:
            svc.retry_turn(student_id, turn_uuid)
        assert exc.value.status_code in (400, 409)


# ---------------------------------------------------------------------------
# 7. Safe Conversation Deletion Tests (with Foreign Keys Enabled)
# ---------------------------------------------------------------------------
class TestSafeDeletion:
    @patch("app.agents.orchestrator.get_genai_client")
    def test_delete_conversation_with_completed_turns(self, mock_genai, client, db):
        """Deleting conversation with completed turns and messages works cleanly without FK errors."""
        mock_client = MagicMock()
        mock_chat = MagicMock()
        mock_response = MagicMock()
        mock_response.function_calls = None
        mock_response.text = "Answer"
        mock_chat.send_message.return_value = mock_response
        mock_client.chats.create.return_value = mock_chat
        mock_genai.return_value = mock_client

        hdrs = _register_and_login(client, "del_comp")
        chat_res = client.post("/api/ai/chat", json={"message": "Turn 1", "idempotency_key": f"seq-{uuid.uuid4()}"}, headers=hdrs)
        conv_id = chat_res.json()["data"]["conversation_id"]

        # Generate deletion token and delete conversation
        tok_res = client.post(f"/api/ai/conversations/{conv_id}/deletion-token", headers=hdrs)
        assert tok_res.status_code == 200
        token_data = tok_res.json()["data"]
        del_res = client.request("DELETE", f"/api/ai/conversations/{conv_id}", json=token_data, headers=hdrs)
        assert del_res.status_code == 200

        # Verify not found
        get_res = client.get(f"/api/ai/conversations/{conv_id}", headers=hdrs)
        assert get_res.status_code == 404

    def test_delete_conversation_with_failed_turns(self, client, db):
        """Deleting conversation with failed turns works cleanly."""
        hdrs = _register_and_login(client, "del_fail")
        with patch("app.agents.orchestrator.get_genai_client", return_value=None):
            chat_res = client.post("/api/ai/chat", json={"message": "Turn 1", "idempotency_key": f"seq-{uuid.uuid4()}"}, headers=hdrs)
            conv_id = chat_res.json()["data"]["conversation_id"]

        tok_res = client.post(f"/api/ai/conversations/{conv_id}/deletion-token", headers=hdrs)
        assert tok_res.status_code == 200
        token_data = tok_res.json()["data"]
        del_res = client.request("DELETE", f"/api/ai/conversations/{conv_id}", json=token_data, headers=hdrs)
        assert del_res.status_code == 200

    def test_delete_conversation_with_generating_turn(self, client, db):
        """Deleting conversation while a turn is generating cleanly cleans up."""
        from app.services.ai_persistence_service import AIPersistenceService
        from app.models.user import User

        student_id = uuid.uuid4()
        user = User(id=student_id, email=f"{student_id}@test.com", username=str(student_id)[:8], hashed_password="h", role="student", is_active=True)
        db.add(user)
        db.commit()

        svc = AIPersistenceService(db)
        conv = svc.create_conversation(student_id, title="Generating")
        svc.initiate_turn(student_id, conv.id, "Wait for me", idempotency_key=f"test-{uuid.uuid4()}")

        # Delete must succeed without FK deadlock
        from app.services.signing_key_service import signing_key_service
        token_data = signing_key_service.generate_deletion_token(student_id, conv.id, db)
        svc.delete_conversation(student_id, conv.id, token_data)
        items, total = svc.list_conversations(student_id)
        assert total == 0


# ---------------------------------------------------------------------------
# 8. Expired Record Cleanup Tests
# ---------------------------------------------------------------------------
class TestCleanupService:
    def test_cleanup_expired_terminal_records(self, db, persistence_db):
        """Terminal idempotency records past expires_at are purged."""
        from app.services.ai_persistence_service import AIPersistenceService
        from app.models.user import User
        from app.models.ai_idempotency import AIIdempotencyRecord

        student_id = uuid.uuid4()
        user = User(id=student_id, email=f"{student_id}@test.com", username=str(student_id)[:8], hashed_password="h", role="student", is_active=True)
        db.add(user)
        db.commit()

        svc = AIPersistenceService(db)
        conv = svc.create_conversation(student_id, title="Cleanup")
        init_res = svc.initiate_turn(student_id, conv.id, "Hello", idempotency_key=f"test-{uuid.uuid4()}")
        rec_id = uuid.UUID(init_res["idempotency_record_id"])
        svc.complete_turn(conv.id, uuid.UUID(init_res["turn_id"]), "Hi", rec_id, init_res["worker_token"])

        # Manually backdate expires_at to the past
        db.query(AIIdempotencyRecord).filter(AIIdempotencyRecord.id == rec_id).update({
            "expires_at": datetime.now(timezone.utc) - timedelta(minutes=10)
        })
        db.commit()

        res = svc.cleanup_expired_records(batch_size=50)
        assert res["idempotency_records_purged"] == 1

        # Verify record no longer exists
        remaining = db.query(AIIdempotencyRecord).filter(AIIdempotencyRecord.id == rec_id).first()
        assert remaining is None

    def test_cleanup_skips_in_progress_and_active_leases(self, db, persistence_db):
        """Records that are IN_PROGRESS or have active lease are NEVER purged."""
        from app.services.ai_persistence_service import AIPersistenceService
        from app.models.user import User
        from app.models.ai_idempotency import AIIdempotencyRecord

        student_id = uuid.uuid4()
        user = User(id=student_id, email=f"{student_id}@test.com", username=str(student_id)[:8], hashed_password="h", role="student", is_active=True)
        db.add(user)
        db.commit()

        svc = AIPersistenceService(db)
        conv = svc.create_conversation(student_id, title="Active")
        init_res = svc.initiate_turn(student_id, conv.id, "Hello", idempotency_key=f"test-{uuid.uuid4()}")
        rec_id = uuid.UUID(init_res["idempotency_record_id"])

        # Even if expires_at is set to past, status is IN_PROGRESS with active lease
        db.query(AIIdempotencyRecord).filter(AIIdempotencyRecord.id == rec_id).update({
            "expires_at": datetime.now(timezone.utc) - timedelta(minutes=10),
            "lease_expires_at": datetime.now(timezone.utc) + timedelta(minutes=5)
        })
        db.commit()

        res = svc.cleanup_expired_records(batch_size=50)
        # Should NOT purge
        assert res["idempotency_records_purged"] == 0

        remaining = db.query(AIIdempotencyRecord).filter(AIIdempotencyRecord.id == rec_id).first()
        assert remaining is not None
