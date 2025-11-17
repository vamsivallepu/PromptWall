# AI Usage Firewall

A lightweight monitoring and governance system that provides organizations with visibility and control over employee usage of AI tools.

## Project Structure

This is a monorepo containing the following packages:

- **packages/shared**: Shared TypeScript interfaces and types
- **packages/browser-extension**: Browser extension for web AI tool detection
- **packages/desktop-agent**: Desktop agent for monitoring desktop AI applications
- **packages/cli-interceptor**: CLI interceptor for command-line AI tools
- **packages/backend**: FastAPI backend service for log ingestion and API
- **packages/dashboard**: React-based web dashboard for viewing logs and analytics

## Getting Started

### Prerequisites

- Node.js 18+ and npm
- Python 3.10+
- PostgreSQL 14+

### Installation

1. Install Node.js dependencies:
```bash
npm install
```

2. Install Python dependencies for backend:
```bash
cd packages/backend
pip install -r requirements.txt
```

3. Build all packages:
```bash
npm run build
```

### Development

Run all packages in development mode:
```bash
npm run dev
```

Or run individual packages:
```bash
# Shared types
cd packages/shared && npm run dev

# Browser extension
cd packages/browser-extension && npm run dev

# Desktop agent
cd packages/desktop-agent && npm run dev

# CLI interceptor
cd packages/cli-interceptor && npm run dev

# Dashboard
cd packages/dashboard && npm run dev

# Backend
cd packages/backend && uvicorn app.main:app --reload
```

## Architecture

The system consists of:

1. **Client-side agents** that detect AI tool usage and classify prompts locally
2. **Backend API** that receives logs and provides data to the dashboard
3. **Dashboard** for viewing usage analytics and managing configuration

All sensitive data analysis happens on-device to ensure privacy.

## License

Proprietary
