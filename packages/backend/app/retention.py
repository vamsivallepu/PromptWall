"""Log retention policy implementation"""
from datetime import datetime, timedelta
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.db_models import LogEntryDB, FirewallConfigDB

logger = logging.getLogger(__name__)


async def cleanup_old_logs(session: AsyncSession, organization_id: str = "default") -> int:
    """
    Delete logs older than the configured retention period.
    WARNING: Currently deletes GLOBAL logs based on the policy, as logs 
    do not have organization_id. Use with caution in multi-tenant setups.
    
    Args:
        session: Database session
        organization_id: Organization ID to get retention policy for
        
    Returns:
        Number of logs deleted
    """
    try:
        # Get the retention policy for the organization
        result = await session.execute(
            select(FirewallConfigDB).where(
                FirewallConfigDB.organization_id == organization_id
            )
        )
        config = result.scalar_one_or_none()
        
        if not config:
            logger.warning(f"No configuration found for organization {organization_id}, using default 90 days")
            retention_days = 90
        else:
            retention_days = config.log_retention_days
        
        # Calculate the cutoff date
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
        
        # Delete logs older than the cutoff date
        result = await session.execute(
            delete(LogEntryDB).where(LogEntryDB.timestamp < cutoff_date)
        )
        
        deleted_count = result.rowcount
        await session.commit()
        
        logger.info(f"Deleted {deleted_count} logs older than {retention_days} days (cutoff: {cutoff_date})")
        return deleted_count
        
    except Exception as e:
        logger.error(f"Error cleaning up old logs: {e}")
        await session.rollback()
        raise


async def cleanup_all_organizations(session: AsyncSession) -> dict[str, int]:
    """
    Clean up logs for all organizations based on their retention policies.
    Note: Currently applies the MAXIMUM retention period found across all policies
    to all logs, as logs are not yet partitioned by organization.
    
    Args:
        session: Database session
        
    Returns:
        Dictionary mapping organization_id to number of logs deleted (simulated)
    """
    try:
        # Get all organization configurations
        result = await session.execute(select(FirewallConfigDB))
        configs = result.scalars().all()
        
        # Default retention
        max_retention_days = 90
        
        if configs:
            # Find maximum retention days to be safe (prevent data loss for orgs with longer retention)
            max_retention_days = max(c.log_retention_days for c in configs)
        
        # Calculate the cutoff date
        cutoff_date = datetime.utcnow() - timedelta(days=max_retention_days)
        
        # Delete logs older than the cutoff date
        result = await session.execute(
            delete(LogEntryDB).where(LogEntryDB.timestamp < cutoff_date)
        )
        
        deleted_count = result.rowcount
        await session.commit()
        
        logger.info(f"Deleted {deleted_count} logs older than {max_retention_days} days (cutoff: {cutoff_date})")
        
        # Return single count mapped to 'global' since we can't attribute to orgs
        return {"global": deleted_count}
        
    except Exception as e:
        logger.error(f"Error cleaning up logs for all organizations: {e}")
        raise
