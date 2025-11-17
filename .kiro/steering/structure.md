# Project Structure

## Monorepo Organization

This is an npm workspaces monorepo with the following structure:

```
ai-usage-firewall/
├── packages/
│   ├── shared/              # Shared TypeScript types and interfaces
│   ├── browser-extension/   # Chrome/browser extension
│   ├── desktop-agent/       # Desktop application monitor
│   ├── cli-interceptor/     # CLI tool interceptor
│   ├── backend/             # FastAPI Python backend
│   └── dashboard/           # React web dashboard
├── package.json             # Root workspace configuration
└── tsconfig.json            # Root TypeScript configuration
```

## Package Details

### packages/shared
- **Purpose**: Shared TypeScript interfaces and types used across all packages
- **Key files**: `src/types/index.ts` - All shared type definitions
- **Exports**: PromptEvent, ClassificationResult, LogEntry, FirewallConfig, etc.
- **Dependencies**: None (pure types)

### packages/browser-extension
- **Purpose**: Browser extension for detecting web-based AI tool usage
- **Key files**: 
  - `src/background.ts` - Background service worker
  - `src/content.ts` - Content script for page interaction
  - `src/manifest.json` - Extension manifest
- **Build**: TypeScript compilation to `dist/`

### packages/desktop-agent
- **Purpose**: Desktop agent for monitoring desktop AI applications
- **Key files**: `src/index.ts`
- **Build**: TypeScript compilation to `dist/`

### packages/cli-interceptor
- **Purpose**: CLI interceptor for command-line AI tools
- **Key files**: 
  - `src/cli.ts` - CLI interface
  - `src/index.ts` - Main interceptor logic
- **Build**: TypeScript compilation to `dist/`

### packages/dashboard
- **Purpose**: React-based web dashboard for analytics and configuration
- **Key files**:
  - `src/main.tsx` - Application entry point
  - `src/App.tsx` - Root component
  - `index.html` - HTML template
  - `vite.config.ts` - Vite configuration
- **Build**: Vite build to `dist/`
- **Dev server**: Vite dev server

### packages/backend
- **Purpose**: FastAPI backend for log ingestion and API
- **Structure**:
  - `app/` - Python application package
    - `__init__.py` - Package initialization
    - `main.py` - FastAPI application entry point
    - `models.py` - Database models
  - `requirements.txt` - Python dependencies
  - `pyproject.toml` - Python project configuration
- **No build step**: Python runs directly

## Architecture Patterns

### Cross-package Dependencies
- All TypeScript packages depend on `@ai-firewall/shared` for type definitions
- Use TypeScript project references for type checking across packages
- Backend defines its own Pydantic models (Python equivalent of TypeScript types)

### Data Flow
1. Client agents (browser/desktop/CLI) detect AI tool usage
2. Agents classify prompts locally using on-device ML models
3. Agents send anonymized logs to backend API
4. Backend stores logs in PostgreSQL
5. Dashboard queries backend API for analytics and configuration

### Privacy Architecture
- Sensitive data analysis happens entirely on the client side
- Only metadata and classification results are sent to the backend
- Actual prompt content is never transmitted or stored centrally

## File Naming Conventions

- TypeScript files: camelCase (e.g., `background.ts`, `main.tsx`)
- Python files: snake_case (e.g., `main.py`, `models.py`)
- Config files: kebab-case or standard names (e.g., `tsconfig.json`, `vite.config.ts`)

## Build Outputs

All packages build to a `dist/` directory:
- TypeScript packages: Compiled JavaScript in `dist/`
- Dashboard: Vite production build in `dist/`
- Backend: No build output (Python runs directly)
