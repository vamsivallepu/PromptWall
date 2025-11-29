"""Tests for log retention policy"""
import pytest
from datetime import datetime, timedelta
import uuid

from app.retention import cleanup_old_logs, cleanup_all_organizations
from app.db_models import LogEntryDB, FirewallConfigDB


@pytest.mark.asyncio
async def test_cleanup_old_logs_with_config(db_session):
    """Test that logs older than retention period are deleted"""
    # Create a firewall config with 30 days retention
    config = FirewallConfigDB(
        id=uuid.uuid4(),
        organization_id="test_org",
        monitored_tools=[],
        sensitivity_thresholds={},
        custom_patterns=[],
        log_retention_days=30,
        updated_by="test_user"
    )
    db_session.add(config)
    await db_session.commit()
    
    # Create logs with different ages
    now = datetime.utcnow()
    
    # Old log (40 days old - should be deleted)
    old_log = LogEntryDB(
        id=uuid.uuid4(),
        timestamp=now - timedelta(days=40),
        device_id="device1",
        user_id="user1",
        tool_name="ChatGPT",
        tool_type="web",
        risk_level="green",
        prompt_length=100,
        detected_entity_types=[],
        entity_count=0,
        was_sanitized=False,
        log_metadata={"agent_version": "1.0.0"}
    )
    
    # Recent log (20 days old - should be kept)
    recent_log = LogEntryDB(
        id=uuid.uuid4(),
        timestamp=now - timedelta(days=20),
        device_id="device1",
        user_id="user1",
        tool_name="ChatGPT",
        tool_type="web",
        risk_level="amber",
        prompt_length=200,
        detected_entity_types=["email"],
        entity_count=1,
        was_sanitized=True,
        log_metadata={"agent_version": "1.0.0"}
    )
    
    # Very recent log (5 days old - should be kept)
    very_recent_log = LogEntryDB(
        id=uuid.uuid4(),
        timestamp=now - timedelta(days=5),
        device_id="device1",
        user_id="user1",
        tool_name="Claude",
        tool_type="web",
        risk_level="red",
        prompt_length=300,
        detected_entity_types=["email", "phone"],
        entity_count=2,
        was_sanitized=True,
        log_metadata={"agent_version": "1.0.0"}
    )
    
    db_session.add_all([old_log, recent_log, very_recent_log])
    await db_session.commit()
    
    # Run cleanup
    deleted_count = await cleanup_old_logs(db_session, "test_org")
    
    # Should have deleted 1 log
    assert deleted_count == 1
    
    # Verify the old log was deleted and recent logs remain
    from sqlalchemy import select
    result = await db_session.execute(select(LogEntryDB))
    remaining_logs = result.scalars().all()
    
    assert len(remaining_logs) == 2
    remaining_ids = {log.id for log in remaining_logs}
    assert old_log.id not in remaining_ids
    assert recent_log.id in remaining_ids
    assert very_recent_log.id in remaining_ids


@pytest.mark.asyncio
async def test_cleanup_with_default_retention(db_session):
    """Test cleanup uses default 90 days when no config exists"""
    now = datetime.utcnow()
    
    # Create a log 100 days old (should be deleted with default 90 days)
    old_log = LogEntryDB(
        id=uuid.uuid4(),
        timestamp=now - timedelta(days=100),
        device_id="device1",
        user_id="user1",
        tool_name="ChatGPT",
        tool_type="web",
        risk_level="green",
        prompt_length=100,
        detected_entity_types=[],
        entity_count=0,
        was_sanitized=False,
        log_metadata={"agent_version": "1.0.0"}
    )
    
    # Create a log 80 days old (should be kept with default 90 days)
    recent_log = LogEntryDB(
        id=uuid.uuid4(),
        timestamp=now - timedelta(days=80),
        device_id="device1",
        user_id="user1",
        tool_name="ChatGPT",
        tool_type="web",
        risk_level="green",
        prompt_length=100,
        detected_entity_types=[],
        entity_count=0,
        was_sanitized=False,
        log_metadata={"agent_version": "1.0.0"}
    )
    
    db_session.add_all([old_log, recent_log])
    await db_session.commit()
    
    # Run cleanup without config (should use default 90 days)
    deleted_count = await cleanup_old_logs(db_session, "nonexistent_org")
    
    # Should have deleted 1 log
    assert deleted_count == 1
    
    # Verify only the recent log remains
    from sqlalchemy import select
    result = await db_session.execute(select(LogEntryDB))
    remaining_logs = result.scalars().all()
    
    assert len(remaining_logs) == 1
    assert remaining_logs[0].id == recent_log.id


@pytest.mark.asyncio
async def test_cleanup_all_organizations(db_session):
    """Test cleanup for multiple organizations (Safe Mode: Max Retention)"""
    # Create configs for two organizations
    config1 = FirewallConfigDB(
        id=uuid.uuid4(),
        organization_id="org1",
        monitored_tools=[],
        sensitivity_thresholds={},
        custom_patterns=[],
        log_retention_days=30,
        updated_by="test_user"
    )
    
    config2 = FirewallConfigDB(
        id=uuid.uuid4(),
        organization_id="org2",
        monitored_tools=[],
        sensitivity_thresholds={},
        custom_patterns=[],
        log_retention_days=60,
        updated_by="test_user"
    )
    
    db_session.add_all([config1, config2])
    await db_session.commit()
    
    now = datetime.utcnow()
    
    # Create logs
    # Org1: 40 days old (would be deleted if separated, but kept due to max retention of 60 days)
    old_log_org1 = LogEntryDB(
        id=uuid.uuid4(),
        timestamp=now - timedelta(days=40),
        device_id="device1",
        user_id="user1",
        tool_name="ChatGPT",
        tool_type="web",
        risk_level="green",
        prompt_length=100,
        detected_entity_types=[],
        entity_count=0,
        was_sanitized=False,
        log_metadata={"agent_version": "1.0.0"}
    )
    
    # Org2: 50 days old (kept)
    log_org2 = LogEntryDB(
        id=uuid.uuid4(),
        timestamp=now - timedelta(days=50),
        device_id="device2",
        user_id="user2",
        tool_name="Claude",
        tool_type="web",
        risk_level="green",
        prompt_length=100,
        detected_entity_types=[],
        entity_count=0,
        was_sanitized=False,
        log_metadata={"agent_version": "1.0.0"}
    )

    # Very old log: 100 days old (deleted because > 60)
    very_old_log = LogEntryDB(
        id=uuid.uuid4(),
        timestamp=now - timedelta(days=100),
        device_id="device3",
        user_id="user3",
        tool_name="ChatGPT",
        tool_type="web",
        risk_level="green",
        prompt_length=100,
        detected_entity_types=[],
        entity_count=0,
        was_sanitized=False,
        log_metadata={"agent_version": "1.0.0"}
    )
    
    db_session.add_all([old_log_org1, log_org2, very_old_log])
    await db_session.commit()
    
    # Run cleanup for all organizations
    deletion_counts = await cleanup_all_organizations(db_session)
    
    # Should have deleted 1 log total (the 100 day old one)
    assert sum(deletion_counts.values()) == 1
    
    # Verify logs
    from sqlalchemy import select
    result = await db_session.execute(select(LogEntryDB))
    remaining_logs = result.scalars().all()
    
    assert len(remaining_logs) == 2
    remaining_ids = {log.id for log in remaining_logs}
    assert very_old_log.id not in remaining_ids
    assert old_log_org1.id in remaining_ids
    assert log_org2.id in remaining_ids


@pytest.mark.asyncio
async def test_cleanup_no_logs_to_delete(db_session):
    """Test cleanup when all logs are within retention period"""
    # Create a config
    config = FirewallConfigDB(
        id=uuid.uuid4(),
        organization_id="test_org",
        monitored_tools=[],
        sensitivity_thresholds={},
        custom_patterns=[],
        log_retention_days=30,
        updated_by="test_user"
    )
    db_session.add(config)
    await db_session.commit()
    
    # Create only recent logs
    now = datetime.utcnow()
    recent_log = LogEntryDB(
        id=uuid.uuid4(),
        timestamp=now - timedelta(days=10),
        device_id="device1",
        user_id="user1",
        tool_name="ChatGPT",
        tool_type="web",
        risk_level="green",
        prompt_length=100,
        detected_entity_types=[],
        entity_count=0,
        was_sanitized=False,
        log_metadata={"agent_version": "1.0.0"}
    )
    
    db_session.add(recent_log)
    await db_session.commit()
    
    # Run cleanup
    deleted_count = await cleanup_old_logs(db_session, "test_org")
    
    # Should have deleted 0 logs
    assert deleted_count == 0
    
    # Verify log still exists
    from sqlalchemy import select
    result = await db_session.execute(select(LogEntryDB))
    remaining_logs = result.scalars().all()
    
    assert len(remaining_logs) == 1
    assert remaining_logs[0].id == recent_log.id
