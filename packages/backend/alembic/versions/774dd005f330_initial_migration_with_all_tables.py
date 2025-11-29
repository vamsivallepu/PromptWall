"""Initial migration with all tables

Revision ID: 774dd005f330
Revises: 
Create Date: 2025-11-20 10:08:24.234768

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSON


# revision identifiers, used by Alembic.
revision: str = '774dd005f330'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('username', sa.String(255), nullable=False, unique=True),
        sa.Column('email', sa.String(255), nullable=False, unique=True),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('full_name', sa.String(255)),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('is_admin', sa.Boolean(), default=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('last_login', sa.DateTime()),
    )
    op.create_index('ix_users_username', 'users', ['username'])
    op.create_index('ix_users_email', 'users', ['email'])

    # Create devices table
    op.create_table(
        'devices',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('device_id', sa.String(255), nullable=False, unique=True),
        sa.Column('user_id', sa.String(255), nullable=False),
        sa.Column('device_type', sa.String(50), nullable=False),
        sa.Column('registered_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('last_seen', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('is_active', sa.Boolean(), default=True),
    )
    op.create_index('ix_devices_device_id', 'devices', ['device_id'])
    op.create_index('ix_devices_user_id', 'devices', ['user_id'])

    # Create firewall_configs table
    op.create_table(
        'firewall_configs',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', sa.String(255), nullable=False, unique=True),
        sa.Column('monitored_tools', JSON, nullable=False),
        sa.Column('sensitivity_thresholds', JSON, nullable=False),
        sa.Column('custom_patterns', JSON, nullable=False),
        sa.Column('log_retention_days', sa.Integer(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('updated_by', sa.String(255), nullable=False),
    )
    op.create_index('ix_firewall_configs_organization_id', 'firewall_configs', ['organization_id'])

    # Create log_entries table
    op.create_table(
        'log_entries',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('device_id', sa.String(255), nullable=False),
        sa.Column('user_id', sa.String(255), nullable=False),
        sa.Column('tool_name', sa.String(100), nullable=False),
        sa.Column('tool_type', sa.String(20), nullable=False),
        sa.Column('risk_level', sa.String(10), nullable=False),
        sa.Column('prompt_length', sa.Integer(), nullable=False),
        sa.Column('detected_entity_types', JSON, nullable=False),
        sa.Column('entity_count', sa.Integer(), nullable=False),
        sa.Column('was_sanitized', sa.Boolean(), nullable=False),
        sa.Column('log_metadata', JSON, nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )
    
    # Create indexes for log_entries
    op.create_index('ix_log_entries_timestamp', 'log_entries', ['timestamp'])
    op.create_index('ix_log_entries_device_id', 'log_entries', ['device_id'])
    op.create_index('ix_log_entries_user_id', 'log_entries', ['user_id'])
    op.create_index('ix_log_entries_tool_name', 'log_entries', ['tool_name'])
    op.create_index('ix_log_entries_risk_level', 'log_entries', ['risk_level'])
    
    # Create composite indexes for common queries
    op.create_index('idx_timestamp_risk', 'log_entries', ['timestamp', 'risk_level'])
    op.create_index('idx_user_timestamp', 'log_entries', ['user_id', 'timestamp'])
    op.create_index('idx_tool_timestamp', 'log_entries', ['tool_name', 'timestamp'])


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('log_entries')
    op.drop_table('firewall_configs')
    op.drop_table('devices')
    op.drop_table('users')
