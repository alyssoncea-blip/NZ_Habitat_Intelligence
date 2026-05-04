"""Scheduled ingestion flows for NZ Habitat Intelligence."""
import sys
from pathlib import Path

from prefect import flow, get_run_logger
from prefect.schedules import CronSchedule

project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from data_pipeline.orchestration.tasks.bronze_tasks import (  # noqa: E402
    ingest_world_bank,
    ingest_rbnz,
    ingest_stats_nz,
    ingest_mbie_tourism,
    ingest_linz,
    ingest_reinz,
)


@flow(
    name="nz-habitat-daily-ingestion",
    log_prints=True,
    description="Daily ingestion: World Bank + REINZ",
)
def run_daily_ingestion(force_refresh: bool = False) -> dict:
    """Run daily scheduled ingestion (World Bank, REINZ)."""
    run_logger = get_run_logger()
    run_logger.info("Running daily ingestion schedule...")

    futures = [
        ingest_world_bank.submit(force_refresh=force_refresh),
        ingest_reinz.submit(force_refresh=force_refresh),
    ]
    results = [f.result() for f in futures]
    success = all(r.get("result", {}).get("success", False) for r in results)

    run_logger.info("Daily ingestion: %s", "SUCCESS" if success else "FAILED")
    return {"schedule": "daily", "success": success, "results": results}


daily_ingestion_schedule = CronSchedule(
    cron="0 6 * * *",
    timezone="UTC",
)


@flow(
    name="nz-habitat-weekly-ingestion",
    log_prints=True,
    description="Weekly ingestion: RBNZ + Stats NZ + MBIE Tourism",
)
def run_weekly_ingestion(force_refresh: bool = False) -> dict:
    """Run weekly scheduled ingestion (RBNZ, Stats NZ, MBIE Tourism)."""
    run_logger = get_run_logger()
    run_logger.info("Running weekly ingestion schedule...")

    futures = [
        ingest_rbnz.submit(force_refresh=force_refresh),
        ingest_stats_nz.submit(force_refresh=force_refresh),
        ingest_mbie_tourism.submit(force_refresh=force_refresh),
    ]
    results = [f.result() for f in futures]
    success = all(r.get("result", {}).get("success", False) for r in results)

    run_logger.info("Weekly ingestion: %s", "SUCCESS" if success else "FAILED")
    return {"schedule": "weekly", "success": success, "results": results}


weekly_ingestion_schedule = CronSchedule(
    cron="0 8 * * 1",
    timezone="UTC",
)


@flow(
    name="nz-habitat-monthly-ingestion",
    log_prints=True,
    description="Monthly ingestion: LINZ",
)
def run_monthly_ingestion(force_refresh: bool = False) -> dict:
    """Run monthly scheduled ingestion (LINZ)."""
    run_logger = get_run_logger()
    run_logger.info("Running monthly ingestion schedule...")

    futures = [
        ingest_linz.submit(force_refresh=force_refresh),
    ]
    results = [f.result() for f in futures]
    success = all(r.get("result", {}).get("success", False) for r in results)

    run_logger.info("Monthly ingestion: %s", "SUCCESS" if success else "FAILED")
    return {"schedule": "monthly", "success": success, "results": results}


monthly_ingestion_schedule = CronSchedule(
    cron="0 10 1 * *",
    timezone="UTC",
)


@flow(
    name="nz-habitat-full-pipeline",
    log_prints=True,
    description="Full pipeline with all stages (runs after daily ingestion)",
)
def run_full_pipeline(force_refresh: bool = False) -> dict:
    """Run the full pipeline (imports and delegates to daily_pipeline flow)."""
    from data_pipeline.orchestration.flows.daily_pipeline import run_daily_pipeline
    return run_daily_pipeline(force_refresh=force_refresh)


full_pipeline_schedule = CronSchedule(
    cron="0 7 * * *",
    timezone="UTC",
)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Scheduled Ingestion Flows")
    parser.add_argument(
        "schedule",
        choices=["daily", "weekly", "monthly", "full"],
        default="daily",
        nargs="?",
    )
    parser.add_argument("--force", action="store_true", help="Force refresh")
    args = parser.parse_args()

    flows_map = {
        "daily": run_daily_ingestion,
        "weekly": run_weekly_ingestion,
        "monthly": run_monthly_ingestion,
        "full": run_full_pipeline,
    }

    result = flows_map[args.schedule](force_refresh=args.force)
    sys.exit(0 if result.get("success") else 1)
