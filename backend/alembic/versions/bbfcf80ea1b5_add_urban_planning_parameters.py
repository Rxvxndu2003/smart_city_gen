"""add_urban_planning_parameters

Revision ID: bbfcf80ea1b5
Revises: ed930398c5fe
Create Date: 2025-12-31 11:17:42.967412

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bbfcf80ea1b5'
down_revision: Union[str, Sequence[str], None] = 'ed930398c5fe'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - Add urban planning parameters to projects table."""
    # Zoning Distribution
    op.add_column('projects', sa.Column('residential_percentage', sa.DECIMAL(5, 2), server_default='60.0', nullable=True))
    op.add_column('projects', sa.Column('commercial_percentage', sa.DECIMAL(5, 2), server_default='20.0', nullable=True))
    op.add_column('projects', sa.Column('industrial_percentage', sa.DECIMAL(5, 2), server_default='10.0', nullable=True))
    op.add_column('projects', sa.Column('green_space_percentage_plan', sa.DECIMAL(5, 2), server_default='10.0', nullable=True))
    
    # Infrastructure
    op.add_column('projects', sa.Column('road_network_type', sa.String(50), server_default='GRID', nullable=True))
    op.add_column('projects', sa.Column('main_road_width', sa.DECIMAL(5, 2), server_default='12.0', nullable=True))
    op.add_column('projects', sa.Column('secondary_road_width', sa.DECIMAL(5, 2), server_default='8.0', nullable=True))
    op.add_column('projects', sa.Column('pedestrian_path_width', sa.DECIMAL(5, 2), server_default='2.0', nullable=True))
    
    # Demographics
    op.add_column('projects', sa.Column('target_population', sa.Integer, nullable=True))
    op.add_column('projects', sa.Column('population_density', sa.DECIMAL(8, 2), nullable=True))
    op.add_column('projects', sa.Column('average_household_size', sa.DECIMAL(4, 2), server_default='3.5', nullable=True))
    
    # Environmental
    op.add_column('projects', sa.Column('climate_zone', sa.String(50), server_default='TROPICAL', nullable=True))
    op.add_column('projects', sa.Column('sustainability_rating', sa.String(20), server_default='BRONZE', nullable=True))
    op.add_column('projects', sa.Column('renewable_energy_target', sa.DECIMAL(5, 2), server_default='0.0', nullable=True))
    op.add_column('projects', sa.Column('water_management_strategy', sa.String(255), nullable=True))


def downgrade() -> None:
    """Downgrade schema - Remove urban planning parameters from projects table."""
    # Remove columns in reverse order
    op.drop_column('projects', 'water_management_strategy')
    op.drop_column('projects', 'renewable_energy_target')
    op.drop_column('projects', 'sustainability_rating')
    op.drop_column('projects', 'climate_zone')
    op.drop_column('projects', 'average_household_size')
    op.drop_column('projects', 'population_density')
    op.drop_column('projects', 'target_population')
    op.drop_column('projects', 'pedestrian_path_width')
    op.drop_column('projects', 'secondary_road_width')
    op.drop_column('projects', 'main_road_width')
    op.drop_column('projects', 'road_network_type')
    op.drop_column('projects', 'green_space_percentage_plan')
    op.drop_column('projects', 'industrial_percentage')
    op.drop_column('projects', 'commercial_percentage')
    op.drop_column('projects', 'residential_percentage')
