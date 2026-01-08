"""add building parameters to projects

Revision ID: add_building_params
Revises: 7e989366bc74
Create Date: 2025-12-06

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_building_params'
down_revision = '7e989366bc74'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add building parameter columns to projects table."""
    op.add_column('projects', sa.Column('building_coverage', sa.DECIMAL(precision=5, scale=2), nullable=True))
    op.add_column('projects', sa.Column('floor_area_ratio', sa.DECIMAL(precision=5, scale=2), nullable=True))
    op.add_column('projects', sa.Column('num_floors', sa.Integer(), nullable=True))
    op.add_column('projects', sa.Column('building_height', sa.DECIMAL(precision=8, scale=2), nullable=True))
    op.add_column('projects', sa.Column('open_space_percentage', sa.DECIMAL(precision=5, scale=2), nullable=True))
    op.add_column('projects', sa.Column('parking_spaces', sa.Integer(), nullable=True))
    op.add_column('projects', sa.Column('owner_name', sa.String(length=255), nullable=True))


def downgrade() -> None:
    """Remove building parameter columns from projects table."""
    op.drop_column('projects', 'owner_name')
    op.drop_column('projects', 'parking_spaces')
    op.drop_column('projects', 'open_space_percentage')
    op.drop_column('projects', 'building_height')
    op.drop_column('projects', 'num_floors')
    op.drop_column('projects', 'floor_area_ratio')
    op.drop_column('projects', 'building_coverage')
