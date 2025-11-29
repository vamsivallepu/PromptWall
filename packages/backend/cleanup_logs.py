#!/usr/bin/env python3
"""
CLI script for running log retention cleanup.

This script can be run manually or scheduled with cron.

Usage:
    python cleanup_logs.py

Example cron entry (run daily at 2 AM):
    0 2 * * * cd /path/to/packages/backend && python cleanup_logs.py
"""
import asyncio
import sys
import logging

from app.scheduler import run_retention_cleanup


def main():
    """Main entry point for the cleanup script"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        asyncio.run(run_retention_cleanup())
        print("Log retention cleanup completed successfully")
        sys.exit(0)
    except Exception as e:
        print(f"Error during log retention cleanup: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
