"""Pydantic models for API request/response validation"""
from datetime import datetime
from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field


class DetectedEntity(BaseModel):
    """Detected sensitive entity in a prompt"""
    type: Literal['pii', 'financial', 'contract', 'ip', 'custom']
    value: str
    startIndex: int = Field(alias='start_index')
    endIndex: int = Field(alias='end_index')
    confidence: float

    class Config:
        populate_by_name = True


class ClassificationResult(BaseModel):
    """Result of prompt classification"""
    riskLevel: Literal['green', 'amber', 'red'] = Field(alias='risk_level')
    detectedEntities: List[DetectedEntity] = Field(alias='detected_entities')
    confidence: float
    processingTimeMs: float = Field(alias='processing_time_ms')

    class Config:
        populate_by_name = True


class LogEntryMetadata(BaseModel):
    """Metadata for log entry"""
    browserVersion: Optional[str] = Field(None, alias='browser_version')
    osVersion: Optional[str] = Field(None, alias='os_version')
    agentVersion: str = Field(alias='agent_version')

    class Config:
        populate_by_name = True


class LogEntry(BaseModel):
    """Log entry for AI tool interaction"""
    id: str
    timestamp: datetime
    deviceId: str = Field(alias='device_id')
    userId: str = Field(alias='user_id')
    toolName: str = Field(alias='tool_name')
    toolType: Literal['web', 'desktop', 'cli'] = Field(alias='tool_type')
    riskLevel: Literal['green', 'amber', 'red'] = Field(alias='risk_level')
    promptLength: int = Field(alias='prompt_length')
    detectedEntityTypes: List[str] = Field(alias='detected_entity_types')
    entityCount: int = Field(alias='entity_count')
    wasSanitized: bool = Field(alias='was_sanitized')
    metadata: LogEntryMetadata

    class Config:
        populate_by_name = True


class LogBatchRequest(BaseModel):
    """Request to upload batch of logs"""
    deviceId: str = Field(alias='device_id')
    logs: List[LogEntry]

    class Config:
        populate_by_name = True


class LogFilter(BaseModel):
    """Filter parameters for log queries"""
    startDate: Optional[str] = Field(None, alias='start_date')
    endDate: Optional[str] = Field(None, alias='end_date')
    riskLevel: Optional[Literal['green', 'amber', 'red']] = Field(None, alias='risk_level')
    toolName: Optional[str] = Field(None, alias='tool_name')
    userId: Optional[str] = Field(None, alias='user_id')
    page: int = 1
    limit: int = 50

    class Config:
        populate_by_name = True


class LogPage(BaseModel):
    """Paginated log response"""
    logs: List[LogEntry]
    total: int
    page: int
    limit: int
    totalPages: int = Field(alias='total_pages')

    class Config:
        populate_by_name = True


class SummaryStats(BaseModel):
    """Summary statistics for dashboard"""
    totalInteractions: int = Field(alias='total_interactions')
    riskDistribution: Dict[str, int] = Field(alias='risk_distribution')
    topUsers: List[Dict[str, Any]] = Field(alias='top_users')
    topTools: List[Dict[str, Any]] = Field(alias='top_tools')

    class Config:
        populate_by_name = True


class MonitoredTool(BaseModel):
    """Monitored AI tool configuration"""
    toolName: str = Field(alias='tool_name')
    enabled: bool
    toolType: Literal['web', 'desktop', 'cli'] = Field(alias='tool_type')

    class Config:
        populate_by_name = True


class SensitivityThresholds(BaseModel):
    """Sensitivity thresholds for risk classification"""
    amberMinEntities: int = Field(alias='amber_min_entities')
    redMinEntities: int = Field(alias='red_min_entities')
    highConfidenceThreshold: float = Field(alias='high_confidence_threshold')

    class Config:
        populate_by_name = True


class SensitivityPattern(BaseModel):
    """Custom pattern for detecting sensitive data"""
    id: str
    name: str
    pattern: str
    type: Literal['pii', 'financial', 'contract', 'ip', 'custom']
    enabled: bool


class FirewallConfig(BaseModel):
    """Firewall configuration"""
    id: str
    organizationId: str = Field(alias='organization_id')
    monitoredTools: List[MonitoredTool] = Field(alias='monitored_tools')
    sensitivityThresholds: SensitivityThresholds = Field(alias='sensitivity_thresholds')
    customPatterns: List[SensitivityPattern] = Field(alias='custom_patterns')
    logRetentionDays: int = Field(alias='log_retention_days')
    updatedAt: datetime = Field(alias='updated_at')
    updatedBy: str = Field(alias='updated_by')

    class Config:
        populate_by_name = True
