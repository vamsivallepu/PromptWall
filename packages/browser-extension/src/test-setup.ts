/**
 * Test setup for browser extension tests
 * Mocks Chrome extension APIs
 */

// Mock chrome.runtime API
global.chrome = {
  runtime: {
    sendMessage: vi.fn((message, callback) => {
      // Mock response
      if (callback) {
        callback({ success: true, data: {} });
      }
      return Promise.resolve({ success: true, data: {} });
    }),
    onMessage: {
      addListener: vi.fn(),
    },
    lastError: null,
  },
  storage: {
    local: {
      get: vi.fn((keys) => Promise.resolve({})),
      set: vi.fn((items) => Promise.resolve()),
    },
  },
} as any;
