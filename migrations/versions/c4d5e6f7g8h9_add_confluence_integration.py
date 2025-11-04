"""Add Confluence integration fields

Revision ID: c4d5e6f7g8h9
Revises: a1b2c3d4e5f6
Create Date: 2025-11-03 19:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c4d5e6f7g8h9'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade():
    # Add Confluence integration columns to user table
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('confluence_email', sa.String(length=120), nullable=True))
        batch_op.add_column(sa.Column('confluence_api_token_encrypted', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('confluence_url', sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column('confluence_default_space', sa.String(length=100), nullable=True))

    # Add Confluence tracking columns to transcription table
    with op.batch_alter_table('transcription', schema=None) as batch_op:
        batch_op.add_column(sa.Column('confluence_page_id', sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column('confluence_page_url', sa.String(length=500), nullable=True))
        batch_op.add_column(sa.Column('confluence_published_at', sa.DateTime(), nullable=True))


def downgrade():
    # Remove Confluence tracking columns from transcription table
    with op.batch_alter_table('transcription', schema=None) as batch_op:
        batch_op.drop_column('confluence_published_at')
        batch_op.drop_column('confluence_page_url')
        batch_op.drop_column('confluence_page_id')

    # Remove Confluence integration columns from user table
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_column('confluence_default_space')
        batch_op.drop_column('confluence_url')
        batch_op.drop_column('confluence_api_token_encrypted')
        batch_op.drop_column('confluence_email')
