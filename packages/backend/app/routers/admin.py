"""Admin endpoints for maintenance tasks"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.database import get_db
from app.retention import cleanup_old_logs, cleanup_all_organizations

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


class CleanupResponse(BaseModel):
    """Response for cleanup operations"""
    deleted_count: int
    message: str


class CleanupAllResponse(BaseModel):
    """Response for cleanup all organizations"""
    deletion_counts: dict[str, int]
    total_deleted: int
    message: str


@router.post("/cleanup-logs", response_model=CleanupResponse)
async def trigger_log_cleanup(
    organization_id: str = "default",
    db: AsyncSession = Depends(get_db)
):
    """
    Manually trigger log retention cleanup for a specific organization.
    
    This endpoint deletes logs older than the configured retention period
    for the specified organization.
    
    Args:
        organization_id: Organization ID to clean up logs for (default: "default")
        db: Database session
        
    Returns:
        Number of logs deleted and status message
    """
    try:
        deleted_count = await cleanup_old_logs(db, organization_id)
        return CleanupResponse(
            deleted_count=deleted_count,
            message=f"Successfully deleted {deleted_count} old logs for organization {organization_id}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during cleanup: {str(e)}")


@router.post("/cleanup-logs/all", response_model=CleanupAllResponse)
async def trigger_all_cleanup(db: AsyncSession = Depends(get_db)):
    """
    Manually trigger log retention cleanup for all organizations.
    
    This endpoint deletes logs older than the configured retention period
    for all organizations based on their individual retention policies.
    
    Args:
        db: Database session
        
    Returns:
        Deletion counts per organization and total deleted
    """
    try:
        deletion_counts = await cleanup_all_organizations(db)
        total_deleted = sum(deletion_counts.values())
        
        return CleanupAllResponse(
            deletion_counts=deletion_counts,
            total_deleted=total_deleted,
            message=f"Successfully deleted {total_deleted} old logs across all organizations"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during cleanup: {str(e)}")
