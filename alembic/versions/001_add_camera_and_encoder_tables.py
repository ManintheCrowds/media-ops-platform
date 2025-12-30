"""Add camera and encoder tables

Revision ID: 001
Revises: 
Create Date: 2024-12-29 16:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Get database dialect
    bind = op.get_bind()
    dialect = bind.dialect.name
    
    # Create enum types for Arlo (PostgreSQL only)
    if dialect == 'postgresql':
        op.execute("CREATE TYPE arlostatus AS ENUM ('online', 'offline', 'unknown', 'battery_low', 'weak_signal')")
        op.execute("CREATE TYPE arloeventtype AS ENUM ('motion', 'audio', 'battery_low', 'offline', 'online', 'recording_started', 'recording_completed', 'snapshot_captured')")
        
        # Create enum types for Encoder
        op.execute("CREATE TYPE encoderstatus AS ENUM ('online', 'offline', 'unknown', 'error', 'recording', 'streaming')")
        op.execute("CREATE TYPE encoderdevicetype AS ENUM ('aja_helo', 'generic')")
    
    # Create arlo_base_stations table
    op.create_table(
        'arlo_base_stations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(64), nullable=False),
        sa.Column('serial_number', sa.String(64), nullable=False),
        sa.Column('ip_address', sa.String(15)),
        sa.Column('status', sa.Enum('online', 'offline', 'unknown', 'battery_low', 'weak_signal', name='arlostatus', create_type=dialect != 'sqlite'), server_default='unknown'),
        sa.Column('last_sync', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('credentials_encrypted', sa.String(512)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('serial_number')
    )
    op.create_index(op.f('ix_arlo_base_stations_serial_number'), 'arlo_base_stations', ['serial_number'], unique=True)
    
    # Create arlo_cameras table
    op.create_table(
        'arlo_cameras',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('base_station_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(64), nullable=False),
        sa.Column('device_id', sa.String(64), nullable=False),
        sa.Column('device_type', sa.String(32)),
        sa.Column('status', sa.Enum('online', 'offline', 'unknown', 'battery_low', 'weak_signal', name='arlostatus', create_type=dialect != 'sqlite'), server_default='unknown'),
        sa.Column('is_armed', sa.Boolean(), server_default='false'),
        sa.Column('battery_level', sa.Integer()),
        sa.Column('signal_strength', sa.Integer()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(['base_station_id'], ['arlo_base_stations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('device_id')
    )
    op.create_index('idx_arlo_camera_base_station', 'arlo_cameras', ['base_station_id'])
    op.create_index(op.f('ix_arlo_cameras_device_id'), 'arlo_cameras', ['device_id'], unique=True)
    op.create_index('idx_arlo_camera_status', 'arlo_cameras', ['status'])
    
    # Create arlo_recordings table
    op.create_table(
        'arlo_recordings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('camera_id', sa.Integer(), nullable=False),
        sa.Column('recording_id', sa.String(128), nullable=False),
        sa.Column('presigned_url', sa.String(512)),
        sa.Column('created_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('duration', sa.Integer()),
        sa.Column('file_size', sa.BigInteger()),
        sa.Column('downloaded', sa.Boolean(), server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(['camera_id'], ['arlo_cameras.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('recording_id')
    )
    op.create_index('idx_arlo_recording_camera', 'arlo_recordings', ['camera_id'])
    op.create_index(op.f('ix_arlo_recordings_recording_id'), 'arlo_recordings', ['recording_id'], unique=True)
    op.create_index('idx_arlo_recording_date', 'arlo_recordings', ['created_date'])
    
    # Create arlo_events table
    op.create_table(
        'arlo_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('camera_id', sa.Integer(), nullable=False),
        sa.Column('event_type', sa.Enum('motion', 'audio', 'battery_low', 'offline', 'online', 'recording_started', 'recording_completed', 'snapshot_captured', name='arloeventtype', create_type=dialect != 'sqlite'), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('details', postgresql.JSON),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(['camera_id'], ['arlo_cameras.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_arlo_event_camera', 'arlo_events', ['camera_id'])
    op.create_index('idx_arlo_event_type', 'arlo_events', ['event_type'])
    op.create_index('idx_arlo_event_timestamp', 'arlo_events', ['timestamp'])
    
    # Create video_encoders table
    op.create_table(
        'video_encoders',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(64), nullable=False),
        sa.Column('ip_address', sa.String(15), nullable=False),
        sa.Column('device_type', sa.Enum('aja_helo', 'generic', name='encoderdevicetype', create_type=dialect != 'sqlite'), server_default='aja_helo'),
        sa.Column('status', sa.Enum('online', 'offline', 'unknown', 'error', 'recording', 'streaming', name='encoderstatus', create_type=dialect != 'sqlite'), server_default='unknown'),
        sa.Column('is_recording', sa.Boolean(), server_default='false'),
        sa.Column('is_streaming', sa.Boolean(), server_default='false'),
        sa.Column('current_recording_path', sa.String(512)),
        sa.Column('current_stream_url', sa.String(512)),
        sa.Column('storage_available', sa.BigInteger()),
        sa.Column('storage_used', sa.BigInteger()),
        sa.Column('port', sa.Integer(), server_default='80'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('ip_address')
    )
    op.create_index(op.f('ix_video_encoders_ip_address'), 'video_encoders', ['ip_address'], unique=True)
    op.create_index('idx_encoder_status', 'video_encoders', ['status'])
    op.create_index('idx_encoder_device_type', 'video_encoders', ['device_type'])


def downgrade() -> None:
    # Get database dialect
    bind = op.get_bind()
    dialect = bind.dialect.name
    
    # Drop indexes
    op.drop_index('idx_encoder_device_type', 'video_encoders')
    op.drop_index('idx_encoder_status', 'video_encoders')
    op.drop_index(op.f('ix_video_encoders_ip_address'), 'video_encoders')
    op.drop_table('video_encoders')
    
    op.drop_index('idx_arlo_event_timestamp', 'arlo_events')
    op.drop_index('idx_arlo_event_type', 'arlo_events')
    op.drop_index('idx_arlo_event_camera', 'arlo_events')
    op.drop_table('arlo_events')
    
    op.drop_index('idx_arlo_recording_date', 'arlo_recordings')
    op.drop_index(op.f('ix_arlo_recordings_recording_id'), 'arlo_recordings')
    op.drop_index('idx_arlo_recording_camera', 'arlo_recordings')
    op.drop_table('arlo_recordings')
    
    op.drop_index('idx_arlo_camera_status', 'arlo_cameras')
    op.drop_index(op.f('ix_arlo_cameras_device_id'), 'arlo_cameras')
    op.drop_index('idx_arlo_camera_base_station', 'arlo_cameras')
    op.drop_table('arlo_cameras')
    
    op.drop_index(op.f('ix_arlo_base_stations_serial_number'), 'arlo_base_stations')
    op.drop_table('arlo_base_stations')
    
    # Drop enum types (PostgreSQL only)
    if dialect == 'postgresql':
        op.execute("DROP TYPE encoderdevicetype")
        op.execute("DROP TYPE encoderstatus")
        op.execute("DROP TYPE arloeventtype")
        op.execute("DROP TYPE arlostatus")

