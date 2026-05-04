"""dbt transformation tasks for Prefect orchestration."""

import logging
import sys
from datetime import datetime
from pathlib import Path

from prefect import task

project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from data_pipeline.dbt_runner import run_dbt_seed, run_dbt_run, run_dbt_test  # noqa: E402
from data_pipeline.orchestration.config.settings import RETRY_CONFIG  # noqa: E402

logger = logging.getLogger(__name__)

retry_cfg = RETRY_CONFIG["dbt"]


@task(
    name="dbt-seed",
    retries=retry_cfg["retries"],
    retry_delay_seconds=retry_cfg["retry_delay_seconds"],
    log_prints=True,
)
def dbt_seed_task() -> dict:
    """Load dbt seed data (nz_regions reference table)."""
    print(f"[{datetime.now().isoformat()}] Running dbt seed...")
    result = run_dbt_seed()
    status = "SUCCESS" if result.get("success") else "FAILED"
    print(f"dbt seed: {status}")
    if result.get("stderr"):
        print(f"  stderr: {result['stderr'][:500]}")
    return {"step": "seed", "success": result.get("success", False), "details": result}


@task(
    name="dbt-run",
    retries=retry_cfg["retries"],
    retry_delay_seconds=retry_cfg["retry_delay_seconds"],
    log_prints=True,
)
def dbt_run_task(full_refresh: bool = False, models: str = None) -> dict:
    """Run dbt models (Silver->Gold transformations)."""
    print(f"[{datetime.now().isoformat()}] Running dbt models...")
    result = run_dbt_run(models=models, full_refresh=full_refresh)
    status = "SUCCESS" if result.get("success") else "FAILED"
    print(f"dbt run: {status}")
    if result.get("stderr"):
        print(f"  stderr: {result['stderr'][:500]}")
    return {"step": "run", "success": result.get("success", False), "details": result}


@task(
    name="dbt-test",
    retries=retry_cfg["retries"],
    retry_delay_seconds=retry_cfg["retry_delay_seconds"],
    log_prints=True,
)
def dbt_test_task(models: str = None) -> dict:
    """Run dbt tests on models."""
    print(f"[{datetime.now().isoformat()}] Running dbt tests...")
    result = run_dbt_test(models=models)
    status = "SUCCESS" if result.get("success") else "FAILED"
    print(f"dbt test: {status}")
    if result.get("stderr"):
        print(f"  stderr: {result['stderr'][:500]}")
    return {"step": "test", "success": result.get("success", False), "details": result}
