"""Generate data contracts for Silver and Gold layer artifacts."""
import json
import logging
import os
import sys
from pathlib import Path

import pandas as pd

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_pipeline.utils.data_contract import (
    DataContract, DataQuality, DataSource, ColumnContract,
)

logger = logging.getLogger(__name__)

# Silver layer: feature sets produced by feature_engineer.py
SILVER_FEATURES = [
    ("affordability", "affordability_features.parquet", DataSource.PROXY, "World Bank + Stats NZ proxy"),
    ("interest_rate_lag", "interest_rate_lag_features.parquet", DataSource.PROXY, "World Bank interest rate lag features"),
    ("tourism_pressure", "tourism_pressure_features.parquet", DataSource.PROXY, "World Bank + MBIE tourism proxy"),
    ("supply_deficit", "supply_deficit_features.parquet", DataSource.PROXY, "World Bank + Stats NZ building consents proxy"),
    ("rent_income_ratio", "rent_income_ratio_features.parquet", DataSource.PROXY, "World Bank GDP/income proxy"),
    ("tourism_lag_analysis", "tourism_lag_analysis_features.parquet", DataSource.PROXY, "Tourism lag correlation features"),
]

# Gold layer: KPI parquet files
GOLD_KPIS = [
    ("01-executive_complete", "kpis-01-executive_complete.parquet", DataSource.PROXY, "Executive dashboard KPIs"),
    ("02-housing_complete", "kpis-02-housing_complete.parquet", DataSource.PROXY, "Housing dashboard KPIs"),
    ("03-tourism_complete", "kpis-03-tourism_complete.parquet", DataSource.PROXY, "Tourism dashboard KPIs"),
    ("04-macro_complete", "kpis-04-macro_complete.parquet", DataSource.PROXY, "Macro dashboard KPIs"),
    ("05-affordability_complete", "kpis-05-affordability_complete.parquet", DataSource.PROXY, "Affordability dashboard KPIs"),
    ("06-forecast_complete", "kpis-06-forecast_complete.parquet", DataSource.PROXY, "Forecast dashboard KPIs"),
]


def _analyze_dataframe(df: pd.DataFrame) -> dict:
    """Analyze a DataFrame for contract metadata."""
    columns = []
    total_nulls = 0
    total_cells = 0

    for col in df.columns:
        null_count = int(df[col].isnull().sum())
        unique_count = int(df[col].nunique())
        total_nulls += null_count
        total_cells += len(df)

        col_contract = ColumnContract(
            name=col,
            dtype=str(df[col].dtype),
            null_count=null_count,
            null_percentage=round(null_count / max(1, len(df)) * 100, 2),
            unique_count=unique_count,
        )

        # Add min/max for numeric columns
        if pd.api.types.is_numeric_dtype(df[col]):
            col_contract.min_value = float(df[col].min()) if not df[col].isnull().all() else None
            col_contract.max_value = float(df[col].max()) if not df[col].isnull().all() else None

        # Add sample values
        non_null = df[col].dropna()
        if len(non_null) > 0:
            col_contract.sample_values = [str(v) for v in non_null.head(3).tolist()]

        columns.append(col_contract)

    null_pct = round(total_nulls / max(1, total_cells) * 100, 2)
    return {
        "columns": columns,
        "null_pct": null_pct,
        "record_count": len(df),
        "column_count": len(df.columns),
    }


def generate_silver_contracts(silver_dir: str = "data_pipeline/silver") -> dict:
    """Generate contracts for Silver layer parquet files."""
    silver_path = Path(silver_dir)
    contracts = {}

    for name, filename, source, source_name in SILVER_FEATURES:
        filepath = silver_path / filename
        if not filepath.exists():
            logger.warning("Silver file not found: %s", filename)
            continue

        try:
            df = pd.read_parquet(filepath)
            analysis = _analyze_dataframe(df)

            null_pct = analysis["null_pct"]
            if null_pct < 5:
                quality = DataQuality.GOOD
            elif null_pct < 20:
                quality = DataQuality.FAIR
            else:
                quality = DataQuality.POOR

            contract = DataContract(
                artifact_name=f"silver_{name}",
                artifact_path=str(filepath),
                layer="silver",
                source=source,
                source_name=source_name,
                quality=quality,
                confidence_score=75.0,
                record_count=analysis["record_count"],
                column_count=analysis["column_count"],
                null_percentage=null_pct,
                columns=analysis["columns"],
                parent_contracts=[str(p) for p in Path("data_pipeline/bronze").glob("*.contract.json")],
                notes=f"Silver feature set: {name}. Derived from Bronze layer World Bank/Stats NZ proxy data.",
            )

            contract_path = str(filepath).replace(".parquet", ".contract.json")
            with open(contract_path, "w", encoding="utf-8") as f:
                json.dump(contract.to_dict(), f, indent=2, default=str)

            contracts[filename] = contract_path
            logger.info("Generated contract for %s (%d records)", filename, analysis["record_count"])

        except Exception as e:
            logger.error("Failed to generate contract for %s: %s", filename, e)

    return contracts


def generate_gold_contracts(gold_dir: str = "data_pipeline/gold") -> dict:
    """Generate contracts for Gold layer KPI parquet files."""
    gold_path = Path(gold_dir)
    contracts = {}

    for name, filename, source, source_name in GOLD_KPIS:
        filepath = gold_path / filename
        if not filepath.exists():
            logger.warning("Gold file not found: %s", filename)
            continue

        try:
            df = pd.read_parquet(filepath)
            analysis = _analyze_dataframe(df)

            contract = DataContract(
                artifact_name=f"gold_{name}",
                artifact_path=str(filepath),
                layer="gold",
                source=source,
                source_name=source_name,
                quality=DataQuality.GOOD,
                confidence_score=85.0,
                record_count=analysis["record_count"],
                column_count=analysis["column_count"],
                null_percentage=analysis["null_pct"],
                columns=analysis["columns"],
                parent_contracts=[str(p) for p in Path("data_pipeline/silver").glob("*.contract.json")],
                notes=f"Gold KPI set: {name}. Computed from Silver layer features.",
            )

            contract_path = str(filepath).replace(".parquet", ".contract.json")
            with open(contract_path, "w", encoding="utf-8") as f:
                json.dump(contract.to_dict(), f, indent=2, default=str)

            contracts[filename] = contract_path
            logger.info("Generated contract for %s (%d records)", filename, analysis["record_count"])

        except Exception as e:
            logger.error("Failed to generate contract for %s: %s", filename, e)

    return contracts


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    print("Generating Silver layer contracts...")
    silver_contracts = generate_silver_contracts()
    print("  Generated %d Silver contracts" % len(silver_contracts))

    print("\nGenerating Gold layer contracts...")
    gold_contracts = generate_gold_contracts()
    print("  Generated %d Gold contracts" % len(gold_contracts))

    print("\nTotal: %d contracts" % (len(silver_contracts) + len(gold_contracts)))
