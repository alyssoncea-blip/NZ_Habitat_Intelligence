"""Silver layer feature engineering tasks for Prefect orchestration."""

import logging
import sys
from datetime import datetime
from pathlib import Path

from prefect import task

project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from data_pipeline.silver.feature_engineer import FeatureEngineer  # noqa: E402
from data_pipeline.orchestration.config.settings import RETRY_CONFIG  # noqa: E402

logger = logging.getLogger(__name__)

retry_cfg = RETRY_CONFIG["silver"]


@task(
    name="compute-affordability",
    retries=retry_cfg["retries"],
    retry_delay_seconds=retry_cfg["retry_delay_seconds"],
    log_prints=True,
)
def compute_affordability() -> dict:
    """Compute affordability features (GDP per capita + regional income ratios)."""
    print(f"[{datetime.now().isoformat()}] Computing affordability features...")
    engineer = FeatureEngineer()
    bronze_data = engineer.load_bronze_data()
    df = engineer._calc_affordability(bronze_data)
    if df is not None and not df.empty:
        output = engineer.silver_dir / "affordability_features.parquet"
        df.to_parquet(output, index=False)
        print(f"Affordability features: {len(df)} rows -> {output}")
        return {
            "feature": "affordability",
            "rows": len(df),
            "file": str(output),
            "success": True,
        }
    print("Affordability features: no data generated")
    return {"feature": "affordability", "rows": 0, "success": False}


@task(
    name="compute-interest-rate-lag",
    retries=retry_cfg["retries"],
    retry_delay_seconds=retry_cfg["retry_delay_seconds"],
    log_prints=True,
)
def compute_interest_rate_lag() -> dict:
    """Compute interest rate lag features (OCR + volatility)."""
    print(f"[{datetime.now().isoformat()}] Computing interest rate lag features...")
    engineer = FeatureEngineer()
    bronze_data = engineer.load_bronze_data()
    df = engineer._calc_interest_rate_lag(bronze_data)
    if df is not None and not df.empty:
        output = engineer.silver_dir / "interest_rate_lag_features.parquet"
        df.to_parquet(output, index=False)
        print(f"Interest rate lag features: {len(df)} rows -> {output}")
        return {
            "feature": "interest_rate_lag",
            "rows": len(df),
            "file": str(output),
            "success": True,
        }
    print("Interest rate lag features: no data generated")
    return {"feature": "interest_rate_lag", "rows": 0, "success": False}


@task(
    name="compute-tourism-pressure",
    retries=retry_cfg["retries"],
    retry_delay_seconds=retry_cfg["retry_delay_seconds"],
    log_prints=True,
)
def compute_tourism_pressure() -> dict:
    """Compute tourism pressure features (visitor arrivals + regional expenditure)."""
    print(f"[{datetime.now().isoformat()}] Computing tourism pressure features...")
    engineer = FeatureEngineer()
    bronze_data = engineer.load_bronze_data()
    df = engineer._calc_tourism_pressure(bronze_data)
    if df is not None and not df.empty:
        output = engineer.silver_dir / "tourism_pressure_features.parquet"
        df.to_parquet(output, index=False)
        print(f"Tourism pressure features: {len(df)} rows -> {output}")
        return {
            "feature": "tourism_pressure",
            "rows": len(df),
            "file": str(output),
            "success": True,
        }
    print("Tourism pressure features: no data generated")
    return {"feature": "tourism_pressure", "rows": 0, "success": False}


@task(
    name="compute-supply-deficit",
    retries=retry_cfg["retries"],
    retry_delay_seconds=retry_cfg["retry_delay_seconds"],
    log_prints=True,
)
def compute_supply_deficit() -> dict:
    """Compute supply deficit features (building consents vs population growth)."""
    print(f"[{datetime.now().isoformat()}] Computing supply deficit features...")
    engineer = FeatureEngineer()
    bronze_data = engineer.load_bronze_data()
    df = engineer._calc_supply_deficit(bronze_data)
    if df is not None and not df.empty:
        output = engineer.silver_dir / "supply_deficit_features.parquet"
        df.to_parquet(output, index=False)
        print(f"Supply deficit features: {len(df)} rows -> {output}")
        return {
            "feature": "supply_deficit",
            "rows": len(df),
            "file": str(output),
            "success": True,
        }
    print("Supply deficit features: no data generated")
    return {"feature": "supply_deficit", "rows": 0, "success": False}


@task(
    name="compute-rent-income-ratio",
    retries=retry_cfg["retries"],
    retry_delay_seconds=retry_cfg["retry_delay_seconds"],
    log_prints=True,
)
def compute_rent_income_ratio() -> dict:
    """Compute rent-to-income ratio features."""
    print(f"[{datetime.now().isoformat()}] Computing rent income ratio features...")
    engineer = FeatureEngineer()
    bronze_data = engineer.load_bronze_data()
    df = engineer._calc_rent_income_ratio(bronze_data)
    if df is not None and not df.empty:
        output = engineer.silver_dir / "rent_income_ratio_features.parquet"
        df.to_parquet(output, index=False)
        print(f"Rent income ratio features: {len(df)} rows -> {output}")
        return {
            "feature": "rent_income_ratio",
            "rows": len(df),
            "file": str(output),
            "success": True,
        }
    print("Rent income ratio features: no data generated")
    return {"feature": "rent_income_ratio", "rows": 0, "success": False}


@task(
    name="compute-tourism-lag-analysis",
    retries=retry_cfg["retries"],
    retry_delay_seconds=retry_cfg["retry_delay_seconds"],
    log_prints=True,
)
def compute_tourism_lag_analysis() -> dict:
    """Compute tourism lag analysis features (macroeconomic volatility composite index)."""
    print(f"[{datetime.now().isoformat()}] Computing tourism lag analysis features...")
    engineer = FeatureEngineer()
    bronze_data = engineer.load_bronze_data()
    df = engineer._calc_macro_volatility(bronze_data)
    if df is not None and not df.empty:
        output = engineer.silver_dir / "tourism_lag_analysis_features.parquet"
        df.to_parquet(output, index=False)
        print(f"Tourism lag analysis features: {len(df)} rows -> {output}")
        return {
            "feature": "tourism_lag_analysis",
            "rows": len(df),
            "file": str(output),
            "success": True,
        }
    print("Tourism lag analysis features: no data generated")
    return {"feature": "tourism_lag_analysis", "rows": 0, "success": False}
