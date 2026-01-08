"""add model_url to projects

Revision ID: add_model_url
Revises: 
Create Date: 2025-12-08

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_model_url'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Add model_url column to projects table
    op.add_column('projects', sa.Column('model_url', sa.String(length=500), nullable=True))


def downgrade():
    # Remove model_url column from projects table
    op.drop_column('projects', 'model_url')
