"""KPI Calculator for NZ Habitat Intelligence - Gold Layer.

Thin orchestrator that delegates to per-dashboard calculator modules.
Each dashboard has its own calculator class in a separate file:
- kpi_executive.py
- kpi_housing.py
- kpi_tourism.py
- kpi_macro.py
- kpi_affordability.py
- kpi_forecast.py
"""
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict

import pandas as pd

from data_pipeline.utils.data_contract import (
    DataSource, save_dataframe_with_contract,
)
from .kpi_base import KPIBaseCalculator
from .kpi_executive import ExecutiveKPICalculator
from .kpi_housing import HousingKPICalculator
from .kpi_tourism import TourismKPICalculator
from .kpi_macro import MacroKPICalculator
from .kpi_affordability import AffordabilityKPICalculator
from .kpi_forecast import ForecastKPICalculator

logger = logging.getLogger(__name__)


class KPICalculator(KPIBaseCalculator):
    """Orchestrates KPI calculation across all 6 dashboard calculators."""

    def calculate_all(self, use_dbt: bool = True) -> Dict[str, pd.DataFrame]:
        """Calculate all KPIs using per-dashboard calculators.

        Args:
            use_dbt: If True, try to read from dbt output first.
                     Falls back to Python calculation if dbt output unavailable.
        """
        if use_dbt:
            return self._calculate_with_dbt()
        return self._calculate_python_only()

    def _calculate_with_dbt(self) -> Dict[str, pd.DataFrame]:
        """Calculate KPIs using dbt as primary source."""
        kpis = self._load_dbt_kpis()

        # Fill missing dashboards with Python calculations
        if "dashboard_01_executive" not in kpis or kpis["dashboard_01_executive"].empty:
            kpis["dashboard_01_executive"] = ExecutiveKPICalculator(
                silver_dir=str(self.silver_dir),
                gold_dir=str(self.gold_dir),
                bronze_dir=str(self.bronze_dir),
            ).calc()
        if "dashboard_02_housing" not in kpis or kpis["dashboard_02_housing"].empty:
            kpis["dashboard_02_housing"] = HousingKPICalculator(
                silver_dir=str(self.silver_dir),
                gold_dir=str(self.gold_dir),
                bronze_dir=str(self.bronze_dir),
            ).calc()
        if "dashboard_03_tourism" not in kpis or kpis["dashboard_03_tourism"].empty:
            kpis["dashboard_03_tourism"] = TourismKPICalculator(
                silver_dir=str(self.silver_dir),
                gold_dir=str(self.gold_dir),
                bronze_dir=str(self.bronze_dir),
            ).calc()
        if "dashboard_04_macro" not in kpis or kpis["dashboard_04_macro"].empty:
            kpis["dashboard_04_macro"] = MacroKPICalculator(
                silver_dir=str(self.silver_dir),
                gold_dir=str(self.gold_dir),
                bronze_dir=str(self.bronze_dir),
            ).calc()
        if "dashboard_05_affordability" not in kpis or kpis["dashboard_05_affordability"].empty:
            kpis["dashboard_05_affordability"] = AffordabilityKPICalculator(
                silver_dir=str(self.silver_dir),
                gold_dir=str(self.gold_dir),
                bronze_dir=str(self.bronze_dir),
            ).calc()
        if "dashboard_06_forecast" not in kpis or kpis["dashboard_06_forecast"].empty:
            kpis["dashboard_06_forecast"] = ForecastKPICalculator(
                silver_dir=str(self.silver_dir),
                gold_dir=str(self.gold_dir),
                bronze_dir=str(self.bronze_dir),
            ).calc()

        self._save_kpis(kpis)
        return kpis

    def _calculate_python_only(self) -> Dict[str, pd.DataFrame]:
        """Calculate all KPIs with Python (legacy mode)."""
        logger.info("Calculating all KPIs from real Silver/Bronze data...")

        kpis = {
            "dashboard_01_executive": ExecutiveKPICalculator(
                silver_dir=str(self.silver_dir),
                gold_dir=str(self.gold_dir),
                bronze_dir=str(self.bronze_dir),
            ).calc(),
            "dashboard_02_housing": HousingKPICalculator(
                silver_dir=str(self.silver_dir),
                gold_dir=str(self.gold_dir),
                bronze_dir=str(self.bronze_dir),
            ).calc(),
            "dashboard_03_tourism": TourismKPICalculator(
                silver_dir=str(self.silver_dir),
                gold_dir=str(self.gold_dir),
                bronze_dir=str(self.bronze_dir),
            ).calc(),
            "dashboard_04_macro": MacroKPICalculator(
                silver_dir=str(self.silver_dir),
                gold_dir=str(self.gold_dir),
                bronze_dir=str(self.bronze_dir),
            ).calc(),
            "dashboard_05_affordability": AffordabilityKPICalculator(
                silver_dir=str(self.silver_dir),
                gold_dir=str(self.gold_dir),
                bronze_dir=str(self.bronze_dir),
            ).calc(),
            "dashboard_06_forecast": ForecastKPICalculator(
                silver_dir=str(self.silver_dir),
                gold_dir=str(self.gold_dir),
                bronze_dir=str(self.bronze_dir),
            ).calc(),
        }

        self._save_kpis(kpis)
        return kpis

    def _load_dbt_kpis(self) -> Dict[str, pd.DataFrame]:
        """Read KPIs from dbt gold output parquet files."""
        logger.info("Reading KPIs from dbt gold output...")
        kpis = {}
        dbt_files = {
            "dashboard_01_executive": "kpis-01-executive_complete.parquet",
            "dashboard_02_housing": "kpis-02-housing_complete.parquet",
            "dashboard_03_tourism": "kpis-03-tourism_complete.parquet",
            "dashboard_04_macro": "kpis-04-macro_complete.parquet",
            "dashboard_05_affordability": "kpis-05-affordability_complete.parquet",
            "dashboard_06_forecast": "kpis-06-forecast_complete.parquet",
        }

        for name, filename in dbt_files.items():
            dbt_path = self.gold_dir / filename
            if dbt_path.exists():
                try:
                    df = pd.read_parquet(dbt_path)
                    if "kpi_name" in df.columns and "name" not in df.columns:
                        df = df.rename(columns={"kpi_name": "name"})
                    if "kpi_value" in df.columns and "value" not in df.columns:
                        df = df.rename(columns={"kpi_value": "value"})
                    kpis[name] = df
                    logger.info("  Loaded dbt %s: %d rows", name, len(df))
                except Exception as e:
                    logger.warning("  Failed to load dbt %s: %s", name, e)

        return kpis

    def _save_kpis(self, kpis: Dict[str, pd.DataFrame]) -> None:
        """Save KPIs with contracts."""
        for name, df in kpis.items():
            clean = name.replace("dashboard_", "").replace("_", "-")
            out = str(self.gold_dir / f"kpis-{clean}_complete")
            try:
                save_dataframe_with_contract(
                    df=df, path=out, artifact_name=f"kpis-{clean}",
                    layer="gold", source=DataSource.REAL,
                    source_name="silver_bronze_real_data",
                    notes="Calculated from real Silver/Bronze data (World Bank, Stats NZ, RBNZ, MBIE)",
                )
                logger.info("  Saved %s: %d rows", name, len(df))
            except Exception as e:
                logger.error("  Error saving %s: %s", name, e)
                fallback = self.gold_dir / f"kpis-{clean}_complete.parquet"
                df.to_parquet(fallback, index=False)

        meta = {
            "generated_at": datetime.now().isoformat(),
            "dashboards": {n: len(df) for n, df in kpis.items()},
            "total_kpis": sum(len(df) for df in kpis.values()),
            "source": "real_silver_bronze_data",
        }
        with open(self.gold_dir / "kpis_metadata_complete.json", "w") as f:
            json.dump(meta, f, indent=2, default=str)

        logger.info("All KPIs calculated and saved. Total: %d KPI records", meta["total_kpis"])


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    calc = KPICalculator()
    kpis = calc.calculate_all()
    print(f"\nGold layer complete: {len(kpis)} dashboards, "
          f"{sum(len(df) for df in kpis.values())} total KPI records")
