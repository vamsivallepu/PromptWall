# AI Usage Firewall - Browser Extension

Browser extension for monitoring and controlling AI tool usage with sensitive data detection.

## Features

- **Multi-Platform Support**: Monitors ChatGPT, Claude, Gemini, and Copilot
- **Real-Time Classification**: Analyzes prompts as you type using GLiNER ML model
- **Risk Indicators**: Visual feedback showing green/amber/red risk levels
- **Prompt Sanitization**: Automatically replaces sensitive data with placeholders
- **Local Buffering**: Stores logs locally and syncs to backend periodically
- **Privacy-First**: All classification happens locally via backend API

## Installation

### Development Mode

1. Generate extension icons (requires Python with Pillow):
   ```bash
   python create_icons.py
   ```

2. Build the extension:
   ```bash
   npm install
   npm run build
   ```

3. Load in Chrome:
   - Open `chrome://extensions/`
   - Enable "Developer mode"
   - Click "Load unpacked"
   - Select the `dist` folder

3. The extension will now monitor supported AI tools

### Production Mode

The extension will be available on the Chrome Web Store (coming soon).

## Usage

1. Navigate to any supported AI tool (ChatGPT, Claude, Gemini, or Copilot)
2. Start typing a prompt
3. The extension will show a risk indicator in the bottom-right corner
4. If sensitive data is detected, a modal will appear with:
   - Original prompt
   - Sanitized version with placeholders
   - List of detected entities
   - Options to use sanitized version or cancel

## Configuration

The extension connects to a local backend service at `http://localhost:8000` by default. Make sure the backend is running before using the extension.

### Backend Configuration

To start the backend:
```bash
cd packages/backend
uvicorn app.main:app --reload
```

### Extension Settings

The following constants can be configured in `background.ts`:

- `BACKEND_URL`: Backend API endpoint (default: `http://localhost:8000`)
- `LOG_BATCH_SIZE`: Number of logs per sync batch (default: 50)
- `LOG_SYNC_INTERVAL_MS`: Time between syncs (default: 5 minutes)
- `MAX_RETRY_ATTEMPTS`: Maximum retry attempts for failed syncs (default: 5)
- `INITIAL_RETRY_DELAY_MS`: Initial retry delay with exponential backoff (default: 1000ms)

## Development

### Running Tests

```bash
npm test
```

### Watch Mode

```bash
npm run dev
```

### Generating Icons

The extension requires icon files. Generate them using:

```bash
python create_icons.py
```

This creates three icon sizes (16x16, 48x48, 128x128) in the `src/` directory.

### Building

```bash
npm run build
```

## Architecture

### Background Service Worker (`background.ts`)

The background service worker coordinates all extension functionality:

- **Message Handling**: Listens for messages from content scripts
  - `PROMPT_DETECTED`: Handles new prompt detection events
  - `CLASSIFY_PROMPT`: Classifies prompts via backend API
  - `LOG_INTERACTION`: Logs user interactions to buffer

- **Classification**: Calls backend API (`/api/v1/classify`) for prompt analysis
  - Returns risk level (green/amber/red)
  - Detects entities with confidence scores
  - Handles errors gracefully with safe defaults

- **Log Buffering**: Stores logs locally before syncing
  - Buffer size: 50 logs or 5-minute intervals
  - Persistent storage using `chrome.storage.local`
  - Automatic retry with exponential backoff (max 5 attempts)

- **Periodic Sync**: Uploads logs to backend in batches
  - Endpoint: `POST /api/v1/logs/batch`
  - Batch size: 50 logs per request
  - Sync interval: 5 minutes

- **Device Management**: Generates and persists device/user IDs

### Content Script (`content.ts`)

Content script injected into AI tool pages for monitoring user interactions.

### Manifest (`manifest.json`)

Extension configuration and permissions for Manifest V3.

## Supported AI Tools

- ChatGPT (chat.openai.com)
- Claude (claude.ai)
- Gemini (gemini.google.com)
- Microsoft Copilot (copilot.microsoft.com)

## Privacy

- No prompt content is stored or transmitted to external services
- Only metadata (length, risk level, entity types) is logged
- All classification happens via local backend API
- Logs are buffered locally and synced periodically
- Device and user IDs are generated locally and stored in `chrome.storage.local`
- Failed log syncs are retried with exponential backoff, then discarded after 5 attempts

## Requirements

- Chrome/Edge/Firefox with Manifest V3 support
- Backend API running on localhost:8000
- Node.js 18+ for development
- Python 3.x with Pillow library for icon generation (development only)
