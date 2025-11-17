/**
 * Shared TypeScript interfaces for AI Usage Firewall
 */

/**
 * Event emitted when AI tool usage is detected
 */
export interface PromptEvent {
  toolName: string;
  toolType: 'web' | 'desktop' | 'cli';
  prompt: string;
  timestamp: Date;
  userId: string;
  metadata: Record<string, any>;
}

/**
 * Result of prompt classification
 */
export interface ClassificationResult {
  riskLevel: 'green' | 'amber' | 'red';
  detectedEntities: DetectedEntity[];
  confidence: number;
  processingTimeMs: number;
}

/**
 * Detected sensitive entity in a prompt
 */
export interface DetectedEntity {
  type: 'pii' | 'financial' | 'contract' | 'ip' | 'custom';
  value: string;
  startIndex: number;
  endIndex: number;
  confidence: number;
}

/**
 * Log entry stored in the database
 */
export interface LogEntry {
  id: string;
  timestamp: Date;
  deviceId: string;
  userId: string;
  toolName: string;
  toolType: 'web' | 'desktop' | 'cli';
  riskLevel: 'green' | 'amber' | 'red';
  promptLength: number;
  detectedEntityTypes: string[];
  entityCount: number;
  wasSanitized: boolean;
  metadata: {
    browserVersion?: string;
    osVersion?: string;
    agentVersion: string;
  };
}

/**
 * Result of prompt sanitization
 */
export interface SanitizationResult {
  sanitizedPrompt: string;
  replacements: Replacement[];
  isFullySanitized: boolean;
}

/**
 * Replacement made during sanitization
 */
export interface Replacement {
  original: string;
  placeholder: string;
  type: string;
}

/**
 * Firewall configuration
 */
export interface FirewallConfig {
  id: string;
  organizationId: string;
  monitoredTools: MonitoredTool[];
  sensitivityThresholds: SensitivityThresholds;
  customPatterns: SensitivityPattern[];
  logRetentionDays: number;
  updatedAt: Date;
  updatedBy: string;
}

/**
 * Monitored AI tool configuration
 */
export interface MonitoredTool {
  toolName: string;
  enabled: boolean;
  toolType: 'web' | 'desktop' | 'cli';
}

/**
 * Sensitivity thresholds for risk classification
 */
export interface SensitivityThresholds {
  amberMinEntities: number;
  redMinEntities: number;
  highConfidenceThreshold: number;
}

/**
 * Custom pattern for detecting sensitive data
 */
export interface SensitivityPattern {
  id: string;
  name: string;
  pattern: string;
  type: 'pii' | 'financial' | 'contract' | 'ip' | 'custom';
  enabled: boolean;
}

/**
 * AI tool pattern for detection
 */
export interface AIToolPattern {
  toolName: string;
  toolType: 'web' | 'desktop' | 'cli';
  domains?: string[];
  processNames?: string[];
  commandPatterns?: string[];
}

/**
 * Pagination parameters
 */
export interface Pagination {
  page: number;
  limit: number;
}

/**
 * Log filter parameters
 */
export interface LogFilter {
  startDate?: string;
  endDate?: string;
  riskLevel?: 'green' | 'amber' | 'red';
  toolName?: string;
  userId?: string;
}

/**
 * Time range for statistics
 */
export interface TimeRange {
  startDate: string;
  endDate: string;
}

/**
 * Summary statistics
 */
export interface SummaryStats {
  totalInteractions: number;
  riskDistribution: {
    green: number;
    amber: number;
    red: number;
  };
  topUsers: Array<{
    userId: string;
    count: number;
  }>;
  topTools: Array<{
    toolName: string;
    count: number;
  }>;
}

/**
 * Paginated log response
 */
export interface LogPage {
  logs: LogEntry[];
  total: number;
  page: number;
  limit: number;
  totalPages: number;
}
