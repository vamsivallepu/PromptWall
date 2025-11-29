/**
 * Browser extension background service worker
 * Handles detection logic and coordinates with content scripts
 */

import type { PromptEvent, ClassificationResult, LogEntry } from '@ai-firewall/shared';

console.log('AI Usage Firewall background service worker initialized');

// Configuration
const BACKEND_URL = 'http://localhost:8000';
const LOG_BATCH_SIZE = 50;
const LOG_SYNC_INTERVAL_MS = 5 * 60 * 1000; // 5 minutes
const MAX_RETRY_ATTEMPTS = 5;
const INITIAL_RETRY_DELAY_MS = 1000;

// Local log buffer
interface BufferedLog {
  log: LogEntry;
  retryCount: number;
}

let logBuffer: BufferedLog[] = [];
let syncTimer: number | null = null;

/**
 * Initialize the background service worker
 */
async function initialize() {
  // Load buffered logs from storage
  const result = await chrome.storage.local.get(['logBuffer']);
  if (result.logBuffer) {
    logBuffer = result.logBuffer;
  }
  
  // Start periodic sync
  startPeriodicSync();
  
  // Listen for messages from content scripts
  chrome.runtime.onMessage.addListener(handleMessage);
  
  console.log('Background service worker initialized with', logBuffer.length, 'buffered logs');
}

/**
 * Handle messages from content scripts
 */
function handleMessage(
  message: any,
  sender: chrome.runtime.MessageSender,
  sendResponse: (response?: any) => void
): boolean {
  if (message.type === 'PROMPT_DETECTED') {
    handlePromptDetected(message.data as PromptEvent)
      .then(result => sendResponse({ success: true, data: result }))
      .catch(error => sendResponse({ success: false, error: error.message }));
    return true; // Keep channel open for async response
  }
  
  if (message.type === 'CLASSIFY_PROMPT') {
    classifyPrompt(message.data.prompt)
      .then(result => sendResponse({ success: true, data: result }))
      .catch(error => sendResponse({ success: false, error: error.message }));
    return true;
  }
  
  if (message.type === 'LOG_INTERACTION') {
    logInteraction(message.data)
      .then(() => sendResponse({ success: true }))
      .catch(error => sendResponse({ success: false, error: error.message }));
    return true;
  }
  
  return false;
}

/**
 * Handle prompt detection event
 */
async function handlePromptDetected(event: PromptEvent): Promise<ClassificationResult> {
  console.log('Prompt detected:', event.toolName, event.prompt.length, 'chars');
  
  // Classify the prompt
  const classification = await classifyPrompt(event.prompt);
  
  return classification;
}

/**
 * Classify a prompt by calling the local Python service
 */
async function classifyPrompt(prompt: string): Promise<ClassificationResult> {
  try {
    const startTime = performance.now();
    
    const response = await fetch(`${BACKEND_URL}/api/v1/classify`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ text: prompt }),
    });
    
    if (!response.ok) {
      throw new Error(`Classification failed: ${response.statusText}`);
    }
    
    const result = await response.json();
    const processingTimeMs = performance.now() - startTime;
    
    return {
      riskLevel: result.risk_level,
      detectedEntities: result.detected_entities.map((e: any) => ({
        type: e.type,
        value: e.value,
        startIndex: e.start_index,
        endIndex: e.end_index,
        confidence: e.confidence,
      })),
      confidence: result.confidence,
      processingTimeMs,
    };
  } catch (error) {
    console.error('Classification error:', error);
    // Return safe default on error
    return {
      riskLevel: 'amber',
      detectedEntities: [],
      confidence: 0,
      processingTimeMs: 0,
    };
  }
}

/**
 * Log an interaction to the buffer
 */
async function logInteraction(data: {
  toolName: string;
  toolType: 'web' | 'desktop' | 'cli';
  promptLength: number;
  riskLevel: 'green' | 'amber' | 'red';
  detectedEntityTypes: string[];
  entityCount: number;
  wasSanitized: boolean;
}): Promise<void> {
  const deviceId = await getDeviceId();
  const userId = await getUserId();
  
  const logEntry: LogEntry = {
    id: generateUUID(),
    timestamp: new Date(),
    deviceId,
    userId,
    toolName: data.toolName,
    toolType: data.toolType,
    riskLevel: data.riskLevel,
    promptLength: data.promptLength,
    detectedEntityTypes: data.detectedEntityTypes,
    entityCount: data.entityCount,
    wasSanitized: data.wasSanitized,
    metadata: {
      browserVersion: navigator.userAgent,
      agentVersion: '1.0.0',
    },
  };
  
  // Add to buffer
  logBuffer.push({
    log: logEntry,
    retryCount: 0,
  });
  
  // Save to storage
  await chrome.storage.local.set({ logBuffer });
  
  console.log('Log added to buffer, total:', logBuffer.length);
  
  // Sync if buffer is full
  if (logBuffer.length >= LOG_BATCH_SIZE) {
    await syncLogs();
  }
}

/**
 * Start periodic log synchronization
 */
function startPeriodicSync() {
  if (syncTimer !== null) {
    clearInterval(syncTimer);
  }
  
  syncTimer = setInterval(() => {
    syncLogs().catch(error => {
      console.error('Periodic sync failed:', error);
    });
  }, LOG_SYNC_INTERVAL_MS) as unknown as number;
}

/**
 * Sync buffered logs to backend
 */
async function syncLogs(): Promise<void> {
  if (logBuffer.length === 0) {
    return;
  }
  
  console.log('Syncing', logBuffer.length, 'logs to backend...');
  
  const logsToSync = logBuffer.slice(0, LOG_BATCH_SIZE);
  
  try {
    const response = await fetch(`${BACKEND_URL}/api/v1/logs/batch`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        deviceId: await getDeviceId(),
        logs: logsToSync.map(bl => bl.log),
      }),
    });
    
    if (!response.ok) {
      throw new Error(`Sync failed: ${response.statusText}`);
    }
    
    // Remove synced logs from buffer
    logBuffer = logBuffer.slice(LOG_BATCH_SIZE);
    await chrome.storage.local.set({ logBuffer });
    
    console.log('Sync successful,', logBuffer.length, 'logs remaining');
  } catch (error) {
    console.error('Sync failed:', error);
    
    // Increment retry count for failed logs
    logsToSync.forEach(bl => {
      bl.retryCount++;
    });
    
    // Remove logs that have exceeded max retries
    logBuffer = logBuffer.filter(bl => bl.retryCount < MAX_RETRY_ATTEMPTS);
    await chrome.storage.local.set({ logBuffer });
    
    // Retry with exponential backoff
    const delay = INITIAL_RETRY_DELAY_MS * Math.pow(2, logsToSync[0]?.retryCount || 0);
    setTimeout(() => syncLogs(), delay);
  }
}

/**
 * Get or generate device ID
 */
async function getDeviceId(): Promise<string> {
  const result = await chrome.storage.local.get(['deviceId']);
  if (result.deviceId) {
    return result.deviceId;
  }
  
  const deviceId = generateUUID();
  await chrome.storage.local.set({ deviceId });
  return deviceId;
}

/**
 * Get or generate user ID
 */
async function getUserId(): Promise<string> {
  const result = await chrome.storage.local.get(['userId']);
  if (result.userId) {
    return result.userId;
  }
  
  // In a real implementation, this would come from authentication
  const userId = 'user-' + generateUUID().substring(0, 8);
  await chrome.storage.local.set({ userId });
  return userId;
}

/**
 * Generate a UUID v4
 */
function generateUUID(): string {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = Math.random() * 16 | 0;
    const v = c === 'x' ? r : (r & 0x3 | 0x8);
    return v.toString(16);
  });
}

// Initialize on load
initialize();
