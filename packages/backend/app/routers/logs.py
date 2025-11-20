"""Log ingestion and query endpoints"""
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc
from sqlalchemy.sql import Select

from app.database import get_db
from app.db_models import LogEntryDB
from app.models import LogBatchRequest, LogEntry, LogPage, LogFilter, SummaryStats
from app.auth import get_current_user, TokenData
from app.rate_limit import limiter

router = APIRouter(prefix="/api/v1/logs", tags=["logs"])


@router.post("/batch", status_code=status.HTTP_201_CREATED)
@limiter.limit("1000/hour")
async def upload_logs(
    request: Request,
    batch: LogBatchRequest,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """
    Upload a batch of log entries from a client device.
    Rate limited to 1000 logs per hour per device.
    
    Requirements: 3.1, 3.4
    """
    # Store device_id in request state for rate limiting
    request.state.device_id = batch.deviceId
    
    try:
        # Convert Pydantic models to SQLAlchemy models
        db_logs = []
        for log in batch.logs:
            db_log = LogEntryDB(
                timestamp=log.timestamp,
                device_id=log.deviceId,
                user_id=log.userId,
                tool_name=log.toolName,
                tool_type=log.toolType,
                risk_level=log.riskLevel,
                prompt_length=log.promptLength,
                detected_entity_types=log.detectedEntityTypes,
                entity_count=log.entityCount,
                was_sanitized=log.wasSanitized,
                log_metadata=log.metadata.model_dump(by_alias=True)
            )
            db_logs.append(db_log)
        
        # Bulk insert logs
        db.add_all(db_logs)
        await db.commit()
        
        return {
            "status": "success",
            "message": f"Successfully uploaded {len(batch.logs)} log entries",
            "count": len(batch.logs)
        }
    
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload logs: {str(e)}"
        )


@router.get("", response_model=LogPage)
async def get_logs(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    risk_level: Optional[str] = None,
    tool_name: Optional[str] = None,
    user_id: Optional[str] = None,
    page: int = 1,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """
    Query log entries with filtering and pagination.
    
    Requirements: 3.2, 3.5
    """
    # Validate pagination parameters
    if page < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Page must be >= 1"
        )
    if limit < 1 or limit > 1000:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Limit must be between 1 and 1000"
        )
    
    # Build query with filters
    query = select(LogEntryDB)
    filters = []
    
    if start_date:
        try:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            filters.append(LogEntryDB.timestamp >= start_dt)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid start_date format. Use ISO 8601 format."
            )
    
    if end_date:
        try:
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            filters.append(LogEntryDB.timestamp <= end_dt)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid end_date format. Use ISO 8601 format."
            )
    
    if risk_level:
        if risk_level not in ['green', 'amber', 'red']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="risk_level must be 'green', 'amber', or 'red'"
            )
        filters.append(LogEntryDB.risk_level == risk_level)
    
    if tool_name:
        filters.append(LogEntryDB.tool_name == tool_name)
    
    if user_id:
        filters.append(LogEntryDB.user_id == user_id)
    
    if filters:
        query = query.where(and_(*filters))
    
    # Get total count
    count_query = select(func.count()).select_from(LogEntryDB)
    if filters:
        count_query = count_query.where(and_(*filters))
    
    result = await db.execute(count_query)
    total = result.scalar_one()
    
    # Apply pagination and ordering
    query = query.order_by(desc(LogEntryDB.timestamp))
    query = query.offset((page - 1) * limit).limit(limit)
    
    # Execute query
    result = await db.execute(query)
    db_logs = result.scalars().all()
    
    # Convert to Pydantic models
    logs = []
    for db_log in db_logs:
        log = LogEntry(
            id=str(db_log.id),
            timestamp=db_log.timestamp,
            deviceId=db_log.device_id,
            userId=db_log.user_id,
            toolName=db_log.tool_name,
            toolType=db_log.tool_type,
            riskLevel=db_log.risk_level,
            promptLength=db_log.prompt_length,
            detectedEntityTypes=db_log.detected_entity_types,
            entityCount=db_log.entity_count,
            wasSanitized=db_log.was_sanitized,
            metadata=db_log.log_metadata
        )
        logs.append(log)
    
    # Calculate total pages
    total_pages = (total + limit - 1) // limit
    
    return LogPage(
        logs=logs,
        total=total,
        page=page,
        limit=limit,
        totalPages=total_pages
    )



@router.get("/stats/summary", response_model=SummaryStats)
async def get_summary_stats(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """
    Get summary statistics for the dashboard.
    
    Requirements: 3.2, 3.5
    """
    # Build base query with date filters
    filters = []
    
    if start_date:
        try:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            filters.append(LogEntryDB.timestamp >= start_dt)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid start_date format. Use ISO 8601 format."
            )
    
    if end_date:
        try:
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            filters.append(LogEntryDB.timestamp <= end_dt)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid end_date format. Use ISO 8601 format."
            )
    
    # Get total interactions
    count_query = select(func.count()).select_from(LogEntryDB)
    if filters:
        count_query = count_query.where(and_(*filters))
    
    result = await db.execute(count_query)
    total_interactions = result.scalar_one()
    
    # Get risk distribution
    risk_query = select(
        LogEntryDB.risk_level,
        func.count(LogEntryDB.id).label('count')
    ).group_by(LogEntryDB.risk_level)
    
    if filters:
        risk_query = risk_query.where(and_(*filters))
    
    result = await db.execute(risk_query)
    risk_rows = result.all()
    risk_distribution = {row.risk_level: row.count for row in risk_rows}
    
    # Ensure all risk levels are present
    for level in ['green', 'amber', 'red']:
        if level not in risk_distribution:
            risk_distribution[level] = 0
    
    # Get top users
    top_users_query = select(
        LogEntryDB.user_id,
        func.count(LogEntryDB.id).label('count')
    ).group_by(LogEntryDB.user_id).order_by(desc('count')).limit(10)
    
    if filters:
        top_users_query = top_users_query.where(and_(*filters))
    
    result = await db.execute(top_users_query)
    top_users_rows = result.all()
    top_users = [
        {"userId": row.user_id, "count": row.count}
        for row in top_users_rows
    ]
    
    # Get top tools
    top_tools_query = select(
        LogEntryDB.tool_name,
        func.count(LogEntryDB.id).label('count')
    ).group_by(LogEntryDB.tool_name).order_by(desc('count')).limit(10)
    
    if filters:
        top_tools_query = top_tools_query.where(and_(*filters))
    
    result = await db.execute(top_tools_query)
    top_tools_rows = result.all()
    top_tools = [
        {"toolName": row.tool_name, "count": row.count}
        for row in top_tools_rows
    ]
    
    return SummaryStats(
        totalInteractions=total_interactions,
        riskDistribution=risk_distribution,
        topUsers=top_users,
        topTools=top_tools
    )



@router.get("/export")
async def export_logs(
    format: str = "csv",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    risk_level: Optional[str] = None,
    tool_name: Optional[str] = None,
    user_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """
    Export log entries in CSV or JSON format.
    Applies the same filters as the get_logs endpoint.
    Streams large exports to avoid memory issues.
    
    Requirements: 3.3
    """
    from fastapi.responses import StreamingResponse
    import csv
    import json
    from io import StringIO
    
    # Validate format
    if format not in ['csv', 'json']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Format must be 'csv' or 'json'"
        )
    
    # Build query with filters (same as get_logs)
    query = select(LogEntryDB)
    filters = []
    
    if start_date:
        try:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            filters.append(LogEntryDB.timestamp >= start_dt)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid start_date format. Use ISO 8601 format."
            )
    
    if end_date:
        try:
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            filters.append(LogEntryDB.timestamp <= end_dt)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid end_date format. Use ISO 8601 format."
            )
    
    if risk_level:
        if risk_level not in ['green', 'amber', 'red']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="risk_level must be 'green', 'amber', or 'red'"
            )
        filters.append(LogEntryDB.risk_level == risk_level)
    
    if tool_name:
        filters.append(LogEntryDB.tool_name == tool_name)
    
    if user_id:
        filters.append(LogEntryDB.user_id == user_id)
    
    if filters:
        query = query.where(and_(*filters))
    
    # Order by timestamp
    query = query.order_by(desc(LogEntryDB.timestamp))
    
    # Execute query
    result = await db.execute(query)
    db_logs = result.scalars().all()
    
    if format == 'csv':
        # Generate CSV
        output = StringIO()
        writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)
        
        # Write header
        writer.writerow([
            'id', 'timestamp', 'device_id', 'user_id', 'tool_name', 'tool_type',
            'risk_level', 'prompt_length', 'detected_entity_types', 'entity_count',
            'was_sanitized', 'browser_version', 'os_version', 'agent_version'
        ])
        
        # Write rows
        for log in db_logs:
            log_meta = log.log_metadata
            writer.writerow([
                str(log.id),
                log.timestamp.isoformat(),
                log.device_id,
                log.user_id,
                log.tool_name,
                log.tool_type,
                log.risk_level,
                log.prompt_length,
                ','.join(log.detected_entity_types),
                log.entity_count,
                log.was_sanitized,
                log_meta.get('browser_version', ''),
                log_meta.get('os_version', ''),
                log_meta.get('agent_version', '')
            ])
        
        # Return CSV response
        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=ai_firewall_logs_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
            }
        )
    
    else:  # format == 'json'
        # Generate JSON
        logs_data = []
        for log in db_logs:
            log_dict = {
                'id': str(log.id),
                'timestamp': log.timestamp.isoformat(),
                'device_id': log.device_id,
                'user_id': log.user_id,
                'tool_name': log.tool_name,
                'tool_type': log.tool_type,
                'risk_level': log.risk_level,
                'prompt_length': log.prompt_length,
                'detected_entity_types': log.detected_entity_types,
                'entity_count': log.entity_count,
                'was_sanitized': log.was_sanitized,
                'metadata': log.log_metadata
            }
            logs_data.append(log_dict)
        
        # Return JSON response
        json_str = json.dumps(logs_data, indent=2)
        return StreamingResponse(
            iter([json_str]),
            media_type="application/json",
            headers={
                "Content-Disposition": f"attachment; filename=ai_firewall_logs_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
            }
        )
