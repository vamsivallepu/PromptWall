# ChatGPT API Interception - Testing Guide

## What Changed

We've replaced the old DOM-based monitoring approach with **API-level interception** for ChatGPT. Instead of watching for textareas and form submissions, we now intercept the actual fetch requests to ChatGPT's backend API.

## How It Works

1. **Fetch Interception**: Overrides `window.fetch` to intercept all network requests
2. **ChatGPT Detection**: Identifies requests to `*/backend-api/conversation` endpoints
3. **Prompt Extraction**: Parses the request body and extracts the last user message
4. **Classification**: Sends the prompt to the backend for risk analysis
5. **Interception**: If risky, shows modal and either blocks or sanitizes the request
6. **Request Modification**: Updates the API request body with sanitized content

## Setup Instructions

### 1. Start the Backend

Make sure your FastAPI backend is running:

```bash
cd packages/backend
uvicorn app.main:app --reload
```

The backend should be accessible at `http://localhost:8000`

### 2. Load the Extension in Chrome

1. Open Chrome and navigate to `chrome://extensions/`
2. Enable "Developer mode" (toggle in top right)
3. Click "Load unpacked"
4. Select the `packages/browser-extension/dist` folder
5. The extension should now appear in your extensions list

### 3. Enable Console Logging

To see detailed debug logs:

1. Navigate to ChatGPT: `https://chat.openai.com` or `https://chatgpt.com`
2. Open Chrome DevTools (F12 or Cmd+Option+I on Mac)
3. Go to the "Console" tab
4. Look for these logs:
   - `🔧 ChatGPT API interception initialized`
   - `✅ ChatGPT API interception setup complete`

## Testing Scenarios

### Test 1: Safe Prompt (Green)

**Prompt to test:**
```
What's the weather like today?
```

**Expected behavior:**
- Console shows: `✅ Low risk, allowing request`
- No modal appears
- Request proceeds normally to ChatGPT
- ChatGPT responds as usual

### Test 2: Moderate Risk Prompt (Amber)

**Prompt to test:**
```
Can you help me draft an email to john.doe@example.com about our project?
```

**Expected behavior:**
- Console shows: `⚠️ High risk detected, showing modal...`
- Modal appears showing the detected email address
- You can choose "Cancel" or "Use Sanitized"
- Sanitized version replaces email with `[PERSONAL_INFO]`

### Test 3: High Risk Prompt (Red)

**Prompt to test:**
```
Here's my credit card number: 4532-1234-5678-9010. Can you tell me if it's valid?
```

**Expected behavior:**
- Console shows: `⚠️ High risk detected, showing modal...`
- Modal appears showing detected financial data
- Sanitized version shows: `[FINANCIAL_DATA]`

### Test 4: Multiple Sensitive Entities

**Prompt to test:**
```
My name is John Smith, email is john@company.com, and my SSN is 123-45-6789. Can you help me fill out this form?
```

**Expected behavior:**
- Modal shows multiple detected entities (email, PII)
- All sensitive data is replaced with placeholders

## Debug Logs to Watch

When you send a prompt, you should see these console logs in sequence:

```
🎯 Intercepted ChatGPT API call: https://chat.openai.com/backend-api/conversation
📦 Request body structure: { hasMessages: true, messageCount: X, keys: [...] }
✉️ Extracted prompt: [first 100 chars of your prompt]...
🔍 Classifying prompt...
📊 Classification result: { riskLevel: 'green/amber/red', entityCount: X }
```

Then either:
- `✅ Low risk, allowing request` (for green)
- `⚠️ High risk detected, showing modal...` (for amber/red)

After user action:
- `🚫 User cancelled the request` (if cancelled)
- `✅ User chose sanitized version` + `📝 Request body updated` (if sanitized)

## Troubleshooting

### Extension Not Loading
- Check that the extension appears in `chrome://extensions/`
- Make sure it's enabled (toggle is on)
- Refresh the ChatGPT page

### No Console Logs
- Make sure you're on `chat.openai.com` or `chatgpt.com`
- Check the Console tab in DevTools
- Try sending a test message

### Backend Connection Failed
- Verify backend is running: `curl http://localhost:8000/health`
- Check console for errors like "Backend connection failed"
- Look for CORS errors

### Modal Not Appearing
- Check console for classification results
- Verify the risk level is "amber" or "red"
- Check for JavaScript errors in console

### Request Not Modified
- Check console log: `📝 Request body updated with sanitized prompt`
- Verify the request body structure matches expected format
- Look for errors in the interception logic

## Advantages Over Old Approach

✅ **No DOM dependencies** - Works regardless of UI changes
✅ **More reliable** - Captures actual API requests
✅ **Simpler code** - Single interception point
✅ **Better accuracy** - Gets exact data sent to LLM
✅ **Future-proof** - Less likely to break with UI updates

## Next Steps

Once ChatGPT interception is working:
1. Apply same approach to Claude
2. Apply to Gemini
3. Apply to Copilot
4. Remove all old DOM-based monitoring code
