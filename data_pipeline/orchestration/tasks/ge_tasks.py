"""Great Expectations validation tasks for Prefect orchestration."""
import logging
import sys
from datetime import datetime
from pathlib import Path

from prefect import task

project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from great_expectations.validate import NZHabitatValidator  # noqa: E402
from data_pipeline.orchestration.config.settings import RETRY_CONFIG  # noqa: E402

logger = logging.getLogger(__name__)

retry_cfg = RETRY_CONFIG["ge"]


@task(
    name="validate-bronze",
    retries=retry_cfg["retries"],
    retry_delay_seconds=retry_cfg["retry_delay_seconds"],
    log_prints=True,
)
def validate_bronze_layer() -> dict:
    """Validate bronze layer JSON files against expectations."""
    print(f"[{datetime.now().isoformat()}] Validating bronze layer...")
    validator = NZHabitatValidator(str(project_root))
    results = validator.validate_bronze_layer()
    passed = sum(1 for r in results if r.get("success"))
    total = len(results)
    print(f"Bronze validation: {passed}/{total} passed")
    return {"layer": "bronze", "passed": passed, "total": total, "success": passed == total, "details": results}


@task(
    name="validate-silver",
    retries=retry_cfg["retries"],
    retry_delay_seconds=retry_cfg["retry_delay_seconds"],
    log_prints=True,
)
def validate_silver_layer() -> dict:
    """Validate silver layer parquet files against expectations."""
    print(f"[{datetime.now().isoformat()}] Validating silver layer...")
    validator = NZHabitatValidator(str(project_root))
    results = validator.validate_silver_layer()
    passed = sum(1 for r in results if r.get("success"))
    total = len(results)
    print(f"Silver validation: {passed}/{total} passed")
    return {"layer": "silver", "passed": passed, "total": total, "success": passed == total, "details": results}


@task(
    name="validate-gold",
    retries=retry_cfg["retries"],
    retry_delay_seconds=retry_cfg["retry_delay_seconds"],
    log_prints=True,
)
def validate_gold_layer() -> dict:
    """Validate gold layer KPI parquet files against expectations."""
    print(f"[{datetime.now().isoformat()}] Validating gold layer...")
    validator = NZHabitatValidator(str(project_root))
    results = validator.validate_gold_layer()
    passed = sum(1 for r in results if r.get("success"))
    total = len(results)
    print(f"Gold validation: {passed}/{total} passed")
    return {"layer": "gold", "passed": passed, "total": total, "success": passed == total, "details": results}
