# Database Setup Guide

This guide covers the database schema, migrations, and retention policy for the AI Usage Firewall backend.

## Overview

The backend uses PostgreSQL as the primary database with SQLAlchemy ORM and Alembic for migrations.

## Database Schema

The schema includes four main tables:

### 1. users
Stores user authentication and profile information.

**Columns:**
- `id` (UUID, PK): Unique user identifier
- `username` (String, unique): Username for login
- `email` (String, unique): User email address
- `hashed_password` (String): Bcrypt hashed password
- `full_name` (String, nullable): User's full name
- `is_active` (Boolean): Whether the user account is active
- `is_admin` (Boolean): Whether the user has admin privileges
- `created_at` (DateTime): Account creation timestamp
- `last_login` (DateTime, nullable): Last login timestamp

**Indexes:**
- `ix_users_username` on `username`
- `ix_users_email` on `email`

### 2. devices
Stores registered client devices (browser extensions, desktop agents, CLI interceptors).

**Columns:**
- `id` (UUID, PK): Unique device identifier
- `device_id` (String, unique): Client-generated device ID
- `user_id` (String): Associated user ID
- `device_type` (String): Type of device (browser/desktop/cli)
- `registered_at` (DateTime): Device registration timestamp
- `last_seen` (DateTime): Last activity timestamp
- `is_active` (Boolean): Whether the device is active

**Indexes:**
- `ix_devices_device_id` on `device_id`
- `ix_devices_user_id` on `user_id`

### 3. firewall_configs
Stores organization-level firewall configuration.

**Columns:**
- `id` (UUID, PK): Unique config identifier
- `organization_id` (String, unique): Organization identifier
- `monitored_tools` (JSON): List of monitored AI tools with enable/disable flags
- `sensitivity_thresholds` (JSON): Risk classification thresholds
- `custom_patterns` (JSON): Custom regex patterns for sensitive data detection
- `log_retention_days` (Integer): Number of days to retain logs (30-365)
- `updated_at` (DateTime): Last update timestamp
- `updated_by` (String): User who last updated the config

**Indexes:**
- `ix_firewall_configs_organization_id` on `organization_id`

### 4. log_entries
Stores AI tool usage logs (metadata only, no prompt content).

**Columns:**
- `id` (UUID, PK): Unique log entry identifier
- `timestamp` (DateTime): When the interaction occurred
- `device_id` (String): Device that generated the log
- `user_id` (String): User who made the interaction
- `tool_name` (String): AI tool name (e.g., "ChatGPT", "Claude")
- `tool_type` (String): Tool type (web/desktop/cli)
- `risk_level` (String): Risk classification (green/amber/red)
- `prompt_length` (Integer): Character count of the prompt
- `detected_entity_types` (JSON): Types of sensitive data detected
- `entity_count` (Integer): Number of sensitive entities found
- `was_sanitized` (Boolean): Whether user used sanitized version
- `log_metadata` (JSON): Additional metadata (browser version, OS, etc.)
- `created_at` (DateTime): Log creation timestamp

**Indexes:**
- `ix_log_entries_timestamp` on `timestamp`
- `ix_log_entries_device_id` on `device_id`
- `ix_log_entries_user_id` on `user_id`
- `ix_log_entries_tool_name` on `tool_name`
- `ix_log_entries_risk_level` on `risk_level`
- `idx_timestamp_risk` on `(timestamp, risk_level)` (composite)
- `idx_user_timestamp` on `(user_id, timestamp)` (composite)
- `idx_tool_timestamp` on `(tool_name, timestamp)` (composite)

## Database Migrations

### Setup

Alembic is configured and ready to use. See `alembic/README.md` for detailed instructions.

### Running Migrations

```bash
# Apply all pending migrations
cd packages/backend
alembic upgrade head

# Rollback the last migration
alembic downgrade -1

# View migration history
alembic history

# View current version
alembic current
```

### Creating New Migrations

```bash
# Auto-generate from model changes (requires database connection)
alembic revision --autogenerate -m "Description"

# Create empty migration
alembic revision -m "Description"
```

## Log Retention Policy

The system automatically deletes logs older than the configured retention period for each organization.

### Configuration

- Default retention: 90 days
- Configurable range: 30-365 days
- Set per organization in `firewall_configs.log_retention_days`

### Cleanup Methods

#### 1. Background Scheduler (Recommended for Production)

Enable automatic cleanup by setting environment variables:

```bash
export ENABLE_RETENTION_SCHEDULER=true
export RETENTION_CLEANUP_INTERVAL_HOURS=24  # Optional, defaults to 24
```

The scheduler runs automatically when the FastAPI application starts.

#### 2. Manual API Trigger

```bash
# Clean up for specific organization
curl -X POST "http://localhost:8000/api/v1/admin/cleanup-logs?organization_id=default"

# Clean up for all organizations
curl -X POST "http://localhost:8000/api/v1/admin/cleanup-logs/all"
```

#### 3. Cron Job (Recommended for Separate Process)

```bash
# Add to crontab (run daily at 2 AM)
0 2 * * * cd /path/to/packages/backend && python cleanup_logs.py >> /var/log/ai-firewall-cleanup.log 2>&1

# Or run manually
python cleanup_logs.py
```

### Implementation Files

- `app/retention.py`: Core retention logic
- `app/scheduler.py`: Background scheduler
- `app/routers/admin.py`: Admin API endpoints
- `cleanup_logs.py`: Standalone CLI script

See `RETENTION_POLICY.md` for detailed documentation.

## Environment Variables

- `DATABASE_URL`: PostgreSQL connection string
  - Default: `postgresql+asyncpg://postgres:@localhost:5432/ai_firewall`
  - Format: `postgresql+asyncpg://user:password@host:port/database`

- `ENABLE_RETENTION_SCHEDULER`: Enable automatic log cleanup
  - Default: `false`
  - Values: `true` or `false`

- `RETENTION_CLEANUP_INTERVAL_HOURS`: Cleanup interval in hours
  - Default: `24`
  - Recommended: `24` (daily)

## Initial Setup

1. **Install dependencies:**
   ```bash
   cd packages/backend
   pip install -r requirements.txt
   ```

2. **Set database URL:**
   ```bash
   export DATABASE_URL="postgresql+asyncpg://user:password@localhost:5432/ai_firewall"
   ```

3. **Run migrations:**
   ```bash
   alembic upgrade head
   ```

4. **Start the application:**
   ```bash
   uvicorn app.main:app --reload
   ```

5. **(Optional) Enable retention scheduler:**
   ```bash
   export ENABLE_RETENTION_SCHEDULER=true
   uvicorn app.main:app --reload
   ```

## Troubleshooting

### Migration Issues

- **Error: "No module named 'psycopg2'"**
  - Solution: `pip install psycopg2-binary`

- **Error: "connection refused"**
  - Ensure PostgreSQL is running
  - Verify DATABASE_URL is correct
  - Check PostgreSQL is accepting connections

### Retention Policy Issues

- **Cleanup not running**
  - Check `ENABLE_RETENTION_SCHEDULER` is set to `true`
  - Verify database connection
  - Check application logs for errors

- **Too many logs deleted**
  - Verify `log_retention_days` in firewall_configs
  - Check cleanup logs for cutoff date

## Security Considerations

1. **No Prompt Content**: The database never stores actual prompt content, only metadata
2. **Password Hashing**: User passwords are hashed with bcrypt
3. **Connection Security**: Use SSL/TLS for database connections in production
4. **Access Control**: Implement proper authentication for admin endpoints
5. **Backup**: Regular database backups recommended before running cleanup

## Performance Optimization

1. **Indexes**: All frequently queried columns have indexes
2. **Composite Indexes**: Common query patterns have composite indexes
3. **Cleanup Timing**: Run retention cleanup during off-peak hours
4. **Connection Pooling**: Configured with 20 connections, 10 overflow
5. **Async Operations**: All database operations are async for better performance
