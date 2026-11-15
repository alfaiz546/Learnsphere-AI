"""AI Chat Session Persistence (Phase 2.5)

Revision ID: e71a93821f04
Revises: dffd6115ad87
Create Date: 2026-11-14 17:45:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'e71a93821f04'
down_revision = 'dffd6115ad87'
branch_labels = None
depends_on = None

def upgrade():
    # -------------------------------------------------------------------------
    # 1. Alter ai_conversations: add metadata, counters, and lock_version
    # -------------------------------------------------------------------------
    op.add_column('ai_conversations', sa.Column('title', sa.String(length=255), nullable=True))
    op.add_column('ai_conversations', sa.Column('last_sequence_number', sa.Integer(), server_default='0', nullable=False))
    op.add_column('ai_conversations', sa.Column('last_turn_number', sa.Integer(), server_default='0', nullable=False))
    op.add_column('ai_conversations', sa.Column('lock_version', sa.Integer(), server_default='1', nullable=False))

    # -------------------------------------------------------------------------
    # 2. Alter ai_messages: add sequence_number and turn_id
    # -------------------------------------------------------------------------
    op.add_column('ai_messages', sa.Column('sequence_number', sa.Integer(), server_default='1', nullable=False))
    op.add_column('ai_messages', sa.Column('turn_id', sa.UUID(), nullable=True))

    # -------------------------------------------------------------------------
    # 3. Create ai_turns table
    # -------------------------------------------------------------------------
    op.create_table(
        'ai_turns',
        sa.Column('id', sa.UUID(), primary_key=True),
        sa.Column('conversation_id', sa.UUID(), sa.ForeignKey('ai_conversations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('turn_number', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=32), server_default='generating', nullable=False),
        sa.Column('user_message_id', sa.UUID(), sa.ForeignKey('ai_messages.id', ondelete='RESTRICT', deferrable=True, initially='DEFERRED'), nullable=False),
        sa.Column('assistant_message_id', sa.UUID(), sa.ForeignKey('ai_messages.id', ondelete='SET NULL'), nullable=True),
        sa.Column('idempotency_record_id', sa.UUID(), nullable=True),
        sa.Column('attempt_version', sa.Integer(), server_default='1', nullable=False),
        sa.Column('error_code', sa.String(length=64), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.clock_timestamp(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.clock_timestamp(), nullable=False),
        sa.UniqueConstraint('conversation_id', 'turn_number', name='uq_ai_turns_conv_turn')
    )
    op.create_index('ix_ai_turns_conversation_id', 'ai_turns', ['conversation_id'])

    # Partial unique index enforcing single generating turn per conversation.
    # Uses raw SQL so it works on both PostgreSQL and SQLite (both support
    # partial indexes via WHERE clause). The SQLAlchemy op.create_index with
    # postgresql_where is ignored by SQLite, which would silently create a
    # non-partial unique index and break the concurrency invariant.
    op.execute(
        sa.text("""
        CREATE UNIQUE INDEX IF NOT EXISTS uq_ai_turns_single_generating
        ON ai_turns (conversation_id)
        WHERE status = 'generating'
        """)
    )

    # -------------------------------------------------------------------------
    # 4. Create ai_idempotency_records table
    # -------------------------------------------------------------------------
    op.create_table(
        'ai_idempotency_records',
        sa.Column('id', sa.UUID(), primary_key=True),
        sa.Column('conversation_id', sa.UUID(), sa.ForeignKey('ai_conversations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('student_id', sa.UUID(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('turn_id', sa.UUID(), nullable=True),
        sa.Column('idempotency_key', sa.String(length=128), nullable=False),
        sa.Column('request_hash', sa.String(length=64), nullable=False),
        sa.Column('status', sa.String(length=32), server_default='IN_PROGRESS', nullable=False),
        sa.Column('owner_token', sa.String(length=64), nullable=True),
        sa.Column('lease_expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('attempt_version', sa.Integer(), server_default='1', nullable=False),
        sa.Column('response_body', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('error_code', sa.String(length=64), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.clock_timestamp(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.clock_timestamp(), nullable=False),
        sa.UniqueConstraint('student_id', 'idempotency_key', name='uq_ai_idempotency_student_key')
    )
    op.create_index('ix_ai_idempotency_lease', 'ai_idempotency_records', ['status', 'lease_expires_at'])

    # -------------------------------------------------------------------------
    # 5. Add Deferrable Circular Foreign Keys
    # -------------------------------------------------------------------------
    op.create_foreign_key(
        'fk_turn_idempotency',
        'ai_turns',
        'ai_idempotency_records',
        ['idempotency_record_id'],
        ['id'],
        ondelete='SET NULL',
        deferrable=True,
        initially='DEFERRED'
    )

    op.create_foreign_key(
        'fk_idempotency_turn',
        'ai_idempotency_records',
        'ai_turns',
        ['turn_id'],
        ['id'],
        ondelete='SET NULL',
        deferrable=True,
        initially='DEFERRED'
    )

    op.create_foreign_key(
        'fk_message_turn',
        'ai_messages',
        'ai_turns',
        ['turn_id'],
        ['id'],
        ondelete='SET NULL'
    )

    # -------------------------------------------------------------------------
    # 6. Backfill Historical Messages with Contiguous Sequences
    # -------------------------------------------------------------------------
    op.execute("""
        DO $$
        DECLARE
            r RECORD;
            v_seq INT;
        BEGIN
            FOR r IN (SELECT DISTINCT conversation_id FROM ai_messages) LOOP
                v_seq := 0;
                FOR r IN (
                    SELECT id FROM ai_messages
                    WHERE conversation_id = r.conversation_id
                    ORDER BY created_at ASC, id ASC
                ) LOOP
                    v_seq := v_seq + 1;
                    UPDATE ai_messages SET sequence_number = v_seq WHERE id = r.id;
                END LOOP;
                UPDATE ai_conversations SET last_sequence_number = v_seq WHERE id = r.conversation_id;
            END LOOP;
        END $$;
    """)

    # Attach Unique Constraint on (conversation_id, sequence_number)
    op.create_unique_constraint(
        'uq_ai_messages_conv_seq',
        'ai_messages',
        ['conversation_id', 'sequence_number']
    )

    # -------------------------------------------------------------------------
    # 7. Create auth_security schema, tables, views, and least-privilege roles
    # -------------------------------------------------------------------------
    op.execute("""
        CREATE SCHEMA IF NOT EXISTS auth_security;

        CREATE TABLE IF NOT EXISTS auth_security.signing_keys (
            key_id VARCHAR(32) PRIMARY KEY,
            key_secret BYTEA NOT NULL,
            algorithm VARCHAR(16) NOT NULL DEFAULT 'sha256',
            status VARCHAR(16) NOT NULL CHECK (status IN ('ACTIVE', 'RETIRED', 'REVOKED')),
            created_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
            signing_expires_at TIMESTAMPTZ NOT NULL,
            verification_expires_at TIMESTAMPTZ NOT NULL
        );

        CREATE UNIQUE INDEX IF NOT EXISTS uq_signing_keys_single_active
        ON auth_security.signing_keys (status)
        WHERE status = 'ACTIVE';

        CREATE TABLE IF NOT EXISTS auth_security.used_nonces (
            nonce VARCHAR(64) PRIMARY KEY,
            consumed_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
            expires_at TIMESTAMPTZ NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_used_nonces_expires_at ON auth_security.used_nonces (expires_at);

        CREATE OR REPLACE VIEW auth_security.active_signing_key AS
        SELECT key_id, algorithm, signing_expires_at
        FROM auth_security.signing_keys
        WHERE status = 'ACTIVE' AND signing_expires_at > clock_timestamp();

        -- Dedicated least-privilege non-login security role
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'auth_security_role') THEN
                CREATE ROLE auth_security_role NOLOGIN;
            END IF;
        END $$;

        -- Revoke default public exposure
        REVOKE ALL ON SCHEMA auth_security FROM PUBLIC;
        REVOKE ALL ON ALL TABLES IN SCHEMA auth_security FROM PUBLIC;
        REVOKE ALL ON auth_security.active_signing_key FROM PUBLIC;

        -- Grant controlled, exact privileges to dedicated role
        GRANT USAGE ON SCHEMA auth_security TO auth_security_role;
        GRANT SELECT, INSERT, UPDATE ON auth_security.signing_keys TO auth_security_role;
        GRANT SELECT, INSERT, DELETE ON auth_security.used_nonces TO auth_security_role;
        GRANT SELECT ON auth_security.active_signing_key TO auth_security_role;

        -- Controlled security-definer helper with hardened search_path
        CREATE OR REPLACE FUNCTION auth_security.consume_nonce(p_nonce VARCHAR(64), p_expires_at TIMESTAMPTZ)
        RETURNS BOOLEAN
        LANGUAGE plpgsql
        SECURITY DEFINER
        SET search_path = pg_catalog, auth_security
        AS $fn$
        BEGIN
            INSERT INTO auth_security.used_nonces (nonce, consumed_at, expires_at)
            VALUES (p_nonce, clock_timestamp(), p_expires_at);
            RETURN TRUE;
        EXCEPTION WHEN unique_violation THEN
            RETURN FALSE;
        END;
        $fn$;

        REVOKE ALL ON FUNCTION auth_security.consume_nonce(VARCHAR, TIMESTAMPTZ) FROM PUBLIC;
        GRANT EXECUTE ON FUNCTION auth_security.consume_nonce(VARCHAR, TIMESTAMPTZ) TO auth_security_role;
    """)


def downgrade():
    op.execute("""
        DROP FUNCTION IF EXISTS auth_security.consume_nonce(VARCHAR, TIMESTAMPTZ);
        DROP VIEW IF EXISTS auth_security.active_signing_key;
        DROP TABLE IF EXISTS auth_security.used_nonces;
        DROP TABLE IF EXISTS auth_security.signing_keys;
        DROP SCHEMA IF EXISTS auth_security CASCADE;
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'auth_security_role') THEN
                DROP ROLE auth_security_role;
            END IF;
        END $$;
    """)
    op.drop_constraint('uq_ai_messages_conv_seq', 'ai_messages', type_='unique')
    op.drop_constraint('fk_message_turn', 'ai_messages', type_='foreignkey')
    op.drop_constraint('fk_idempotency_turn', 'ai_idempotency_records', type_='foreignkey')
    op.drop_constraint('fk_turn_idempotency', 'ai_turns', type_='foreignkey')
    op.drop_table('ai_idempotency_records')
    op.drop_table('ai_turns')
    op.drop_column('ai_messages', 'turn_id')
    op.drop_column('ai_messages', 'sequence_number')
    op.drop_column('ai_conversations', 'lock_version')
    op.drop_column('ai_conversations', 'last_turn_number')
    op.drop_column('ai_conversations', 'last_sequence_number')
    op.drop_column('ai_conversations', 'title')
