# Technology Stack

## Build System

- **Monorepo**: npm workspaces managing multiple packages
- **TypeScript**: Strict mode enabled, ES2020 target
- **Project references**: TypeScript project references for cross-package dependencies

## Frontend Stack

- **React 18**: UI framework for dashboard
- **Vite**: Build tool and dev server for dashboard
- **TypeScript**: All frontend code is strongly typed
- **Browser Extension**: Chrome extension APIs with TypeScript

## Backend Stack

- **FastAPI**: Python web framework (v0.109.0)
- **Uvicorn**: ASGI server for FastAPI
- **Pydantic**: Data validation and settings management (v2.5.3)
- **SQLAlchemy**: ORM for database operations (v2.0.25)
- **Alembic**: Database migrations
- **PostgreSQL**: Primary database (v14+)
- **AsyncPG**: Async PostgreSQL driver

## ML/NLP Libraries

- **GLiNER**: Entity recognition for detecting sensitive data (v0.1.12)
- **PyTorch**: ML framework (v2.1.2)
- **Transformers**: Hugging Face transformers (v4.36.2)

## Security & Rate Limiting

- **python-jose**: JWT token handling
- **passlib**: Password hashing with bcrypt
- **slowapi**: Rate limiting middleware

## Prerequisites

- Node.js 18+
- Python 3.10+
- PostgreSQL 14+

## Common Commands

### Installation
```bash
# Install all Node.js dependencies
npm install

# Install Python backend dependencies
cd packages/backend
pip install -r requirements.txt
```

### Development
```bash
# Run all packages in dev mode
npm run dev

# Run backend dev server
cd packages/backend
uvicorn app.main:app --reload

# Run individual package dev mode
cd packages/<package-name>
npm run dev
```

### Building
```bash
# Build all packages
npm run build

# Build specific package
cd packages/<package-name>
npm run build
```

### Testing
```bash
# Run all tests
npm run test

# Backend tests (when implemented)
cd packages/backend
pytest
```

## Package Naming Convention

All packages use the `@ai-firewall/` scope:
- `@ai-firewall/shared`
- `@ai-firewall/browser-extension`
- `@ai-firewall/desktop-agent`
- `@ai-firewall/cli-interceptor`
- `@ai-firewall/dashboard`
