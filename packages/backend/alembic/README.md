# Database Migrations

This directory contains Alembic database migrations for the AI Usage Firewall backend.

## Setup

Alembic is already configured and ready to use. The database URL is read from the `DATABASE_URL` environment variable, which defaults to:

```
postgresql+asyncpg://postgres:postgres@localhost:5432/ai_firewall
```

## Running Migrations

### Apply all pending migrations

```bash
cd packages/backend
alembic upgrade head
```

### Rollback the last migration

```bash
alembic downgrade -1
```

### View migration history

```bash
alembic history
```

### View current migration version

```bash
alembic current
```

## Creating New Migrations

### Auto-generate a migration from model changes

```bash
alembic revision --autogenerate -m "Description of changes"
```

Note: Auto-generation requires a database connection. Review the generated migration before applying it.

### Create an empty migration

```bash
alembic revision -m "Description of changes"
```

## Environment Variables

- `DATABASE_URL`: PostgreSQL connection string (default: `postgresql+asyncpg://postgres:postgres@localhost:5432/ai_firewall`)

Note: Alembic automatically converts `postgresql+asyncpg://` to `postgresql://` for compatibility with psycopg2.

## Initial Migration

The initial migration (`774dd005f330_initial_migration_with_all_tables.py`) creates:

- `users` table: User authentication and profile data
- `devices` table: Registered client devices
- `firewall_configs` table: Organization firewall configuration
- `log_entries` table: AI tool usage logs with indexes for efficient querying

All tables include appropriate indexes for query performance.
