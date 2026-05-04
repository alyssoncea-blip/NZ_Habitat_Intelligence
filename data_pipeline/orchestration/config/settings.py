"""Configuration for Prefect orchestration."""

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
DATA_PIPELINE = PROJECT_ROOT / "data_pipeline"
BRONZE_DIR = DATA_PIPELINE / "bronze"
SILVER_DIR = DATA_PIPELINE / "silver"
GOLD_DIR = DATA_PIPELINE / "gold"
DBT_PROJECT_DIR = PROJECT_ROOT / "dbt_nz"
GE_DIR = PROJECT_ROOT / "great_expectations"

RETRY_CONFIG = {
    "bronze": {"retries": 3, "retry_delay_seconds": 60},
    "silver": {"retries": 2, "retry_delay_seconds": 30},
    "dbt": {"retries": 2, "retry_delay_seconds": 120},
    "ge": {"retries": 1, "retry_delay_seconds": 30},
}

SCHEDULES = {
    "daily_ingestion": {"cron": "0 6 * * *", "timezone": "UTC"},
    "weekly_ingestion": {"cron": "0 8 * * 1", "timezone": "UTC"},
    "monthly_ingestion": {"cron": "0 10 1 * *", "timezone": "UTC"},
    "full_pipeline": {"cron": "0 7 * * *", "timezone": "UTC"},
}

INGESTOR_SCHEDULE = {
    "daily": ["world_bank", "reinz"],
    "weekly": ["rbnz", "stats_nz", "mbie_tourism"],
    "monthly": ["linz"],
}

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
PREFECT_API_URL = os.getenv("PREFECT_API_URL", "")
SLACK_WEBHOOK_URL = os.getenv("ALERT_WEBHOOK_URL", "")
EMAIL_RECIPIENTS = os.getenv("ALERT_EMAIL_RECIPIENTS", "")
