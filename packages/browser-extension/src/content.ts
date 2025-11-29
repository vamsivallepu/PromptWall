/**
 * Content script for AI tool page injection
 * Monitors and intercepts AI tool interactions
 */

import type { PromptEvent, ClassificationResult, DetectedEntity, SanitizationResult } from '@ai-firewall/shared';

// ============================================================================
// COMPREHENSIVE LOGGING SYSTEM
// ============================================================================

interface LogEntry {
  timestamp: string;
  level: 'INFO' | 'WARN' | 'ERROR' | 'DEBUG';
  message: string;
  data?: any;
}

const logHistory: LogEntry[] = [];
const MAX_LOG_HISTORY = 100;

function log(level: 'INFO' | 'WARN' | 'ERROR' | 'DEBUG', message: string, data?: any) {
  const timestamp = new Date().toISOString();
  const entry: LogEntry = { timestamp, level, message, data };

  // Add to history
  logHistory.push(entry);
  if (logHistory.length > MAX_LOG_HISTORY) {
    logHistory.shift();
  }

  // Save to chrome storage
  chrome.storage.local.set({ aiFirewallLogs: logHistory });

  // Console output with emoji
  const emoji = {
    INFO: 'ℹ️',
    WARN: '⚠️',
    ERROR: '❌',
    DEBUG: '🔍'
  }[level];

  const prefix = `[AI-Firewall ${emoji}]`;
  if (data) {
    console.log(prefix, message, data);
  } else {
    console.log(prefix, message);
  }
}

// Export log viewer function to window for easy access
(window as any).viewAIFirewallLogs = () => {
  console.table(logHistory);
  return logHistory;
};

(window as any).clearAIFirewallLogs = () => {
  logHistory.length = 0;
  chrome.storage.local.set({ aiFirewallLogs: [] });
  console.log('[AI-Firewall] Logs cleared');
};

// Initial load log
log('INFO', '🚀 AI Usage Firewall content script loaded', {
  url: window.location.href,
  hostname: window.location.hostname,
  timestamp: new Date().toISOString()
});

// Detect which AI tool we're on
const toolName = detectAITool();
console.log('Detected AI tool:', toolName);

/**
 * Detect which AI tool the current page belongs to
 */
function detectAITool(): string {
  const hostname = window.location.hostname;
  
  if (hostname.includes('chatgpt.com')) return 'ChatGPT';
  if (hostname.includes('claude.ai')) return 'Claude';
  if (hostname.includes('gemini.google.com')) return 'Gemini';
  if (hostname.includes('copilot.microsoft.com')) return 'Copilot';
  
  return 'Unknown';
}

/**
 * Send message to background script with retry logic
 */
async function sendToBackground(type: string, data: any, retries = 3): Promise<any> {
  return new Promise((resolve, reject) => {
    const attemptSend = (attemptsLeft: number) => {
      chrome.runtime.sendMessage({ type, data }, (response) => {
        if (chrome.runtime.lastError) {
          console.warn('Message send failed:', chrome.runtime.lastError.message, 'Retries left:', attemptsLeft);
          
          if (attemptsLeft > 0) {
            // Retry after a short delay
            setTimeout(() => attemptSend(attemptsLeft - 1), 500);
          } else {
            reject(new Error(chrome.runtime.lastError.message));
          }
        } else if (response?.success) {
          resolve(response.data);
        } else {
          reject(new Error(response?.error || 'Unknown error'));
        }
      });
    };
    
    attemptSend(retries);
  });
}

/**
 * Classify a prompt
 */
async function classifyPrompt(prompt: string): Promise<ClassificationResult> {
  return sendToBackground('CLASSIFY_PROMPT', { prompt });
}

/**
 * Log an interaction
 */
async function logInteraction(data: {
  promptLength: number;
  riskLevel: 'green' | 'amber' | 'red';
  detectedEntityTypes: string[];
  entityCount: number;
  wasSanitized: boolean;
}): Promise<void> {
  await sendToBackground('LOG_INTERACTION', {
    toolName,
    toolType: 'web' as const,
    ...data,
  });
}

/**
 * Sanitize a prompt by replacing detected entities with placeholders
 */
function sanitizePrompt(prompt: string, entities: DetectedEntity[]): SanitizationResult {
  if (entities.length === 0) {
    return {
      sanitizedPrompt: prompt,
      replacements: [],
      isFullySanitized: true,
    };
  }
  
  // Sort entities by start index in reverse order to maintain indices during replacement
  const sortedEntities = [...entities].sort((a, b) => b.startIndex - a.startIndex);
  
  let sanitized = prompt;
  const replacements: Array<{ original: string; placeholder: string; type: string }> = [];
  
  for (const entity of sortedEntities) {
    const placeholder = getPlaceholder(entity.type);
    const original = sanitized.substring(entity.startIndex, entity.endIndex);
    
    sanitized = 
      sanitized.substring(0, entity.startIndex) +
      placeholder +
      sanitized.substring(entity.endIndex);
    
    replacements.push({
      original,
      placeholder,
      type: entity.type,
    });
  }
  
  return {
    sanitizedPrompt: sanitized,
    replacements: replacements.reverse(), // Reverse to match original order
    isFullySanitized: true,
  };
}

/**
 * Get placeholder for entity type
 */
function getPlaceholder(type: string): string {
  const placeholders: Record<string, string> = {
    pii: '[PERSONAL_INFO]',
    financial: '[FINANCIAL_DATA]',
    contract: '[CONTRACT_INFO]',
    ip: '[INTELLECTUAL_PROPERTY]',
    custom: '[SENSITIVE_DATA]',
  };
  
  return placeholders[type] || '[REDACTED]';
}

/**
 * Show sanitization modal to user
 */
function showSanitizationModal(
  originalPrompt: string,
  sanitizationResult: SanitizationResult,
  classification: ClassificationResult,
  onUseOriginal: () => void,
  onUseSanitized: () => void,
  onCancel: () => void
): void {
  // Create modal overlay
  const overlay = document.createElement('div');
  overlay.id = 'ai-firewall-modal-overlay';
  overlay.style.cssText = `
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.7);
    z-index: 999999;
    display: flex;
    align-items: center;
    justify-content: center;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  `;
  
  // Create modal
  const modal = document.createElement('div');
  modal.style.cssText = `
    background: white;
    border-radius: 12px;
    padding: 24px;
    max-width: 700px;
    max-height: 80vh;
    overflow-y: auto;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  `;
  
  // Risk level color
  const riskColors = {
    green: '#10b981',
    amber: '#f59e0b',
    red: '#ef4444',
  };
  
  const riskColor = riskColors[classification.riskLevel];
  
  modal.innerHTML = `
    <div style="margin-bottom: 20px;">
      <h2 style="margin: 0 0 8px 0; font-size: 24px; color: #111;">
        ⚠️ Sensitive Data Detected
      </h2>
      <div style="display: inline-block; padding: 4px 12px; background: ${riskColor}; color: white; border-radius: 6px; font-size: 14px; font-weight: 600;">
        ${classification.riskLevel.toUpperCase()} RISK
      </div>
    </div>
    
    <p style="margin: 0 0 20px 0; color: #666; font-size: 14px;">
      We detected ${classification.detectedEntities.length} sensitive ${classification.detectedEntities.length === 1 ? 'entity' : 'entities'} in your prompt. 
      You can use the sanitized version below or cancel the submission.
    </p>
    
    <div style="margin-bottom: 20px;">
      <h3 style="margin: 0 0 8px 0; font-size: 16px; color: #111;">Original Prompt:</h3>
      <div style="background: #f9fafb; border: 1px solid #e5e7eb; border-radius: 8px; padding: 12px; font-size: 14px; color: #374151; max-height: 150px; overflow-y: auto; white-space: pre-wrap; word-break: break-word;">
${escapeHtml(originalPrompt)}
      </div>
    </div>
    
    <div style="margin-bottom: 20px;">
      <h3 style="margin: 0 0 8px 0; font-size: 16px; color: #111;">Sanitized Prompt:</h3>
      <div style="background: #f0fdf4; border: 1px solid #86efac; border-radius: 8px; padding: 12px; font-size: 14px; color: #166534; max-height: 150px; overflow-y: auto; white-space: pre-wrap; word-break: break-word;">
${escapeHtml(sanitizationResult.sanitizedPrompt)}
      </div>
    </div>
    
    <div style="margin-bottom: 20px;">
      <h3 style="margin: 0 0 8px 0; font-size: 16px; color: #111;">Detected Entities:</h3>
      <div style="display: flex; flex-wrap: gap; gap: 8px;">
        ${classification.detectedEntities.map(e => `
          <span style="display: inline-block; padding: 4px 8px; background: #fee; border: 1px solid #fcc; border-radius: 4px; font-size: 12px; color: #c00;">
            ${escapeHtml(e.value)} (${e.type})
          </span>
        `).join('')}
      </div>
    </div>
    
    <div style="display: flex; gap: 12px; justify-content: flex-end;">
      <button id="ai-firewall-cancel" style="padding: 10px 20px; background: #f3f4f6; border: 1px solid #d1d5db; border-radius: 6px; font-size: 14px; font-weight: 600; color: #374151; cursor: pointer;">
        Cancel
      </button>
      <button id="ai-firewall-use-sanitized" style="padding: 10px 20px; background: #10b981; border: none; border-radius: 6px; font-size: 14px; font-weight: 600; color: white; cursor: pointer;">
        Use Sanitized
      </button>
    </div>
  `;
  
  overlay.appendChild(modal);
  document.body.appendChild(overlay);
  
  // Add event listeners
  document.getElementById('ai-firewall-cancel')?.addEventListener('click', () => {
    document.body.removeChild(overlay);
    onCancel();
  });
  
  document.getElementById('ai-firewall-use-sanitized')?.addEventListener('click', () => {
    document.body.removeChild(overlay);
    onUseSanitized();
  });
}

/**
 * Escape HTML to prevent XSS
 */
function escapeHtml(text: string): string {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

/**
 * Handle prompt submission with classification and potential interception
 */
async function handlePromptSubmission(
  prompt: string,
  inputElement: HTMLElement,
  form?: HTMLFormElement
): Promise<void> {
  try {
    // Classify the prompt
    const classification = await classifyPrompt(prompt);
    
    if (classification.riskLevel === 'red' || classification.riskLevel === 'amber') {
      // Show interception modal
      const result = await showInterceptionModal(prompt, classification);
      
      if (result.action === 'cancel') {
        // Log cancellation
        await logInteraction({
          promptLength: prompt.length,
          riskLevel: classification.riskLevel,
          detectedEntityTypes: classification.detectedEntities.map(e => e.type),
          entityCount: classification.detectedEntities.length,
          wasSanitized: false,
        });
        return; // Don't submit
      } else if (result.action === 'sanitized') {
        // Replace with sanitized prompt
        if ('value' in inputElement) {
          (inputElement as HTMLTextAreaElement).value = result.sanitizedPrompt;
        } else {
          inputElement.textContent = result.sanitizedPrompt;
        }
        
        // Log sanitized usage
        await logInteraction({
          promptLength: prompt.length,
          riskLevel: classification.riskLevel,
          detectedEntityTypes: classification.detectedEntities.map(e => e.type),
          entityCount: classification.detectedEntities.length,
          wasSanitized: true,
        });
      }
    } else {
      // Log green interaction
      await logInteraction({
        promptLength: prompt.length,
        riskLevel: 'green',
        detectedEntityTypes: [],
        entityCount: 0,
        wasSanitized: false,
      });
    }
    
    // Allow submission to proceed
    if (form) {
      // Remove our listener temporarily to avoid infinite loop
      const newForm = form.cloneNode(true) as HTMLFormElement;
      form.parentNode?.replaceChild(newForm, form);
      newForm.requestSubmit();
    } else {
      // Trigger the original event
      const event = new KeyboardEvent('keydown', {
        key: 'Enter',
        bubbles: true,
        cancelable: true,
      });
      inputElement.dispatchEvent(event);
    }
  } catch (error) {
    console.error('Error handling prompt submission:', error);
    // Allow submission on error
  }
}

/**
 * Show interception modal and wait for user decision
 */
async function showInterceptionModal(
  prompt: string,
  classification: ClassificationResult
): Promise<{ action: 'cancel' | 'sanitized'; sanitizedPrompt: string }> {
  return new Promise((resolve) => {
    const sanitizationResult = sanitizePrompt(prompt, classification.detectedEntities);
    
    showSanitizationModal(
      prompt,
      sanitizationResult,
      classification,
      () => {
        // Use original (not implemented in this version)
        resolve({ action: 'cancel', sanitizedPrompt: prompt });
      },
      () => {
        // Use sanitized
        resolve({ action: 'sanitized', sanitizedPrompt: sanitizationResult.sanitizedPrompt });
      },
      () => {
        // Cancel
        resolve({ action: 'cancel', sanitizedPrompt: prompt });
      }
    );
  });
}

/**
 * Initialize tool-specific monitoring
 */
function initializeMonitoring() {
  if (toolName === 'ChatGPT') {
    initChatGPTMonitoring();
  } else if (toolName === 'Claude') {
    initClaudeMonitoring();
  } else if (toolName === 'Gemini') {
    initGeminiMonitoring();
  } else if (toolName === 'Copilot') {
    initCopilotMonitoring();
  }
}

/**
 * Initialize ChatGPT monitoring using API interception
 * Intercepts fetch calls to ChatGPT's backend API
 */
function initChatGPTMonitoring() {
  log('INFO', '🔧 Initializing ChatGPT API interception');

  // Store original fetch
  const originalFetch = window.fetch;

  if (!originalFetch) {
    log('ERROR', 'window.fetch is not available!');
    return;
  }

  log('INFO', '✅ window.fetch found, setting up interception');

  // Override fetch to intercept ChatGPT API calls
  (window.fetch as any) = async function(url: RequestInfo | URL, options?: RequestInit): Promise<Response> {

    // Detect ChatGPT API calls
    const urlString = typeof url === 'string' ? url : url.toString();
    const isChatGPTApi = (
      (urlString.includes('chat.openai.com') || urlString.includes('chatgpt.com')) &&
      urlString.includes('/backend-api/') &&
      (urlString.includes('/conversation') || urlString.includes('/f/conversation')) &&
      options?.method === 'POST'
    );

    if (isChatGPTApi && options?.body) {
      log('INFO', '🎯 Intercepted ChatGPT API call', { url: urlString });

      try {
        // Parse request body
        const requestBody = typeof options.body === 'string'
          ? JSON.parse(options.body)
          : options.body;

        log('DEBUG', '📦 Request body structure', {
          hasMessages: !!requestBody.messages,
          messageCount: requestBody.messages?.length,
          keys: Object.keys(requestBody)
        });

        // Extract the user's prompt (last message in the conversation)
        let userPrompt = '';
        if (requestBody.messages && Array.isArray(requestBody.messages)) {
          // Find the last user message (filter by author.role === 'user')
          const userMessages = requestBody.messages.filter((msg: any) => msg.author?.role === 'user');
          const lastUserMessage = userMessages[userMessages.length - 1];

          log('DEBUG', 'Found user messages', { count: userMessages.length });

          if (lastUserMessage) {
            // ChatGPT structure: content.parts is an array of strings
            if (lastUserMessage.content?.parts && Array.isArray(lastUserMessage.content.parts)) {
              // Join all parts (usually just one for text-only messages)
              userPrompt = lastUserMessage.content.parts.join('\n');
              log('DEBUG', 'Extracted from content.parts');
            }
            // Fallback: handle direct string content
            else if (typeof lastUserMessage.content === 'string') {
              userPrompt = lastUserMessage.content;
              log('DEBUG', 'Extracted from string content');
            }
          }
        }

        log('INFO', '✉️ Extracted prompt', {
          length: userPrompt.length,
          preview: userPrompt.substring(0, 100)
        });

        if (userPrompt && userPrompt.trim()) {
          // Classify the prompt
          log('INFO', '🔍 Classifying prompt...');
          const classification = await classifyPrompt(userPrompt);
          log('INFO', '📊 Classification result', {
            riskLevel: classification.riskLevel,
            entityCount: classification.detectedEntities.length
          });

          // Handle based on risk level
          if (classification.riskLevel === 'red' || classification.riskLevel === 'amber') {
            log('WARN', '⚠️ High risk detected, showing modal');

            // Show interception modal
            const result = await showInterceptionModal(userPrompt, classification);

            if (result.action === 'cancel') {
              log('INFO', '🚫 User cancelled the request');

              // Log cancellation
              await logInteraction({
                promptLength: userPrompt.length,
                riskLevel: classification.riskLevel,
                detectedEntityTypes: classification.detectedEntities.map(e => e.type),
                entityCount: classification.detectedEntities.length,
                wasSanitized: false,
              });

              // Block the request by returning an error response
              return new Response(
                JSON.stringify({
                  error: 'Request cancelled by AI Usage Firewall',
                  message: 'Sensitive data detected and request was cancelled by user'
                }),
                {
                  status: 400,
                  headers: { 'Content-Type': 'application/json' }
                }
              );
            } else if (result.action === 'sanitized') {
              log('INFO', '✅ User chose sanitized version');

              // Replace the prompt with sanitized version
              if (requestBody.messages && Array.isArray(requestBody.messages)) {
                const userMessages = requestBody.messages.filter((msg: any) => msg.author?.role === 'user');
                const lastUserMessage = userMessages[userMessages.length - 1];

                if (lastUserMessage) {
                  // ChatGPT structure: replace content.parts array
                  if (lastUserMessage.content?.parts && Array.isArray(lastUserMessage.content.parts)) {
                    lastUserMessage.content.parts = [result.sanitizedPrompt];
                  }
                  // Fallback: handle direct string content
                  else if (typeof lastUserMessage.content === 'string') {
                    lastUserMessage.content = result.sanitizedPrompt;
                  }
                }
              }

              // Update the request body
              options.body = JSON.stringify(requestBody);
              log('INFO', '📝 Request body updated with sanitized prompt');

              // Log sanitized usage
              await logInteraction({
                promptLength: userPrompt.length,
                riskLevel: classification.riskLevel,
                detectedEntityTypes: classification.detectedEntities.map(e => e.type),
                entityCount: classification.detectedEntities.length,
                wasSanitized: true,
              });
            }
          } else {
            log('INFO', '✅ Low risk, allowing request');

            // Log green interaction
            await logInteraction({
              promptLength: userPrompt.length,
              riskLevel: 'green',
              detectedEntityTypes: [],
              entityCount: 0,
              wasSanitized: false,
            });
          }
        }
      } catch (error) {
        log('ERROR', '❌ Error intercepting ChatGPT request', { error });
        // On error, allow the request to proceed
      }
    }

    // Proceed with the (possibly modified) request
    return originalFetch(url, options);
  };

  log('INFO', '✅ ChatGPT API interception setup complete');
}

/**
 * Initialize Claude monitoring
 * Intercepts API calls to Claude's backend
 */
function initClaudeMonitoring() {
  console.log('Claude monitoring initialized');
  
  // Intercept fetch requests to Claude API
  const originalFetch = window.fetch;
  window.fetch = async function(...args) {
    const [url, options] = args;
    
    // Check if this is a Claude API call
    if (typeof url === 'string' && url.includes('/api/') && options?.method === 'POST') {
      try {
        const body = options.body;
        if (typeof body === 'string') {
          const data = JSON.parse(body);
          
          // Extract prompt from various possible fields
          const prompt = data.prompt || data.message || data.text || '';
          
          if (prompt && typeof prompt === 'string' && prompt.trim()) {
            // Classify and potentially intercept
            const classification = await classifyPrompt(prompt);
            
            if (classification.riskLevel === 'red' || classification.riskLevel === 'amber') {
              // Show modal and wait for user decision
              const result = await showInterceptionModal(prompt, classification);
              
              if (result.action === 'cancel') {
                // Log cancellation
                await logInteraction({
                  promptLength: prompt.length,
                  riskLevel: classification.riskLevel,
                  detectedEntityTypes: classification.detectedEntities.map(e => e.type),
                  entityCount: classification.detectedEntities.length,
                  wasSanitized: false,
                });
                
                // Return empty response to cancel
                return new Response(JSON.stringify({ error: 'Cancelled by user' }), {
                  status: 400,
                  headers: { 'Content-Type': 'application/json' },
                });
              } else if (result.action === 'sanitized') {
                // Replace prompt with sanitized version
                data.prompt = result.sanitizedPrompt;
                data.message = result.sanitizedPrompt;
                data.text = result.sanitizedPrompt;
                
                options.body = JSON.stringify(data);
                
                // Log sanitized usage
                await logInteraction({
                  promptLength: prompt.length,
                  riskLevel: classification.riskLevel,
                  detectedEntityTypes: classification.detectedEntities.map(e => e.type),
                  entityCount: classification.detectedEntities.length,
                  wasSanitized: true,
                });
              }
            } else {
              // Log green interaction
              await logInteraction({
                promptLength: prompt.length,
                riskLevel: 'green',
                detectedEntityTypes: [],
                entityCount: 0,
                wasSanitized: false,
              });
            }
          }
        }
      } catch (error) {
        console.error('Error intercepting Claude request:', error);
      }
    }
    
    return originalFetch.apply(this, args);
  };
}

/**
 * Initialize Gemini monitoring
 * Monitors input fields for prompt submission
 */
function initGeminiMonitoring() {
  console.log('Gemini monitoring initialized');
  
  // Monitor for input elements
  const observer = new MutationObserver(() => {
    const inputElements = document.querySelectorAll('textarea, div[contenteditable="true"]');
    
    inputElements.forEach((element) => {
      const htmlElement = element as HTMLElement;
      if (!htmlElement.dataset || htmlElement.dataset.aiFirewallMonitored) return;
      
      htmlElement.dataset.aiFirewallMonitored = 'true';
      console.log('Found Gemini input element, attaching listener');
      
      // Add real-time classification
      addRealTimeClassification(htmlElement);
      
      // Monitor for Enter key or button clicks
      htmlElement.addEventListener('keydown', async (e: KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
          const prompt = (element as HTMLTextAreaElement).value || (element as HTMLElement).textContent || '';
          if (!prompt.trim()) return;
          
          e.preventDefault();
          e.stopPropagation();
          
          await handlePromptSubmission(prompt.trim(), htmlElement);
        }
      }, { capture: true });
    });
    
    // Also monitor submit buttons
    const submitButtons = document.querySelectorAll('button[type="submit"], button[aria-label*="Send"]');
    submitButtons.forEach((button) => {
      const htmlButton = button as HTMLElement;
      if (!htmlButton.dataset || htmlButton.dataset.aiFirewallMonitored) return;
      
      htmlButton.dataset.aiFirewallMonitored = 'true';
      
      button.addEventListener('click', async (e) => {
        const inputElement = document.querySelector('textarea, div[contenteditable="true"]') as HTMLElement;
        if (!inputElement) return;
        
        const prompt = (inputElement as HTMLTextAreaElement).value || inputElement.textContent || '';
        if (!prompt.trim()) return;
        
        e.preventDefault();
        e.stopPropagation();
        
        await handlePromptSubmission(prompt.trim(), inputElement);
      }, { capture: true });
    });
  });
  
  observer.observe(document.body, {
    childList: true,
    subtree: true,
  });
}

/**
 * Initialize Copilot monitoring
 * Captures prompts from Microsoft Copilot interface
 */
function initCopilotMonitoring() {
  console.log('Copilot monitoring initialized');
  
  // Monitor for textarea and input elements
  const observer = new MutationObserver(() => {
    const textarea = document.querySelector('textarea[placeholder*="Ask"], textarea.input-area, #userInput') as HTMLTextAreaElement;
    
    if (textarea && !textarea.dataset.aiFirewallMonitored) {
      textarea.dataset.aiFirewallMonitored = 'true';
      console.log('Found Copilot textarea, attaching listener');
      
      // Add real-time classification
      addRealTimeClassification(textarea);
      
      // Intercept form submission
      const form = textarea.closest('form');
      if (form) {
        form.addEventListener('submit', async (e) => {
          const prompt = textarea.value.trim();
          if (!prompt) return;
          
          e.preventDefault();
          e.stopPropagation();
          
          await handlePromptSubmission(prompt, textarea, form);
        }, { capture: true });
      }
      
      // Also monitor Enter key
      textarea.addEventListener('keydown', async (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
          const prompt = textarea.value.trim();
          if (!prompt) return;
          
          e.preventDefault();
          e.stopPropagation();
          
          await handlePromptSubmission(prompt, textarea);
        }
      }, { capture: true });
    }
  });
  
  observer.observe(document.body, {
    childList: true,
    subtree: true,
  });
}

/**
 * Show risk level indicator near input element
 */
function showRiskIndicator(
  inputElement: HTMLElement,
  riskLevel: 'green' | 'amber' | 'red',
  entityCount: number
): void {
  // Remove existing indicator
  const existing = document.getElementById('ai-firewall-risk-indicator');
  if (existing) {
    existing.remove();
  }
  
  // Create indicator
  const indicator = document.createElement('div');
  indicator.id = 'ai-firewall-risk-indicator';
  
  const colors = {
    green: '#10b981',
    amber: '#f59e0b',
    red: '#ef4444',
  };
  
  const labels = {
    green: 'Safe',
    amber: 'Caution',
    red: 'Warning',
  };
  
  indicator.style.cssText = `
    position: fixed;
    bottom: 20px;
    right: 20px;
    padding: 12px 16px;
    background: ${colors[riskLevel]};
    color: white;
    border-radius: 8px;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    font-size: 14px;
    font-weight: 600;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    z-index: 999998;
    display: flex;
    align-items: center;
    gap: 8px;
    animation: slideIn 0.3s ease-out;
  `;
  
  indicator.innerHTML = `
    <span>🛡️</span>
    <span>${labels[riskLevel]}</span>
    ${entityCount > 0 ? `<span style="opacity: 0.9;">(${entityCount} ${entityCount === 1 ? 'entity' : 'entities'})</span>` : ''}
  `;
  
  // Add animation
  const style = document.createElement('style');
  style.textContent = `
    @keyframes slideIn {
      from {
        transform: translateX(100%);
        opacity: 0;
      }
      to {
        transform: translateX(0);
        opacity: 1;
      }
    }
  `;
  document.head.appendChild(style);
  
  document.body.appendChild(indicator);
  
  // Auto-remove after 3 seconds
  setTimeout(() => {
    if (indicator.parentNode) {
      indicator.style.animation = 'slideIn 0.3s ease-out reverse';
      setTimeout(() => indicator.remove(), 300);
    }
  }, 3000);
}

/**
 * Add real-time classification as user types
 */
function addRealTimeClassification(inputElement: HTMLElement): void {
  let debounceTimer: number;
  
  const handleInput = async () => {
    clearTimeout(debounceTimer);
    
    debounceTimer = setTimeout(async () => {
      const text = ('value' in inputElement) 
        ? (inputElement as HTMLTextAreaElement).value 
        : inputElement.textContent || '';
      
      if (text.trim().length < 10) return; // Don't classify very short text
      
      try {
        const classification = await classifyPrompt(text);
        showRiskIndicator(inputElement, classification.riskLevel, classification.detectedEntities.length);
      } catch (error) {
        console.error('Real-time classification error:', error);
      }
    }, 1000) as unknown as number; // Debounce for 1 second
  };
  
  inputElement.addEventListener('input', handleInput);
  inputElement.addEventListener('keyup', handleInput);
}

// Start monitoring
log('INFO', 'Starting monitoring for tool: ' + toolName);

// Wait a bit for the background script to initialize
setTimeout(() => {
  log('INFO', 'Initializing monitoring...');
  initializeMonitoring();

  // Test backend connectivity
  setTimeout(async () => {
    log('INFO', 'Testing backend connectivity...');
    try {
      const result = await classifyPrompt('test prompt');
      log('INFO', 'Backend connection successful', result);
    } catch (error) {
      log('ERROR', 'Backend connection failed', { error });
      log('WARN', 'Make sure the backend is running: cd packages/backend && uvicorn app.main:app --reload');
    }
  }, 2000);
}, 500);
