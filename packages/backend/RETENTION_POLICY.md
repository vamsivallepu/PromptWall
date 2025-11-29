# Log Retention Policy

The AI Usage Firewall implements automatic log retention to manage database size and comply with data retention policies.

## How It Works

Logs older than the configured retention period are automatically deleted. Each organization can configure its own retention period between 30 and 365 days.

## Configuration

The retention period is configured per organization in the `firewall_configs` table via the `log_retention_days` field.

Default retention period: **90 days**

## Cleanup Methods

### 1. Automatic Background Scheduler (Recommended for Production)

Enable the background scheduler by setting environment variables:

```bash
export ENABLE_RETENTION_SCHEDULER=true
export RETENTION_CLEANUP_INTERVAL_HOURS=24  # Optional, defaults to 24
```

The scheduler runs automatically when the FastAPI application starts and executes cleanup at the specified interval.

### 2. Manual API Trigger

Use the admin API endpoints to manually trigger cleanup:

```bash
# Clean up logs for a specific organization
curl -X POST "http://localhost:8000/api/v1/admin/cleanup-logs?organization_id=default"

# Clean up logs for all organizations
curl -X POST "http://localhost:8000/api/v1/admin/cleanup-logs/all"
```

### 3. Cron Job (Recommended for Separate Cleanup Process)

Schedule the cleanup script to run periodically using cron:

```bash
# Edit crontab
crontab -e

# Add entry to run daily at 2 AM
0 2 * * * cd /path/to/packages/backend && /path/to/python cleanup_logs.py >> /var/log/ai-firewall-cleanup.log 2>&1
```

Or run manually:

```bash
cd packages/backend
python cleanup_logs.py
```

## Monitoring

The cleanup process logs the following information:

- Number of logs deleted per organization
- Total logs deleted
- Cutoff date used for deletion
- Any errors encountered

Check application logs for cleanup activity:

```bash
# If using the background scheduler
tail -f /var/log/ai-firewall.log | grep retention

# If using cron
tail -f /var/log/ai-firewall-cleanup.log
```

## Best Practices

1. **Production**: Use the background scheduler or cron job, not manual API triggers
2. **Testing**: Use manual API triggers to test retention policy
3. **Monitoring**: Set up alerts for cleanup failures
4. **Backup**: Consider backing up logs before deletion if required for compliance
5. **Retention Period**: Set retention period based on:
   - Regulatory requirements
   - Storage capacity
   - Audit needs

## Database Impact

The cleanup process:

- Uses efficient DELETE queries with timestamp filtering
- Runs in a transaction (can be rolled back on error)
- Uses existing indexes on the `timestamp` column for performance
- Minimal impact on database performance when run during off-peak hours

## Troubleshooting

### Cleanup not running

1. Check environment variables are set correctly
2. Verify database connection is working
3. Check application logs for errors
4. Ensure the organization has a valid configuration

### Too many logs being deleted

1. Verify the `log_retention_days` configuration
2. Check the cutoff date in logs
3. Review the organization's retention policy

### Cleanup taking too long

1. Run cleanup during off-peak hours
2. Consider increasing the cleanup interval
3. Check database indexes are present
4. Monitor database performance during cleanup
