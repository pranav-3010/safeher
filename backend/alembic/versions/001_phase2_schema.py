"""Phase 2 Supabase PostgreSQL + PostGIS Schema Migration

Revision ID: 001_phase2_schema
Revises: 
Create Date: 2026-08-18

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from geoalchemy2 import Geography

revision: str = '001_phase2_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Enable PostGIS Extension
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis;")

    # 2. Table: data_sources
    op.create_table(
        'data_sources',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('organization', sa.String(length=255), nullable=True),
        sa.Column('source_type', sa.String(length=50), nullable=False),
        sa.Column('official_url', sa.Text(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('geographic_coverage', sa.String(length=255), nullable=True),
        sa.Column('license', sa.String(length=255), nullable=True),
        sa.Column('terms_of_use', sa.Text(), nullable=True),
        sa.Column('access_method', sa.String(length=100), nullable=True),
        sa.Column('update_frequency', sa.String(length=100), nullable=True),
        sa.Column('historical_start_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('historical_end_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('geographic_precision', sa.String(length=100), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('is_verified', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_data_sources_name', 'data_sources', ['name'])
    op.create_index('ix_data_sources_source_type', 'data_sources', ['source_type'])

    # 3. Table: source_fetches
    op.create_table(
        'source_fetches',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('data_source_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('records_fetched', sa.Integer(), server_default=sa.text('0'), nullable=False),
        sa.Column('records_inserted', sa.Integer(), server_default=sa.text('0'), nullable=False),
        sa.Column('records_updated', sa.Integer(), server_default=sa.text('0'), nullable=False),
        sa.Column('records_rejected', sa.Integer(), server_default=sa.text('0'), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('metadata_json', postgresql.JSONB(astext_metadata=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['data_source_id'], ['data_sources.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_source_fetches_status', 'source_fetches', ['status'])

    # 4. Table: crime_incidents
    op.create_table(
        'crime_incidents',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('external_source_id', sa.String(length=255), nullable=True),
        sa.Column('data_source_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('incident_type', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('reported_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('occurred_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('latitude', sa.Float(), nullable=True),
        sa.Column('longitude', sa.Float(), nullable=True),
        sa.Column('location', Geography(geometry_type='POINT', srid=4326), nullable=True),
        sa.Column('severity', sa.Float(), nullable=True),
        sa.Column('source_confidence', sa.Float(), nullable=True),
        sa.Column('verification_status', sa.String(length=50), server_default=sa.text("'UNVERIFIED'"), nullable=False),
        sa.Column('source_reference', sa.String(length=255), nullable=True),
        sa.Column('raw_data', postgresql.JSONB(astext_metadata=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint('latitude IS NULL OR (latitude >= -90 AND latitude <= 90)', name='check_valid_latitude'),
        sa.CheckConstraint('longitude IS NULL OR (longitude >= -180 AND longitude <= 180)', name='check_valid_longitude'),
        sa.CheckConstraint('severity IS NULL OR (severity >= 0.0 AND severity <= 1.0)', name='check_valid_severity'),

        sa.ForeignKeyConstraint(['data_source_id'], ['data_sources.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_crime_incidents_location', 'crime_incidents', ['location'], postgresql_using='gist')
    op.create_index('ix_crime_incidents_occurred_at', 'crime_incidents', ['occurred_at'])
    op.create_index('ix_crime_incidents_incident_type', 'crime_incidents', ['incident_type'])

    # 5. Table: news_articles
    op.create_table(
        'news_articles',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('data_source_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('external_article_id', sa.String(length=255), nullable=True),
        sa.Column('title', sa.Text(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('content_reference', sa.Text(), nullable=True),
        sa.Column('url', sa.Text(), nullable=True),
        sa.Column('publisher', sa.String(length=255), nullable=True),
        sa.Column('published_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('retrieved_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('language', sa.String(length=10), server_default=sa.text("'en'"), nullable=False),
        sa.Column('content_hash', sa.String(length=64), nullable=False),
        sa.Column('processing_status', sa.String(length=50), server_default=sa.text("'PENDING'"), nullable=False),
        sa.Column('llm_processed', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['data_source_id'], ['data_sources.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('content_hash')
    )

    # 6. Table: news_incidents
    op.create_table(
        'news_incidents',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('news_article_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('event_type', sa.String(length=100), nullable=False),
        sa.Column('location_text', sa.Text(), nullable=True),
        sa.Column('location', Geography(geometry_type='POINT', srid=4326), nullable=True),
        sa.Column('occurred_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('severity', sa.Float(), nullable=True),
        sa.Column('llm_confidence', sa.Float(), nullable=True),
        sa.Column('verification_status', sa.String(length=50), server_default=sa.text("'UNVERIFIED'"), nullable=False),
        sa.Column('extraction_metadata', postgresql.JSONB(astext_metadata=True), nullable=True),
        sa.Column('valid_from', sa.DateTime(timezone=True), nullable=True),
        sa.Column('valid_until', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['news_article_id'], ['news_articles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_news_incidents_location', 'news_incidents', ['location'], postgresql_using='gist')

    # 7. Table: community_reports
    op.create_table(
        'community_reports',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('user_reference', sa.String(length=255), nullable=True),
        sa.Column('report_type', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('location', Geography(geometry_type='POINT', srid=4326), nullable=False),
        sa.Column('reported_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('occurred_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('verification_status', sa.String(length=50), server_default=sa.text("'UNVERIFIED'"), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('review_status', sa.String(length=50), server_default=sa.text("'PENDING'"), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_community_reports_location', 'community_reports', ['location'], postgresql_using='gist')

    # 8. Table: osm_features
    op.create_table(
        'osm_features',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('osm_id', sa.String(length=255), nullable=True),
        sa.Column('feature_type', sa.String(length=100), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=True),
        sa.Column('category', sa.String(length=100), nullable=False),
        sa.Column('location', Geography(geometry_type='POINT', srid=4326), nullable=True),
        sa.Column('geometry', Geography(geometry_type='GEOMETRY', srid=4326), nullable=True),
        sa.Column('tags', postgresql.JSONB(astext_metadata=True), nullable=True),
        sa.Column('source', sa.String(length=100), nullable=True),
        sa.Column('retrieved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_osm_features_geometry', 'osm_features', ['geometry'], postgresql_using='gist')
    op.create_index('idx_osm_features_location', 'osm_features', ['location'], postgresql_using='gist')

    # 9. Table: road_segments
    op.create_table(
        'road_segments',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('osm_id', sa.String(length=255), nullable=True),
        sa.Column('road_name', sa.String(length=255), nullable=True),
        sa.Column('road_type', sa.String(length=100), nullable=True),
        sa.Column('geometry', Geography(geometry_type='LINESTRING', srid=4326), nullable=False),
        sa.Column('length_meters', sa.Float(), nullable=True),
        sa.Column('max_speed', sa.Integer(), nullable=True),
        sa.Column('oneway', sa.Boolean(), nullable=True),
        sa.Column('has_sidewalk', sa.Boolean(), nullable=True),
        sa.Column('is_dead_end', sa.Boolean(), nullable=True),
        sa.Column('intersection_density', sa.Float(), nullable=True),
        sa.Column('lighting_status', sa.String(length=50), nullable=True),
        sa.Column('commercial_activity_score', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_road_segments_geometry', 'road_segments', ['geometry'], postgresql_using='gist')
    op.create_index('ix_road_segments_road_type', 'road_segments', ['road_type'])
    op.create_index('ix_road_segments_road_name', 'road_segments', ['road_name'])

    # 10. Table: emergency_facilities
    op.create_table(
        'emergency_facilities',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('facility_type', sa.String(length=50), nullable=False),
        sa.Column('location', Geography(geometry_type='POINT', srid=4326), nullable=False),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('phone', sa.String(length=50), nullable=True),
        sa.Column('is_24_hours', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('source', sa.String(length=100), nullable=True),
        sa.Column('source_reference', sa.String(length=255), nullable=True),
        sa.Column('verification_status', sa.String(length=50), server_default=sa.text("'VERIFIED'"), nullable=False),
        sa.Column('last_verified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_emergency_facilities_location', 'emergency_facilities', ['location'], postgresql_using='gist')

    # 11. Table: environmental_features
    op.create_table(
        'environmental_features',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('road_segment_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('lighting_status', sa.String(length=50), nullable=True),
        sa.Column('lighting_source', sa.String(length=100), nullable=True),
        sa.Column('commercial_activity', sa.String(length=50), nullable=True),
        sa.Column('foot_traffic_indicator', sa.String(length=50), nullable=True),
        sa.Column('visibility_indicator', sa.String(length=50), nullable=True),
        sa.Column('road_width', sa.Float(), nullable=True),
        sa.Column('footpath_available', sa.Boolean(), nullable=True),
        sa.Column('surveillance_indicator', sa.String(length=50), nullable=True),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('source_reference', sa.String(length=255), nullable=True),
        sa.Column('observed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['road_segment_id'], ['road_segments.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # 12. Table: risk_events
    op.create_table(
        'risk_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('event_type', sa.String(length=100), nullable=False),
        sa.Column('source_type', sa.String(length=50), nullable=False),
        sa.Column('source_reference', sa.String(length=255), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('location', Geography(geometry_type='POINT', srid=4326), nullable=False),
        sa.Column('severity', sa.Float(), nullable=False),
        sa.Column('confidence', sa.Float(), server_default=sa.text('1.0'), nullable=False),
        sa.Column('verification_status', sa.String(length=50), server_default=sa.text("'UNVERIFIED'"), nullable=False),
        sa.Column('valid_from', sa.DateTime(timezone=True), nullable=False),
        sa.Column('valid_until', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint('severity >= 0.0 AND severity <= 1.0', name='check_valid_risk_event_severity'),
        sa.CheckConstraint('confidence >= 0.0 AND confidence <= 1.0', name='check_valid_risk_event_confidence'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_risk_events_location', 'risk_events', ['location'], postgresql_using='gist')

    # 13. Table: model_versions
    op.create_table(
        'model_versions',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('model_name', sa.String(length=100), nullable=False),
        sa.Column('version', sa.String(length=50), nullable=False),
        sa.Column('algorithm', sa.String(length=100), nullable=False),
        sa.Column('training_started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('training_completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('training_data_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('training_data_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('feature_list', postgresql.JSONB(astext_metadata=True), nullable=True),
        sa.Column('metrics', postgresql.JSONB(astext_metadata=True), nullable=True),
        sa.Column('artifact_uri', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=50), server_default=sa.text("'INACTIVE'"), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('version')
    )

    # 14. Table: risk_predictions
    op.create_table(
        'risk_predictions',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('road_segment_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('prediction_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('time_of_day', sa.Integer(), nullable=False),
        sa.Column('day_of_week', sa.Integer(), nullable=False),
        sa.Column('risk_score', sa.Float(), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('risk_level', sa.String(length=20), nullable=False),
        sa.Column('model_version_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('data_freshness', sa.String(length=50), nullable=True),
        sa.Column('feature_snapshot', postgresql.JSONB(astext_metadata=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint('risk_score >= 0.0 AND risk_score <= 1.0', name='check_valid_risk_score'),
        sa.CheckConstraint('confidence >= 0.0 AND confidence <= 1.0', name='check_valid_risk_confidence'),
        sa.ForeignKeyConstraint(['model_version_id'], ['model_versions.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['road_segment_id'], ['road_segments.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # 15. Table: model_predictions
    op.create_table(
        'model_predictions',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('model_version_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('road_segment_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('prediction_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('prediction', sa.Float(), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('features', postgresql.JSONB(astext_metadata=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['model_version_id'], ['model_versions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['road_segment_id'], ['road_segments.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # 16. Table: route_analyses
    op.create_table(
        'route_analyses',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('request_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('source_location', Geography(geometry_type='POINT', srid=4326), nullable=False),
        sa.Column('destination_location', Geography(geometry_type='POINT', srid=4326), nullable=False),
        sa.Column('requested_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('departure_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('route_provider', sa.String(length=50), nullable=False),
        sa.Column('route_count', sa.Integer(), server_default=sa.text('1'), nullable=False),
        sa.Column('selected_route', postgresql.JSONB(astext_metadata=True), nullable=True),
        sa.Column('safety_cost', sa.Float(), nullable=True),
        sa.Column('distance_meters', sa.Float(), nullable=True),
        sa.Column('duration_seconds', sa.Float(), nullable=True),
        sa.Column('average_risk', sa.Float(), nullable=True),
        sa.Column('maximum_risk', sa.Float(), nullable=True),
        sa.Column('high_risk_percentage', sa.Float(), nullable=True),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('metadata_json', postgresql.JSONB(astext_metadata=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_route_analyses_source_location', 'route_analyses', ['source_location'], postgresql_using='gist')
    op.create_index('idx_route_analyses_dest_location', 'route_analyses', ['destination_location'], postgresql_using='gist')

    # 17. Table: emergency_events
    op.create_table(
        'emergency_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('event_reference', sa.String(length=100), nullable=False),
        sa.Column('user_reference', sa.String(length=255), nullable=True),
        sa.Column('location', Geography(geometry_type='POINT', srid=4326), nullable=False),
        sa.Column('trigger_type', sa.String(length=50), nullable=False),
        sa.Column('triggered_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('status', sa.String(length=50), server_default=sa.text("'ACTIVE'"), nullable=False),
        sa.Column('notification_status', sa.String(length=50), server_default=sa.text("'PENDING'"), nullable=False),
        sa.Column('notification_provider', sa.String(length=50), nullable=True),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('metadata_json', postgresql.JSONB(astext_metadata=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('event_reference')
    )
    op.create_index('idx_emergency_events_location', 'emergency_events', ['location'], postgresql_using='gist')

    # 18. Table: system_logs
    op.create_table(
        'system_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('service', sa.String(length=100), nullable=False),
        sa.Column('level', sa.String(length=20), nullable=False),
        sa.Column('event_type', sa.String(length=100), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('source_reference', sa.String(length=255), nullable=True),
        sa.Column('metadata_json', postgresql.JSONB(astext_metadata=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('system_logs')
    op.drop_index('idx_emergency_events_location', table_name='emergency_events')
    op.drop_table('emergency_events')
    op.drop_index('idx_route_analyses_dest_location', table_name='route_analyses')
    op.drop_index('idx_route_analyses_source_location', table_name='route_analyses')
    op.drop_table('route_analyses')
    op.drop_table('model_predictions')
    op.drop_table('risk_predictions')
    op.drop_table('model_versions')
    op.drop_index('idx_risk_events_location', table_name='risk_events')
    op.drop_table('risk_events')
    op.drop_table('environmental_features')
    op.drop_index('idx_emergency_facilities_location', table_name='emergency_facilities')
    op.drop_table('emergency_facilities')
    op.drop_index('idx_road_segments_geometry', table_name='road_segments')
    op.drop_table('road_segments')
    op.drop_index('idx_osm_features_location', table_name='osm_features')
    op.drop_index('idx_osm_features_geometry', table_name='osm_features')
    op.drop_table('osm_features')
    op.drop_index('idx_community_reports_location', table_name='community_reports')
    op.drop_table('community_reports')
    op.drop_index('idx_news_incidents_location', table_name='news_incidents')
    op.drop_table('news_incidents')
    op.drop_table('news_articles')
    op.drop_index('idx_crime_incidents_location', table_name='crime_incidents')
    op.drop_table('crime_incidents')
    op.drop_table('source_fetches')
    op.drop_table('data_sources')
