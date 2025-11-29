# Extension Debugging Guide

## What Changed

I've added a **comprehensive logging system** that:
- ✅ Logs to both console and chrome.storage
- ✅ Tracks every step of the interception process
- ✅ Provides easy-to-read emoji-based logs
- ✅ Allows viewing full log history
- ✅ Fixed manifest to include `chatgpt.com` domain

## Step 1: Reload the Extension

**IMPORTANT:** After building, you must reload the extension!

1. Go to `chrome://extensions/`
2. Find "AI Usage Firewall"
3. Click the **reload icon** (circular arrow)
4. You should see "Version 1.0.0" displayed

## Step 2: Open ChatGPT with DevTools

1. Navigate to `https://chatgpt.com` (or `https://chat.openai.com`)
2. **BEFORE doing anything else**, open DevTools:
   - Press **F12** (or Cmd+Option+I on Mac)
   - Go to the **Console** tab
3. You should immediately see these logs:

```
[AI-Firewall ℹ️] 🚀 AI Usage Firewall content script loaded {url: "https://chatgpt.com/...", hostname: "chatgpt.com", timestamp: "..."}
[AI-Firewall ℹ️] Starting monitoring for tool: ChatGPT
[AI-Firewall ℹ️] Initializing monitoring...
[AI-Firewall ℹ️] 🔧 Initializing ChatGPT API interception
[AI-Firewall ℹ️] ✅ window.fetch found, setting up interception
[AI-Firewall ℹ️] ✅ ChatGPT API interception setup complete
[AI-Firewall ℹ️] Testing backend connectivity...
```

### If You DON'T See These Logs

**Problem: Content script not loading**

Check these:

1. **Verify extension is enabled:**
   - Go to `chrome://extensions/`
   - Make sure the toggle is ON (blue)

2. **Check if content script is injected:**
   - In DevTools, go to **Sources** tab
   - Look for `content.js` in the file tree
   - If missing, the extension isn't loading

3. **Check for errors:**
   - In Console tab, look for red error messages
   - Take a screenshot and share it

4. **Hard refresh the page:**
   - Press **Ctrl+Shift+R** (or Cmd+Shift+R on Mac)
   - This clears cache and reloads everything

## Step 3: View All Logs

In the Console, type these commands to view logs:

### View All Logs as Table
```javascript
viewAIFirewallLogs()
```

This will show a nice table with all log entries including:
- Timestamp
- Level (INFO/WARN/ERROR/DEBUG)
- Message
- Data

### Clear Logs
```javascript
clearAIFirewallLogs()
```

## Step 4: Send a Test Message

1. Type "hello" in ChatGPT
2. Press Enter or click Send
3. Watch the Console

### Expected Logs When Sending a Message

You should see this sequence:

```
[AI-Firewall ℹ️] 🎯 Intercepted ChatGPT API call {url: "https://chatgpt.com/backend-api/f/conversation"}
[AI-Firewall 🔍] 📦 Request body structure {hasMessages: true, messageCount: 1, keys: Array(16)}
[AI-Firewall 🔍] Found user messages {count: 1}
[AI-Firewall 🔍] Extracted from content.parts
[AI-Firewall ℹ️] ✉️ Extracted prompt {length: 5, preview: "hello"}
[AI-Firewall ℹ️] 🔍 Classifying prompt...
[AI-Firewall ℹ️] 📊 Classification result {riskLevel: "green", entityCount: 0}
[AI-Firewall ℹ️] ✅ Low risk, allowing request
```

### If You DON'T See "Intercepted ChatGPT API call"

This means the fetch interception isn't working. Try:

1. **Check if fetch is being called:**
   - Open Network tab in DevTools
   - Send a message
   - Look for `/backend-api/f/conversation` request
   - If you see it, fetch is working but our interception isn't

2. **Verify the interception was set up:**
   - Look for: `✅ ChatGPT API interception setup complete`
   - If missing, there's an initialization error

3. **Check for timing issues:**
   - The content script runs at `document_start`
   - If ChatGPT loads before our script, interception might fail
   - Try refreshing the page with DevTools already open

## Step 5: Test with Sensitive Data

Try this prompt:
```
My email is john.doe@example.com
```

You should see:
```
[AI-Firewall ℹ️] 🎯 Intercepted ChatGPT API call
[AI-Firewall ℹ️] ✉️ Extracted prompt {length: 31, preview: "My email is john.doe@example.com"}
[AI-Firewall ℹ️] 🔍 Classifying prompt...
[AI-Firewall ℹ️] 📊 Classification result {riskLevel: "amber", entityCount: 1}
[AI-Firewall ⚠️] ⚠️ High risk detected, showing modal
```

A modal should appear showing the detected email.

## Step 6: Check Backend Connection

The extension automatically tests backend connectivity. Look for:

```
[AI-Firewall ℹ️] Testing backend connectivity...
[AI-Firewall ℹ️] Backend connection successful {riskLevel: "green", ...}
```

### If Backend Connection Fails

```
[AI-Firewall ❌] Backend connection failed {error: {...}}
[AI-Firewall ⚠️] Make sure the backend is running: cd packages/backend && uvicorn app.main:app --reload
```

**To fix:**
1. Open a terminal
2. Navigate to backend: `cd packages/backend`
3. Start the server: `uvicorn app.main:app --reload`
4. Verify it's running: `curl http://localhost:8000/health`
5. Refresh ChatGPT page

## Troubleshooting Common Issues

### Issue: "Detected AI tool: Unknown"

**Cause:** You're on a non-ChatGPT page

**Fix:** Navigate to `https://chatgpt.com` or `https://chat.openai.com`

### Issue: No logs appear at all

**Cause:** Content script not loading

**Fixes:**
1. Reload extension at `chrome://extensions/`
2. Hard refresh page (Ctrl+Shift+R)
3. Check if extension has permissions for chatgpt.com
4. Try disabling/enabling the extension

### Issue: "window.fetch is not available"

**Cause:** Script running before fetch is defined (very rare)

**Fix:** Add a small delay before initialization (already handled)

### Issue: Logs show but no interception

**Cause:** URL pattern not matching

**Debug:**
1. Check the exact URL in the address bar
2. Look for the "Intercepted ChatGPT API call" log
3. If missing, the URL pattern might not match
4. Share the URL and we can update the pattern

### Issue: Modal appears but request still sent

**Cause:** Modal action not being handled correctly

**Debug:**
1. Check which action you selected (Cancel or Use Sanitized)
2. Look for corresponding log: "User cancelled" or "User chose sanitized"
3. Check Network tab to see if request was modified or blocked

## Viewing Stored Logs

Logs are also saved to chrome.storage. To view them:

1. Go to `chrome://extensions/`
2. Find "AI Usage Firewall"
3. Click "Details"
4. Scroll to "Inspect views" and click "service worker" or "background page"
5. In the console, type:
   ```javascript
   chrome.storage.local.get(['aiFirewallLogs'], (result) => {
     console.table(result.aiFirewallLogs);
   });
   ```

## Log Levels

- **ℹ️ INFO:** Normal operations (interceptions, extractions, decisions)
- **⚠️ WARN:** Warnings (high risk detected, missing backend)
- **❌ ERROR:** Errors (failed to intercept, parse errors)
- **🔍 DEBUG:** Detailed debug info (request structure, extraction details)

## Quick Verification Checklist

Before reporting an issue, verify:

- [ ] Extension is enabled at `chrome://extensions/`
- [ ] Extension has been reloaded after building
- [ ] You're on `chatgpt.com` or `chat.openai.com`
- [ ] DevTools Console is open
- [ ] You see "AI Usage Firewall content script loaded" log
- [ ] You see "ChatGPT API interception setup complete" log
- [ ] Backend is running at `http://localhost:8000`
- [ ] You sent a message in ChatGPT
- [ ] You checked Network tab for `/backend-api/` requests

## Getting Help

If you've tried everything and it's still not working:

1. **Take screenshots of:**
   - Chrome extensions page showing the extension
   - Console tab with all logs visible
   - Network tab showing requests (if any)

2. **Share this info:**
   - Exact URL you're on
   - Which step failed
   - Any error messages in red
   - Output of `viewAIFirewallLogs()`

3. **Try the backend directly:**
   ```bash
   curl -X POST http://localhost:8000/api/v1/classify \
     -H "Content-Type: application/json" \
     -d '{"text":"test email: john@example.com"}'
   ```
   Share the output

## Success Indicators

You'll know everything is working when:

1. ✅ Console shows initial load logs
2. ✅ Backend connectivity test passes
3. ✅ Sending "hello" shows interception logs
4. ✅ Sending email shows modal with detection
5. ✅ Modal allows cancel/sanitize actions
6. ✅ Actions are logged correctly
