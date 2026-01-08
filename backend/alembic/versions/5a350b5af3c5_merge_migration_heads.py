"""Merge migration heads

Revision ID: 5a350b5af3c5
Revises: add_building_params, add_model_url
Create Date: 2025-12-12 13:10:45.651998

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5a350b5af3c5'
down_revision: Union[str, Sequence[str], None] = ('add_building_params', 'add_model_url')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
