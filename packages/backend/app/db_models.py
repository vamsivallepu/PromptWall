"""SQLAlchemy database models"""
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, Boolean, Float, JSON, Index, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.types import TypeDecorator, CHAR
from app.database import Base
import uuid


class GUID(TypeDecorator):
    """Platform-independent GUID type.
    Uses PostgreSQL's UUID type, otherwise uses CHAR(36), storing as stringified hex values.
    """
    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(UUID(as_uuid=True))
        else:
            return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return value
        else:
            if isinstance(value, uuid.UUID):
                return str(value)
            else:
                return str(uuid.UUID(value))

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        else:
            if isinstance(value, uuid.UUID):
                return value
            else:
                return uuid.UUID(value)


class LogEntryDB(Base):
    """Database model for log entries"""
    __tablename__ = "log_entries"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    timestamp = Column(DateTime, nullable=False, index=True)
    device_id = Column(String(255), nullable=False, index=True)
    user_id = Column(String(255), nullable=False, index=True)
    tool_name = Column(String(100), nullable=False, index=True)
    tool_type = Column(String(20), nullable=False)
    risk_level = Column(String(10), nullable=False, index=True)
    prompt_length = Column(Integer, nullable=False)
    detected_entity_types = Column(JSON, nullable=False)
    entity_count = Column(Integer, nullable=False)
    was_sanitized = Column(Boolean, nullable=False)
    log_metadata = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Composite indexes for common queries
    __table_args__ = (
        Index('idx_timestamp_risk', 'timestamp', 'risk_level'),
        Index('idx_user_timestamp', 'user_id', 'timestamp'),
        Index('idx_tool_timestamp', 'tool_name', 'timestamp'),
    )


class FirewallConfigDB(Base):
    """Database model for firewall configuration"""
    __tablename__ = "firewall_configs"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    organization_id = Column(String(255), nullable=False, unique=True, index=True)
    monitored_tools = Column(JSON, nullable=False)
    sensitivity_thresholds = Column(JSON, nullable=False)
    custom_patterns = Column(JSON, nullable=False)
    log_retention_days = Column(Integer, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(String(255), nullable=False)


class DeviceDB(Base):
    """Database model for registered devices"""
    __tablename__ = "devices"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    device_id = Column(String(255), nullable=False, unique=True, index=True)
    user_id = Column(String(255), nullable=False, index=True)
    device_type = Column(String(50), nullable=False)
    registered_at = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)


class UserDB(Base):
    """Database model for users"""
    __tablename__ = "users"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    username = Column(String(255), nullable=False, unique=True, index=True)
    email = Column(String(255), nullable=False, unique=True, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)
