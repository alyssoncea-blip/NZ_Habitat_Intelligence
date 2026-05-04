"""Base KPI calculator for NZ Habitat Intelligence — Gold Layer.

Shared data loading, helpers, and data accessors used by all dashboard KPI calculators.
"""
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

NZ_REGIONS = [
    "Northland", "Auckland", "Waikato", "Bay of Plenty", "Gisborne",
    "Hawke's Bay", "Taranaki", "Manawatu-Wanganui", "Wellington",
    "Tasman", "Nelson", "Marlborough", "West Coast", "Canterbury",
    "Otago", "Southland",
]


class KPIBaseCalculator:
    """Base class providing shared data loading and helper methods."""

    def __init__(self, silver_dir: str = "data_pipeline/silver",
                 gold_dir: str = "data_pipeline/gold",
                 bronze_dir: str = "data_pipeline/bronze"):
        self.silver_dir = Path(silver_dir)
        self.gold_dir = Path(gold_dir)
        self.bronze_dir = Path(bronze_dir)
        self.gold_dir.mkdir(parents=True, exist_ok=True)
        self.features = self._load_silver_features()
        self.bronze = self._load_bronze_data()
        self.now = datetime.now()

    def _load_silver_features(self) -> Dict[str, pd.DataFrame]:
        features: Dict[str, pd.DataFrame] = {}
        for fp in sorted(self.silver_dir.glob("*_features.parquet")):
            if "fixed" in fp.stem:
                continue
            try:
                df = pd.read_parquet(fp)
                if df.empty:
                    continue
                key = fp.stem.replace("_features", "")
                features[key] = df
                logger.info("  Loaded silver: %s (%d rows)", key, len(df))
            except Exception as e:
                logger.warning("  Skip %s: %s", fp.name, e)
        return features

    def _load_bronze_data(self) -> Dict[str, pd.DataFrame]:
        bronze = {}
        for pattern in ["stats_nz_*.json", "mbie_*.json", "rbnz_*.json"]:
            for fp in sorted(self.bronze_dir.glob(pattern)):
                if ".contract." in fp.name:
                    continue
                try:
                    with open(fp, "r", encoding="utf-8") as f:
                        raw = json.load(f)
                    records = raw.get("data", [])
                    if records:
                        df = pd.DataFrame(records)
                        for col in df.columns:
                            if col not in ("region", "month_name", "quarter", "date"):
                                df[col] = pd.to_numeric(df[col], errors="coerce")
                        name = fp.stem.replace("_raw", "")
                        bronze[name] = df
                except Exception:
                    pass
        return bronze

    @staticmethod
    def _safe_float(val: Any, default: float = 0.0) -> float:
        if val is None:
            return default
        try:
            f = float(val)
            return f if np.isfinite(f) else default
        except (ValueError, TypeError):
            return default

    @staticmethod
    def _safe_latest(df: Optional[pd.DataFrame], col: str, default: float = 0.0) -> float:
        if df is None or df.empty or col not in df.columns:
            return default
        valid = df[col].dropna()
        if valid.empty:
            return default
        return float(valid.iloc[-1])

    @staticmethod
    def _latest_year(features: Dict[str, pd.DataFrame]) -> int:
        years = set()
        for df in features.values():
            if "year" in df.columns:
                years.update(pd.to_numeric(df["year"], errors="coerce").dropna().astype(int).tolist())
        return max(years) if years else datetime.now().year

    def _get_ocr_current(self) -> float:
        df = self.features.get("interest_rate_lag")
        val = self._safe_latest(df, "interest_rate")
        if val > 0:
            return val
        if "rbnz_ocr" in self.bronze:
            ocr = self.bronze["rbnz_ocr"]
            if "value" in ocr.columns:
                valid = ocr["value"].dropna()
                if not valid.empty:
                    return float(valid.iloc[-1])
        return 5.50

    def _get_inflation_latest(self) -> float:
        df = self.features.get("rent_income_ratio")
        val = self._safe_latest(df, "general_inflation")
        if val > 0:
            return val
        return 4.0

    def _get_unemployment_latest(self) -> float:
        df = self.features.get("tourism_pressure")
        if df is not None and not df.empty and "unemployment_rate" in df.columns:
            valid = df["unemployment_rate"].dropna()
            if not valid.empty:
                return float(valid.iloc[-1])
        return 4.0

    def _get_gdp_per_capita(self) -> float:
        df = self.features.get("affordability")
        if df is not None and not df.empty and "gdp_per_capita" in df.columns:
            valid = df["gdp_per_capita"].dropna()
            if not valid.empty:
                return float(valid.iloc[-1])
        return 48000.0

    def _get_gdp_per_capita_yoy(self) -> float:
        df = self.features.get("affordability")
        if df is None or df.empty or "gdp_per_capita" not in df.columns:
            return 2.0
        vals = df["gdp_per_capita"].dropna()
        if len(vals) >= 2:
            prev, curr = float(vals.iloc[-2]), float(vals.iloc[-1])
            if prev > 0:
                return (curr - prev) / prev * 100
        return 2.0

    def _get_housing_supply_pressure(self) -> float:
        df = self.features.get("supply_deficit")
        if df is not None and not df.empty and "housing_supply_pressure" in df.columns:
            valid = df["housing_supply_pressure"].dropna()
            if not valid.empty:
                return float(valid.iloc[-1])
        return 50.0

    def _get_rent_inflation(self) -> float:
        df = self.features.get("rent_income_ratio")
        val = self._safe_latest(df, "rent_inflation")
        return val if val > 0 else 6.0

    def _get_affordability_erosion(self) -> float:
        df = self.features.get("rent_income_ratio")
        val = self._safe_latest(df, "affordability_erosion")
        return val if np.isfinite(val) else 2.0

    def _get_macro_volatility(self) -> float:
        df = self.features.get("tourism_lag_analysis")
        val = self._safe_latest(df, "macroeconomic_volatility_index")
        return val if val > 0 else 30.0

    def _get_ir_impact_score(self) -> float:
        df = self.features.get("interest_rate_lag")
        val = self._safe_latest(df, "interest_rate_impact_score")
        return val if val > 0 else 50.0

    def _get_tourism_economy_corr(self) -> float:
        df = self.features.get("tourism_pressure")
        if df is not None and not df.empty and "tourism_growth_yoy" in df.columns:
            if "housing_supply_pressure" in df.columns:
                corr = df["tourism_growth_yoy"].corr(df["housing_supply_pressure"])
                if np.isfinite(corr):
                    return corr
        return 0.0

    def _get_regional_data(self) -> Dict[str, Dict[str, Any]]:
        """Build regional data from Bronze Stats NZ and MBIE data."""
        regional = {}

        if "stats_nz_population" in self.bronze:
            pop = self.bronze["stats_nz_population"]
            if "year" in pop.columns and "region" in pop.columns and "population" in pop.columns:
                latest_year = pop["year"].max()
                latest = pop[pop["year"] == latest_year]
                for _, row in latest.iterrows():
                    r = row["region"]
                    if r not in regional:
                        regional[r] = {}
                    regional[r]["population"] = int(row["population"])

        if "stats_nz_income" in self.bronze:
            inc = self.bronze["stats_nz_income"]
            if "year" in inc.columns and "region" in inc.columns and "median_income" in inc.columns:
                latest_year = inc["year"].max()
                latest = inc[inc["year"] == latest_year]
                for _, row in latest.iterrows():
                    r = row["region"]
                    if r not in regional:
                        regional[r] = {}
                    regional[r]["median_income"] = float(row["median_income"])

        if "stats_nz_building_consents" in self.bronze:
            bc = self.bronze["stats_nz_building_consents"]
            if "year" in bc.columns and "region" in bc.columns and "consents" in bc.columns:
                latest_year = bc["year"].max()
                latest = bc[bc["year"] == latest_year]
                for _, row in latest.iterrows():
                    r = row["region"]
                    if r not in regional:
                        regional[r] = {}
                    regional[r]["building_consents"] = int(row["consents"])

        if "mbie_rent_data" in self.bronze:
            rent = self.bronze["mbie_rent_data"]
            if "year" in rent.columns and "region" in rent.columns and "median_weekly_rent_nzd" in rent.columns:
                latest_year = rent["year"].max()
                latest = rent[rent["year"] == latest_year]
                for _, row in latest.iterrows():
                    r = row["region"]
                    if r not in regional:
                        regional[r] = {}
                    regional[r]["weekly_rent"] = float(row["median_weekly_rent_nzd"])

        if "mbie_regional_tourism" in self.bronze:
            rt = self.bronze["mbie_regional_tourism"]
            if "year" in rt.columns and "region" in rt.columns and "tourism_expenditure_nzd_millions" in rt.columns:
                latest_year = rt["year"].max()
                latest = rt[rt["year"] == latest_year]
                for _, row in latest.iterrows():
                    r = row["region"]
                    if r not in regional:
                        regional[r] = {}
                    regional[r]["tourism_expenditure_millions"] = float(row["tourism_expenditure_nzd_millions"])

        return regional

    def _estimate_median_price(self, region: str, regional: Dict) -> float:
        """Estimate median house price from regional income x price-to-income ratio."""
        income = regional.get(region, {}).get("median_income", 65000)
        pop = regional.get(region, {}).get("population", 100000)
        if pop > 1000000:
            ratio = 9.0
        elif pop > 500000:
            ratio = 8.0
        elif pop > 200000:
            ratio = 7.5
        else:
            ratio = 6.5
        return round(income * ratio, 0)
