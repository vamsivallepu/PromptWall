"""Configuration management endpoints"""
from datetime import datetime
import re
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.db_models import FirewallConfigDB
from app.models import FirewallConfig, SensitivityPattern
from app.auth import get_current_user, get_current_admin_user, TokenData

router = APIRouter(prefix="/api/v1/config", tags=["configuration"])


def validate_config(config: FirewallConfig) -> None:
    """
    Validate firewall configuration.
    
    Requirements: 6.1, 6.2, 6.3, 6.4, 6.5
    """
    # Validate log retention days (30-365)
    if config.logRetentionDays < 30 or config.logRetentionDays > 365:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Log retention days must be between 30 and 365"
        )
    
    # Validate sensitivity thresholds
    thresholds = config.sensitivityThresholds
    if thresholds.amberMinEntities < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Amber minimum entities must be >= 0"
        )
    
    if thresholds.redMinEntities < thresholds.amberMinEntities:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Red minimum entities must be >= amber minimum entities"
        )
    
    if thresholds.highConfidenceThreshold < 0 or thresholds.highConfidenceThreshold > 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="High confidence threshold must be between 0 and 1"
        )
    
    # Validate custom patterns (regex)
    for pattern in config.customPatterns:
        if pattern.enabled:
            try:
                re.compile(pattern.pattern)
            except re.error as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid regex pattern '{pattern.name}': {str(e)}"
                )
    
    # Validate monitored tools
    valid_tool_types = {'web', 'desktop', 'cli'}
    for tool in config.monitoredTools:
        if tool.toolType not in valid_tool_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid tool type '{tool.toolType}'. Must be one of: {valid_tool_types}"
            )


@router.get("", response_model=FirewallConfig, response_model_by_alias=False)
async def get_config(
    organization_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """
    Fetch firewall configuration for an organization.
    
    Requirements: 6.1, 6.2, 6.3, 6.4, 6.5
    """
    # Use default organization if not specified
    if organization_id is None:
        organization_id = "default"
    
    # Query configuration
    query = select(FirewallConfigDB).where(
        FirewallConfigDB.organization_id == organization_id
    )
    result = await db.execute(query)
    config_db = result.scalar_one_or_none()
    
    if config_db is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Configuration not found for organization '{organization_id}'"
        )
    
    # Convert to Pydantic model
    config = FirewallConfig(
        id=str(config_db.id),
        organizationId=config_db.organization_id,
        monitoredTools=config_db.monitored_tools,
        sensitivityThresholds=config_db.sensitivity_thresholds,
        customPatterns=config_db.custom_patterns,
        logRetentionDays=config_db.log_retention_days,
        updatedAt=config_db.updated_at,
        updatedBy=config_db.updated_by
    )
    
    return config


@router.put("", response_model=FirewallConfig, response_model_by_alias=False)
async def update_config(
    config: FirewallConfig,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_admin_user)
):
    """
    Update firewall configuration.
    Only admins can update configuration.
    
    Requirements: 6.1, 6.2, 6.3, 6.4, 6.5
    """
    # Validate configuration
    validate_config(config)
    
    # Query existing configuration
    query = select(FirewallConfigDB).where(
        FirewallConfigDB.organization_id == config.organizationId
    )
    result = await db.execute(query)
    config_db = result.scalar_one_or_none()
    
    if config_db is None:
        # Create new configuration
        config_db = FirewallConfigDB(
            organization_id=config.organizationId,
            monitored_tools=[tool.model_dump(by_alias=True) for tool in config.monitoredTools],
            sensitivity_thresholds=config.sensitivityThresholds.model_dump(by_alias=True),
            custom_patterns=[pattern.model_dump(by_alias=True) for pattern in config.customPatterns],
            log_retention_days=config.logRetentionDays,
            updated_by=current_user.username
        )
        db.add(config_db)
    else:
        # Update existing configuration
        config_db.monitored_tools = [tool.model_dump(by_alias=True) for tool in config.monitoredTools]
        config_db.sensitivity_thresholds = config.sensitivityThresholds.model_dump(by_alias=True)
        config_db.custom_patterns = [pattern.model_dump(by_alias=True) for pattern in config.customPatterns]
        config_db.log_retention_days = config.logRetentionDays
        config_db.updated_at = datetime.utcnow()
        config_db.updated_by = current_user.username
    
    await db.commit()
    await db.refresh(config_db)
    
    # Convert to Pydantic model
    updated_config = FirewallConfig(
        id=str(config_db.id),
        organizationId=config_db.organization_id,
        monitoredTools=config_db.monitored_tools,
        sensitivityThresholds=config_db.sensitivity_thresholds,
        customPatterns=config_db.custom_patterns,
        logRetentionDays=config_db.log_retention_days,
        updatedAt=config_db.updated_at,
        updatedBy=config_db.updated_by
    )
    
    return updated_config


@router.post("", response_model=FirewallConfig, status_code=status.HTTP_201_CREATED, response_model_by_alias=False)
async def create_config(
    config: FirewallConfig,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_admin_user)
):
    """
    Create a new firewall configuration.
    Only admins can create configuration.
    
    Requirements: 6.1, 6.2, 6.3, 6.4, 6.5
    """
    # Validate configuration
    validate_config(config)
    
    # Check if configuration already exists
    query = select(FirewallConfigDB).where(
        FirewallConfigDB.organization_id == config.organizationId
    )
    result = await db.execute(query)
    existing_config = result.scalar_one_or_none()
    
    if existing_config is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Configuration already exists for organization '{config.organizationId}'"
        )
    
    # Create new configuration
    config_db = FirewallConfigDB(
        organization_id=config.organizationId,
        monitored_tools=[tool.model_dump(by_alias=True) for tool in config.monitoredTools],
        sensitivity_thresholds=config.sensitivityThresholds.model_dump(by_alias=True),
        custom_patterns=[pattern.model_dump(by_alias=True) for pattern in config.customPatterns],
        log_retention_days=config.logRetentionDays,
        updated_by=current_user.username
    )
    db.add(config_db)
    await db.commit()
    await db.refresh(config_db)
    
    # Convert to Pydantic model
    created_config = FirewallConfig(
        id=str(config_db.id),
        organizationId=config_db.organization_id,
        monitoredTools=config_db.monitored_tools,
        sensitivityThresholds=config_db.sensitivity_thresholds,
        customPatterns=config_db.custom_patterns,
        logRetentionDays=config_db.log_retention_days,
        updatedAt=config_db.updated_at,
        updatedBy=config_db.updated_by
    )
    
    return created_config
