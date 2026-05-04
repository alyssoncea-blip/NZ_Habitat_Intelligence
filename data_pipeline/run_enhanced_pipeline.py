"""Run pipeline with dbt + Great Expectations integration.

Canonical entry point for the NZ Habitat Intelligence data pipeline.
Runs: Bronze -> Silver -> dbt Gold -> GE validation -> Backtesting -> Catalog.

Can be executed directly or via Prefect orchestration.
"""

import logging
import sys
import importlib.util
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load custom GE validator directly to avoid namespace collision with great-expectations package
_ge_validate_path = project_root / "great_expectations" / "validate.py"
if _ge_validate_path.exists():
    _spec = importlib.util.spec_from_file_location("ge_validate", _ge_validate_path)
    _ge_module = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(_ge_module)
    NZHabitatValidator = _ge_module.NZHabitatValidator
else:
    NZHabitatValidator = None

from data_pipeline.bronze.bronze_orchestrator import BronzeOrchestrator
from data_pipeline.dbt_runner import run_full_pipeline as run_dbt_pipeline
from data_pipeline.utils.alert_manager import AlertManager, SLATracker

logger = logging.getLogger(__name__)


def run_enhanced_pipeline(force_refresh: bool = False) -> dict:
    """Run complete pipeline: bronze -> silver -> dbt gold -> GE validation.

    Args:
        force_refresh: Skip bronze cache and fetch fresh data.

    Returns:
        Dictionary with pipeline results per stage.
    """
    alerts = AlertManager()
    sla = SLATracker(alert_manager=alerts, max_duration_minutes=60)
    sla.start_pipeline()

    results = {
        "start_time": datetime.now().isoformat(),
        "stages": {},
        "overall_success": False,
    }

    # Stage 1: Bronze ingestion
    logger.info("=" * 60)
    logger.info("STAGE 1: Bronze Layer Ingestion")
    logger.info("=" * 60)
    sla.start_stage("bronze")

    orchestrator = BronzeOrchestrator()
    bronze_result = orchestrator.run_ingestor("all", force_refresh=force_refresh)
    results["stages"]["bronze"] = bronze_result
    sla.end_stage("bronze", success=bronze_result.get("success", False))

    if not bronze_result.get("success"):
        logger.error("Bronze ingestion failed. Aborting pipeline.")
        results["overall_success"] = False
        return results

    # Stage 2: Silver feature engineering
    logger.info("=" * 60)
    logger.info("STAGE 2: Silver Layer Feature Engineering")
    logger.info("=" * 60)
    sla.start_stage("silver")

    try:
        from data_pipeline.silver.feature_engineer import FeatureEngineer

        engineer = FeatureEngineer()
        bronze_data = engineer.load_bronze_data()

        silver_results = {}
        for name, calc_fn in [
            ("affordability", engineer._calc_affordability),
            ("interest_rate_lag", engineer._calc_interest_rate_lag),
            ("tourism_pressure", engineer._calc_tourism_pressure),
            ("supply_deficit", engineer._calc_supply_deficit),
            ("rent_income_ratio", engineer._calc_rent_income_ratio),
            ("tourism_lag_analysis", engineer._calc_macro_volatility),
        ]:
            try:
                df = calc_fn(bronze_data)
                if df is not None and not df.empty:
                    output = engineer.silver_dir / f"{name}_features.parquet"
                    df.to_parquet(output, index=False)
                    silver_results[name] = str(output)
                    logger.info("  Silver %s: %d rows -> %s", name, len(df), output)
            except Exception as e:
                logger.error("  Silver %s failed: %s", name, e)

        results["stages"]["silver"] = {
            "success": bool(silver_results),
            "features_created": len(silver_results),
            "files": silver_results,
        }
    except Exception as e:
        logger.error("Silver feature engineering failed: %s", e)
        results["stages"]["silver"] = {"success": False, "error": str(e)}

    sla.end_stage("silver", success=results["stages"]["silver"].get("success", False))

    # Stage 3: dbt Gold transformations
    logger.info("=" * 60)
    logger.info("STAGE 3: dbt Gold Layer Transformations")
    logger.info("=" * 60)
    sla.start_stage("dbt_gold")

    dbt_result = run_dbt_pipeline()
    results["stages"]["dbt_gold"] = {
        "success": all(v.get("success", False) for v in dbt_result.values()),
        "details": {k: v.get("success", False) for k, v in dbt_result.items()},
    }
    sla.end_stage("dbt_gold", success=results["stages"]["dbt_gold"]["success"])

    # Stage 3b: Python KPI calculator (dbt-first mode)
    # Reads dbt output as primary source, supplements with Python-only KPIs
    logger.info("=" * 60)
    logger.info("STAGE 3b: Python KPI Calculator (dbt-first reconciliation)")
    logger.info("=" * 60)
    sla.start_stage("kpi_calculator")

    try:
        from data_pipeline.gold.kpi_calculator import KPICalculator

        calc = KPICalculator()
        kpis = calc.calculate_all(use_dbt=True)
        results["stages"]["kpi_calculator"] = {
            "success": True,
            "dashboards": {name: len(df) for name, df in kpis.items()},
            "total_kpis": sum(len(df) for df in kpis.values()),
        }
        logger.info(
            "  KPI calculator complete: %d dashboards, %d total KPIs",
            len(kpis),
            sum(len(df) for df in kpis.values()),
        )
    except Exception as e:
        logger.error("  KPI calculator failed: %s", e)
        results["stages"]["kpi_calculator"] = {"success": False, "error": str(e)}

    sla.end_stage(
        "kpi_calculator",
        success=results["stages"]["kpi_calculator"].get("success", False),
    )

    # Stage 4: Great Expectations validation
    logger.info("=" * 60)
    logger.info("STAGE 4: Great Expectations Validation")
    logger.info("=" * 60)
    sla.start_stage("great_expectations")

    if NZHabitatValidator is None:
        logger.warning("  GE validator not available. Skipping validation.")
        results["stages"]["great_expectations"] = {"success": True, "skipped": True}
    else:
        validator = NZHabitatValidator(str(project_root))
        ge_results = validator.run_all_validations()
        validator.print_report(ge_results)

        results["stages"]["great_expectations"] = {
            "success": all(
                r.get("success", False)
                for layer in ["bronze", "silver", "gold"]
                for r in ge_results.get(layer, [])
            ),
            "summary": ge_results.get("summary", {}),
        }
    sla.end_stage(
        "great_expectations", success=results["stages"]["great_expectations"]["success"]
    )

    # Stage 5: Forecast backtesting
    logger.info("=" * 60)
    logger.info("STAGE 5: Forecast Backtesting (Walk-Forward Validation)")
    logger.info("=" * 60)

    try:
        from data_pipeline.gold.forecast_backtest import (
            backtest_from_features,
            format_backtest_report,
        )
        from data_pipeline.silver.feature_engineer import FeatureEngineer

        engineer = FeatureEngineer()
        features = engineer.run_all_feature_engineering()

        backtest = backtest_from_features(features, target_col="gdp_per_capita")
        report = format_backtest_report(backtest)
        logger.info(report)

        results["stages"]["backtesting"] = {
            "success": True,
            "mean_mape": backtest.mean_mape,
            "mean_rmse": backtest.mean_rmse,
            "mean_directional_accuracy": backtest.mean_directional_accuracy,
            "n_folds": backtest.n_folds,
        }
    except Exception as e:
        logger.error("  Backtesting failed: %s", e)
        results["stages"]["backtesting"] = {"success": False, "error": str(e)}

    # Stage 6: Data catalog generation
    logger.info("=" * 60)
    logger.info("STAGE 6: Data Catalog Generation")
    logger.info("=" * 60)

    try:
        from data_pipeline.utils.data_catalog import build_catalog

        catalog = build_catalog(str(project_root))
        catalog.export()
        catalog_report = catalog.generate_report()
        logger.info(catalog_report)

        results["stages"]["data_catalog"] = {
            "success": True,
            "total_datasets": len(catalog.entries),
            "catalog_path": str(project_root / "data_pipeline" / "catalog.json"),
        }
    except Exception as e:
        logger.error("  Data catalog generation failed: %s", e)
        results["stages"]["data_catalog"] = {"success": False, "error": str(e)}

    # Stage 7: Data quality report
    logger.info("=" * 60)
    logger.info("STAGE 7: Data Quality Report")
    logger.info("=" * 60)

    try:
        from data_pipeline.utils.quality_dashboard import run_quality_report

        quality_summary = run_quality_report(
            validations_dir=str(project_root / "great_expectations" / "validations"),
            output_path=str(
                project_root
                / "great_expectations"
                / "validations"
                / "quality_report.html"
            ),
        )
        results["stages"]["quality_report"] = {
            "success": True,
            "success_rate": quality_summary.get("success_rate", 0),
            "total_expectations": quality_summary.get("total_expectations", 0),
        }
    except Exception as e:
        logger.error("  Quality report generation failed: %s", e)
        results["stages"]["quality_report"] = {"success": False, "error": str(e)}

    # SLA check
    sla.check_total_duration()
    results["sla"] = sla.get_sla_report()
    results["alerts"] = alerts.get_summary()

    # Overall result
    results["overall_success"] = all(
        stage.get("success", False) for stage in results["stages"].values()
    )
    results["end_time"] = datetime.now().isoformat()

    return results


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    import argparse

    parser = argparse.ArgumentParser(description="Enhanced pipeline with dbt + GE")
    parser.add_argument(
        "--force", action="store_true", help="Force refresh bronze data"
    )
    args = parser.parse_args()

    results = run_enhanced_pipeline(force_refresh=args.force)

    print("\n" + "=" * 60)
    print("PIPELINE RESULT")
    print("=" * 60)
    for stage, result in results.get("stages", {}).items():
        status = "SUCCESS" if result.get("success") else "FAILED"
        print(f"  {stage}: {status}")
    print(f"\nOverall: {'SUCCESS' if results.get('overall_success') else 'FAILED'}")
    print("=" * 60)

    sys.exit(0 if results.get("overall_success") else 1)
