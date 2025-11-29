"""Background scheduler for periodic tasks"""
import asyncio
import logging
from datetime import datetime

from app.database import AsyncSessionLocal
from app.retention import cleanup_all_organizations

logger = logging.getLogger(__name__)


async def run_retention_cleanup():
    """Run log retention cleanup task"""
    logger.info("Starting log retention cleanup task")
    
    async with AsyncSessionLocal() as session:
        try:
            deletion_counts = await cleanup_all_organizations(session)
            total_deleted = sum(deletion_counts.values())
            logger.info(f"Log retention cleanup completed. Total logs deleted: {total_deleted}")
            logger.info(f"Deletion breakdown: {deletion_counts}")
        except Exception as e:
            logger.error(f"Error during log retention cleanup: {e}")
            raise


async def schedule_retention_cleanup(interval_hours: int = 24):
    """
    Schedule periodic log retention cleanup.
    
    Args:
        interval_hours: How often to run cleanup (default: 24 hours)
    """
    logger.info(f"Starting retention cleanup scheduler (interval: {interval_hours} hours)")
    
    while True:
        try:
            await run_retention_cleanup()
        except Exception as e:
            logger.error(f"Retention cleanup failed: {e}")
        
        # Wait for the next interval
        await asyncio.sleep(interval_hours * 3600)


if __name__ == "__main__":
    # This can be run as a standalone script
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    asyncio.run(run_retention_cleanup())
