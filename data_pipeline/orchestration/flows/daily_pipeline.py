"""Main daily pipeline flow for NZ Habitat Intelligence."""

import logging
import sys
from datetime import datetime
from pathlib import Path

from prefect import flow, get_run_logger

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
from data_pipeline.orchestration.tasks.silver_tasks import (  # noqa: E402
    compute_affordability,
    compute_interest_rate_lag,
    compute_tourism_pressure,
    compute_supply_deficit,
    compute_rent_income_ratio,
    compute_macro_volatility,
)
from data_pipeline.orchestration.tasks.dbt_tasks import (  # noqa: E402
    dbt_seed_task,
    dbt_run_task,
    dbt_test_task,
)
from data_pipeline.orchestration.tasks.ge_tasks import (  # noqa: E402
    validate_bronze_layer,
    validate_silver_layer,
    validate_gold_layer,
)

logger = logging.getLogger(__name__)


@flow(
    name="nz-habitat-daily-pipeline",
    log_prints=True,
    description="Complete daily pipeline: bronze -> silver -> dbt -> GE validation",
)
def run_daily_pipeline(force_refresh: bool = False) -> dict:
    """Run the complete daily data pipeline.

    Execution order:
    1. Bronze: All 6 ingestors run in parallel
    2. Silver: All 6 feature computations run in parallel (after bronze)
    3. dbt: seed -> run -> test (sequential, after silver)
    4. GE: All 3 layer validations run in parallel (after dbt)

    Args:
        force_refresh: Skip bronze cache and fetch fresh data.

    Returns:
        Dictionary with pipeline results per stage.
    """
    run_logger = get_run_logger()
    run_logger.info("=" * 60)
    run_logger.info("NZ HABITAT INTELLIGENCE - DAILY PIPELINE")
    run_logger.info("=" * 60)
    run_logger.info("force_refresh=%s", force_refresh)

    results = {"start_time": datetime.now().isoformat(), "stages": {}}

    # ── Stage 1: Bronze (parallel ingestors) ──────────────────────────
    run_logger.info("STAGE 1: Bronze Layer Ingestion (parallel)")
    bronze_futures = [
        ingest_world_bank.submit(force_refresh=force_refresh),
        ingest_rbnz.submit(force_refresh=force_refresh),
        ingest_stats_nz.submit(force_refresh=force_refresh),
        ingest_mbie_tourism.submit(force_refresh=force_refresh),
        ingest_linz.submit(force_refresh=force_refresh),
        ingest_reinz.submit(force_refresh=force_refresh),
    ]
    bronze_results = [f.result() for f in bronze_futures]
    bronze_success = all(
        r.get("result", {}).get("success", False) for r in bronze_results
    )
    results["stages"]["bronze"] = {
        "success": bronze_success,
        "sources": [r["source"] for r in bronze_results],
        "details": bronze_results,
    }
    run_logger.info(
        "Bronze stage: %s", "SUCCESS" if bronze_success else "PARTIAL/FAILED"
    )

    if not bronze_success:
        run_logger.warning("Some bronze ingestors failed, continuing pipeline...")

    # ── Stage 2: Silver (parallel features, wait for bronze) ──────────
    run_logger.info("STAGE 2: Silver Layer Feature Engineering (parallel)")
    silver_futures = [
        compute_affordability.submit(wait_for=bronze_futures),
        compute_interest_rate_lag.submit(wait_for=bronze_futures),
        compute_tourism_pressure.submit(wait_for=bronze_futures),
        compute_supply_deficit.submit(wait_for=bronze_futures),
        compute_rent_income_ratio.submit(wait_for=bronze_futures),
        compute_macro_volatility.submit(wait_for=bronze_futures),
    ]
    silver_results = [f.result() for f in silver_futures]
    silver_success_count = sum(1 for r in silver_results if r.get("success"))
    silver_success = silver_success_count > 0
    results["stages"]["silver"] = {
        "success": silver_success,
        "features_created": silver_success_count,
        "details": silver_results,
    }
    run_logger.info(
        "Silver stage: %d/%d features created",
        silver_success_count,
        len(silver_results),
    )

    # ── Stage 3: dbt (sequential: seed -> run -> test) ────────────────
    run_logger.info("STAGE 3: dbt Gold Layer Transformations (sequential)")
    seed_result = dbt_seed_task.submit(wait_for=silver_futures).result()
    run_result = dbt_run_task.submit(wait_for=[seed_result]).result()
    test_result = dbt_test_task.submit(wait_for=[run_result]).result()

    dbt_success = all(
        [
            seed_result.get("success", False),
            run_result.get("success", False),
            test_result.get("success", False),
        ]
    )
    results["stages"]["dbt"] = {
        "success": dbt_success,
        "seed": seed_result,
        "run": run_result,
        "test": test_result,
    }
    run_logger.info("dbt stage: %s", "SUCCESS" if dbt_success else "FAILED")

    # ── Stage 4: GE Validation (parallel per layer) ───────────────────
    run_logger.info("STAGE 4: Great Expectations Validation (parallel)")
    ge_futures = [
        validate_bronze_layer.submit(),
        validate_silver_layer.submit(),
        validate_gold_layer.submit(),
    ]
    ge_results = [f.result() for f in ge_futures]
    ge_success = all(r.get("success", False) for r in ge_results)
    results["stages"]["ge_validation"] = {
        "success": ge_success,
        "details": ge_results,
    }
    run_logger.info("GE validation: %s", "SUCCESS" if ge_success else "FAILED")

    # ── Overall result ────────────────────────────────────────────────
    results["end_time"] = datetime.now().isoformat()
    results["overall_success"] = all(
        [
            bronze_success,
            silver_success,
            dbt_success,
            ge_success,
        ]
    )

    run_logger.info("=" * 60)
    run_logger.info("PIPELINE COMPLETE")
    for stage, result in results["stages"].items():
        status = "SUCCESS" if result.get("success") else "FAILED"
        run_logger.info("  %s: %s", stage, status)
    run_logger.info(
        "Overall: %s", "SUCCESS" if results["overall_success"] else "FAILED"
    )
    run_logger.info("=" * 60)

    return results


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="NZ Habitat Daily Pipeline (Prefect)")
    parser.add_argument(
        "--force", action="store_true", help="Force refresh bronze data"
    )
    args = parser.parse_args()

    result = run_daily_pipeline(force_refresh=args.force)
    sys.exit(0 if result.get("overall_success") else 1)
