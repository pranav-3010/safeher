"""Add crime_statistics and crime_geographic_areas tables

Revision ID: 002_add_crime_stats
Revises: 001_phase2_schema
Create Date: 2026-08-18

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from geoalchemy2 import Geography

revision: str = '002_add_crime_stats'
down_revision: Union[str, None] = '001_phase2_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Table: crime_statistics
    op.create_table(
        'crime_statistics',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('data_source_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('state', sa.String(length=100), nullable=False),
        sa.Column('district_or_city', sa.String(length=150), nullable=True),
        sa.Column('crime_type', sa.String(length=150), nullable=False),
        sa.Column('case_count', sa.Integer(), server_default=sa.text('0'), nullable=False),
        sa.Column('crime_rate', sa.Float(), nullable=True),
        sa.Column('source_reference', sa.String(length=255), nullable=True),
        sa.Column('raw_data', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['data_source_id'], ['data_sources.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_crime_statistics_year', 'crime_statistics', ['year'])
    op.create_index('ix_crime_statistics_state', 'crime_statistics', ['state'])
    op.create_index('ix_crime_statistics_district', 'crime_statistics', ['district_or_city'])
    op.create_index('ix_crime_statistics_crime_type', 'crime_statistics', ['crime_type'])

    # 2. Table: crime_geographic_areas
    op.create_table(
        'crime_geographic_areas',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('state', sa.String(length=100), nullable=True),
        sa.Column('district', sa.String(length=150), nullable=True),
        sa.Column('area_type', sa.String(length=100), server_default=sa.text("'POLICE_STATION_JURISDICTION'"), nullable=False),
        sa.Column('boundary', Geography(geometry_type='GEOMETRY', srid=4326), nullable=False),
        sa.Column('risk_index', sa.Float(), nullable=True),
        sa.Column('source_reference', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_crime_geographic_areas_boundary', 'crime_geographic_areas', ['boundary'], postgresql_using='gist')


def downgrade() -> None:
    op.drop_index('idx_crime_geographic_areas_boundary', table_name='crime_geographic_areas')
    op.drop_table('crime_geographic_areas')
    op.drop_table('crime_statistics')
