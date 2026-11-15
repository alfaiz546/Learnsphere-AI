'''alembic revision --autogenerate -m "add streak and xp tables"'''

from alembic import op
import sqlalchemy as sa
import uuid

# revision identifiers, used by Alembic.
revision = 'f1c2b3d4e5f6'
# The previous head revision is e71a93821f04
down_revision = 'e71a93821f04'
branch_labels = None
depends_on = None


def upgrade():
    # Create streaks table
    op.create_table(
        'streaks',
        sa.Column('user_id', sa.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('current_streak', sa.Integer, nullable=False, server_default='0'),
        sa.Column('longest_streak', sa.Integer, nullable=False, server_default='0'),
        sa.Column('last_activity', sa.Date, nullable=True),
        sa.Column('timezone', sa.String(length=64), nullable=False, server_default='Asia/Kolkata'),
    )

    # Create xp_transactions table
    op.create_table(
        'xp_transactions',
        sa.Column('id', sa.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('user_id', sa.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('activity_type', sa.String(length=50), nullable=False),
        sa.Column('reference_id', sa.UUID(as_uuid=True), nullable=False),
        sa.Column('amount', sa.Integer, nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.UniqueConstraint('user_id', 'activity_type', 'reference_id', name='uq_xp_user_activity_ref')
    )


def downgrade():
    op.drop_table('xp_transactions')
    op.drop_table('streaks')
