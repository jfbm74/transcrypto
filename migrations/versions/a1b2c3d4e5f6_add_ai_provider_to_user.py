"""Add ai_provider to User

Revision ID: a1b2c3d4e5f6
Revises: 713f61e89967
Create Date: 2025-11-03 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = '713f61e89967'
branch_labels = None
depends_on = None


def upgrade():
    # Add ai_provider column to user table
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('ai_provider', sa.String(length=20), nullable=True))

    # Set default value for existing users
    op.execute("UPDATE user SET ai_provider = 'openai' WHERE ai_provider IS NULL")


def downgrade():
    # Remove ai_provider column from user table
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_column('ai_provider')
