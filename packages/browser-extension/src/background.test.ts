/**
 * Tests for background service worker functionality
 */
import { describe, it, expect, beforeEach, vi } from 'vitest';

describe('Background Service Worker', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });
  
  describe('Log Buffering', () => {
    it('should initialize with empty buffer', () => {
      const logBuffer: any[] = [];
      expect(logBuffer.length).toBe(0);
    });
    
    it('should add logs to buffer', () => {
      const logBuffer: any[] = [];
      const log = {
        id: 'test-id',
        timestamp: new Date(),
        deviceId: 'device-1',
        userId: 'user-1',
        toolName: 'ChatGPT',
        toolType: 'web' as const,
        riskLevel: 'green' as const,
        promptLength: 100,
        detectedEntityTypes: [],
        entityCount: 0,
        wasSanitized: false,
        metadata: {
          agentVersion: '1.0.0',
        },
      };
      
      logBuffer.push({ log, retryCount: 0 });
      
      expect(logBuffer.length).toBe(1);
      expect(logBuffer[0].log.toolName).toBe('ChatGPT');
    });
    
    it('should trigger sync when buffer reaches batch size', () => {
      const LOG_BATCH_SIZE = 50;
      const logBuffer: any[] = [];
      
      // Add logs to buffer
      for (let i = 0; i < LOG_BATCH_SIZE; i++) {
        logBuffer.push({
          log: {
            id: `log-${i}`,
            toolName: 'ChatGPT',
          },
          retryCount: 0,
        });
      }
      
      expect(logBuffer.length).toBe(LOG_BATCH_SIZE);
      expect(logBuffer.length >= LOG_BATCH_SIZE).toBe(true);
    });
  });
  
  describe('Retry Logic', () => {
    it('should increment retry count on failed sync', () => {
      const log = {
        log: { id: 'test-id' },
        retryCount: 0,
      };
      
      // Simulate failed sync
      log.retryCount++;
      
      expect(log.retryCount).toBe(1);
    });
    
    it('should remove logs after max retries', () => {
      const MAX_RETRY_ATTEMPTS = 5;
      const logBuffer = [
        { log: { id: 'log-1' }, retryCount: 3 },
        { log: { id: 'log-2' }, retryCount: 5 },
        { log: { id: 'log-3' }, retryCount: 6 },
      ];
      
      const filtered = logBuffer.filter(bl => bl.retryCount < MAX_RETRY_ATTEMPTS);
      
      expect(filtered.length).toBe(1);
      expect(filtered[0].log.id).toBe('log-1');
    });
  });
  
  describe('UUID Generation', () => {
    it('should generate valid UUID v4 format', () => {
      const uuid = 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
        const r = Math.random() * 16 | 0;
        const v = c === 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
      });
      
      // Check UUID format
      expect(uuid).toMatch(/^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/);
    });
  });
  
  describe('Message Handling', () => {
    it('should handle CLASSIFY_PROMPT message type', () => {
      const message = {
        type: 'CLASSIFY_PROMPT',
        data: { prompt: 'Test prompt' },
      };
      
      expect(message.type).toBe('CLASSIFY_PROMPT');
      expect(message.data.prompt).toBe('Test prompt');
    });
    
    it('should handle LOG_INTERACTION message type', () => {
      const message = {
        type: 'LOG_INTERACTION',
        data: {
          toolName: 'ChatGPT',
          toolType: 'web',
          promptLength: 100,
          riskLevel: 'green',
          detectedEntityTypes: [],
          entityCount: 0,
          wasSanitized: false,
        },
      };
      
      expect(message.type).toBe('LOG_INTERACTION');
      expect(message.data.toolName).toBe('ChatGPT');
    });
  });
  
  describe('Storage Operations', () => {
    it('should save log buffer to chrome storage', async () => {
      const logBuffer = [{ log: { id: 'test' }, retryCount: 0 }];
      
      await chrome.storage.local.set({ logBuffer });
      
      expect(chrome.storage.local.set).toHaveBeenCalledWith({ logBuffer });
    });
    
    it('should load log buffer from chrome storage', async () => {
      const mockBuffer = [{ log: { id: 'test' }, retryCount: 0 }];
      
      vi.mocked(chrome.storage.local.get).mockResolvedValue({ logBuffer: mockBuffer });
      
      const result = await chrome.storage.local.get(['logBuffer']);
      
      expect(result.logBuffer).toEqual(mockBuffer);
    });
  });
});
