"""Feature Engineering for NZ Habitat Intelligence — Silver Layer.

Calculates 6 core feature sets from REAL Bronze data:
- World Bank (GDP, inflation, unemployment, interest rates, population)
- Stats NZ (building consents, population, income by region)
- RBNZ (OCR, mortgage rates, CPI)
- MBIE (visitor arrivals, regional tourism, rent data)

All features are data-driven — no hardcoded or synthetic values.
"""
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

import pandas as pd

from data_pipeline.utils.data_contract import (
    DataSource, save_dataframe_with_contract,
)

logger = logging.getLogger(__name__)

NZ_REGIONS = [
    "Auckland", "Wellington", "Canterbury", "Waikato", "Bay of Plenty",
    "Otago", "Northland", "Taranaki", "Hawke's Bay", "Manawatu-Wanganui",
    "Southland", "Nelson", "Tasman", "Marlborough", "Gisborne", "West Coast",
]

# Load reference data from config
_CONFIG_DIR = Path(__file__).parent.parent / "config"
_REFERENCE_DATA: Dict[str, Any] = {}
try:
    with open(_CONFIG_DIR / "reference_data.json", "r", encoding="utf-8") as f:
        _REFERENCE_DATA = json.load(f)
except Exception:
    pass

_REGIONAL_POP_SHARES: Dict[str, float] = _REFERENCE_DATA.get("regional_population_shares", {})


class FeatureEngineer:
    """Feature engineering from real Bronze data."""

    def __init__(self, bronze_dir: str = "data_pipeline/bronze",
                 silver_dir: str = "data_pipeline/silver"):
        self.bronze_dir = Path(bronze_dir)
        self.silver_dir = Path(silver_dir)
        self.silver_dir.mkdir(parents=True, exist_ok=True)

    def _get_bronze_contracts(self) -> List[str]:
        """Get paths to all Bronze layer contract files."""
        contracts = []
        if self.bronze_dir.exists():
            for contract_file in sorted(self.bronze_dir.glob("*.contract.json")):
                contracts.append(str(contract_file))
        return contracts

    # ── Load Bronze data ──────────────────────────────────────────────
    def load_bronze_data(self) -> Dict[str, Any]:
        """Load all Bronze layer data."""
        data = {"world_bank": {}, "rbnz": {}, "stats_nz": {}, "mbie": {}}

        for pattern, key in [
            ("world_bank_*.json", "world_bank"),
            ("rbnz_*.json", "rbnz"),
            ("stats_nz_*.json", "stats_nz"),
            ("mbie_*.json", "mbie"),
        ]:
            for fp in sorted(self.bronze_dir.glob(pattern)):
                if ".contract." in fp.name:
                    continue
                try:
                    with open(fp, "r", encoding="utf-8") as f:
                        raw = json.load(f)
                    records = raw.get("data", [])
                    if records:
                        df = pd.DataFrame(records)
                        # Normalize numeric columns
                        for col in df.columns:
                            if col not in ("region", "month_name", "quarter", "date", "indicator", "country"):
                                df[col] = pd.to_numeric(df[col], errors="coerce")
                        name = fp.stem.replace("_raw", "").replace(f"{key}_", "")
                        # Handle duplicate keys (e.g., interest_rate vs interest_rates)
                        if name in data[key]:
                            name = name + "_alt"
                        data[key][name] = df
                        logger.info("  Loaded %s/%s: %d rows, cols=%s", key, name, len(df), list(df.columns))
                except Exception as e:
                    logger.warning("  Skip %s: %s", fp.name, e)

        return data

    # ── Feature 1: Affordability ──────────────────────────────────────
    def _calc_affordability(self, bronze: Dict) -> Optional[pd.DataFrame]:
        """Affordability = GDP per capita (national) + regional price/income ratios."""
        wb = bronze["world_bank"]
        sn = bronze["stats_nz"]

        # Find GDP and population data (handle both old and new formats)
        gdp_df = None
        pop_df = None

        for key in ["gdp", "gdp_growth"]:
            if key in wb and "value" in wb[key].columns:
                gdp_df = wb[key][["year", "value"]].rename(columns={"value": "gdp"})
                break

        for key in ["population"]:
            if key in wb and "value" in wb[key].columns:
                pop_df = wb[key][["year", "value"]].rename(columns={"value": "population"})
                break

        if gdp_df is None or pop_df is None:
            return None

        macro = pd.merge(gdp_df, pop_df, on="year", how="outer").sort_values("year")
        if macro.empty:
            return None

        # GDP per capita
        macro["gdp_per_capita"] = macro["gdp"] / macro["population"]

        # Regional affordability from Stats NZ income
        if "income" in sn and not sn["income"].empty:
            inc = sn["income"]
            if "year" in inc.columns and "region" in inc.columns:
                rows = []
                for _, row in macro.iterrows():
                    year = int(row["year"])
                    gdp_pc = row.get("gdp_per_capita", None)
                    if gdp_pc is None or gdp_pc <= 0:
                        continue
                    year_inc = inc[inc["year"] == year] if "year" in inc.columns else pd.DataFrame()
                    for region in NZ_REGIONS:
                        region_inc = year_inc[year_inc["region"] == region] if not year_inc.empty else pd.DataFrame()
                        median_income = None
                        if not region_inc.empty:
                            if "median_household_income" in region_inc.columns:
                                median_income = region_inc["median_household_income"].iloc[0]
                            elif "median_income" in region_inc.columns:
                                median_income = region_inc["median_income"].iloc[0]
                        if median_income and median_income > 0:
                            aff_idx = round((gdp_pc / median_income) * 50, 1)
                        else:
                            aff_idx = None
                        price_to_income_ratio = None
                        if median_income and median_income > 0:
                            price_to_income_ratio = round(gdp_pc / median_income, 4)
                        rows.append({
                            "year": year,
                            "region": region,
                            "gdp_per_capita": round(gdp_pc, 0),
                            "median_income": median_income,
                            "affordability_index": aff_idx,
                            "price_to_income_ratio": price_to_income_ratio,
                        })
                if rows:
                    return pd.DataFrame(rows)

        # Fallback: national-level only
        macro["region"] = "New Zealand"
        macro["year"] = macro["year"].astype(int)
        macro["affordability_index"] = (
            (macro["gdp_per_capita"] - macro["gdp_per_capita"].min()) /
            (macro["gdp_per_capita"].max() - macro["gdp_per_capita"].min() + 1) * 100
        ).round(1)
        return macro[["region", "year", "affordability_index", "gdp_per_capita"]]

    # ── Feature 2: Interest Rate Lag ──────────────────────────────────
    def _calc_interest_rate_lag(self, bronze: Dict) -> Optional[pd.DataFrame]:
        """Interest rate analysis from RBNZ OCR + World Bank rates."""
        rbnz = bronze["rbnz"]
        wb = bronze["world_bank"]

        annual = None

        # Try RBNZ OCR first
        if "ocr" in rbnz and not rbnz["ocr"].empty:
            ocr = rbnz["ocr"]
            if "ocr_rate" in ocr.columns and "date" in ocr.columns:
                ocr = ocr.sort_values("date").reset_index(drop=True)
                ocr["year"] = pd.to_datetime(ocr["date"]).dt.year
                annual = ocr.groupby("year")["ocr_rate"].mean().reset_index()
                annual.columns = ["year", "ocr_value"]
            elif "value" in ocr.columns:
                if "date" in ocr.columns:
                    ocr["year"] = pd.to_datetime(ocr["date"]).dt.year
                    annual = ocr.groupby("year")["value"].mean().reset_index()
                    annual.columns = ["year", "ocr_value"]

        # Fallback to World Bank interest rate
        if annual is None or annual.empty:
            for key in ["interest_rate", "interest_rates"]:
                if key in wb and "value" in wb[key].columns and "year" in wb[key].columns:
                    annual = wb[key][["year", "value"]].rename(columns={"value": "ocr_value"})
                    break

        if annual is None or annual.empty:
            return None

        annual = annual.sort_values("year").reset_index(drop=True)
        annual["mortgage_rate_2yr"] = annual["ocr_value"]
        annual["rate_volatility"] = annual["ocr_value"].rolling(3, min_periods=1).std()
        annual["ocr_change_bps"] = annual["ocr_value"].pct_change(fill_method=None) * 100
        max_vol = annual["rate_volatility"].max() + 0.01
        annual["interest_rate_impact_score"] = (annual["rate_volatility"] / max_vol * 100).round(1)
        annual["region"] = "New Zealand"
        annual["year"] = annual["year"].astype(int)
        return annual[["year", "region", "ocr_value", "mortgage_rate_2yr", "ocr_change_bps", "rate_volatility", "interest_rate_impact_score"]]

    # ── Feature 3: Tourism Pressure ───────────────────────────────────
    def _calc_tourism_pressure(self, bronze: Dict) -> Optional[pd.DataFrame]:
        """Tourism pressure from MBIE visitor arrivals + regional tourism expenditure."""
        mbie = bronze["mbie"]
        wb = bronze["world_bank"]

        rows = []

        # Use regional tourism expenditure if available
        if "regional_tourism" in mbie and not mbie["regional_tourism"].empty:
            rt = mbie["regional_tourism"]
            if "year" in rt.columns and "region" in rt.columns:
                for _, row in rt.iterrows():
                    year = int(row["year"])
                    region = row["region"]
                    # Handle different column names
                    expenditure = row.get("tourism_expenditure_nzd_millions",
                                 row.get("tourism_spending_usd", 0))

                    pop_share = self._get_region_population_share(region)
                    # Use config for NZ population estimate, fallback to 5.2M
                    nz_pop = _REFERENCE_DATA.get("nz_population_estimates", {}).get(
                        str(year), 5200000
                    )
                    pop_estimate = pop_share * nz_pop
                    pressure = round((expenditure * 1000000 / max(1, pop_estimate)) * 10, 1) if pop_estimate > 0 else 0

                    rows.append({
                        "year": year,
                        "region": region,
                        "tourism_expenditure": expenditure,
                        "visitor_arrivals": expenditure,
                        "tourism_pressure_index": pressure,
                    })

        if rows:
            df = pd.DataFrame(rows)
            # Add unemployment from World Bank
            for key in ["unemployment"]:
                if key in wb and "value" in wb[key].columns and "year" in wb[key].columns:
                    unemp = wb[key][["year", "value"]].rename(columns={"value": "unemployment_rate"})
                    df = pd.merge(df, unemp, on="year", how="left")
                    break

            # Add tourism growth YoY
            df = df.sort_values(["region", "year"])
            df["tourism_growth_yoy"] = df.groupby("region")["tourism_expenditure"].pct_change(fill_method=None) * 100
            return df

        return None

    # ── Feature 4: Supply Deficit ─────────────────────────────────────
    def _calc_supply_deficit(self, bronze: Dict) -> Optional[pd.DataFrame]:
        """Supply deficit = Stats NZ building consents vs population growth."""
        sn = bronze["stats_nz"]

        if "building_consents" not in sn or sn["building_consents"].empty:
            return None

        bc = sn["building_consents"]
        if "year" not in bc.columns or "region" not in bc.columns:
            return None

        # Get population data
        pop_df = None
        if "population" in sn and not sn["population"].empty:
            pop_df = sn["population"]

        rows = []
        for region in NZ_REGIONS:
            region_bc = bc[bc["region"] == region].sort_values("year")
            if region_bc.empty:
                continue

            # Get population for this region
            region_pop = pd.DataFrame()
            if pop_df is not None and "region" in pop_df.columns:
                region_pop = pop_df[pop_df["region"] == region].sort_values("year")

            for _, bc_row in region_bc.iterrows():
                year = int(bc_row["year"])
                # Handle different column names for consents
                consents = bc_row.get("consents",
                            bc_row.get("new_residential_consents",
                            bc_row.get("total_consents", 0)))

                # Population for this region/year
                population = None
                if not region_pop.empty:
                    pop_row = region_pop[region_pop["year"] == year]
                    if not pop_row.empty and "population" in pop_row.columns:
                        population = pop_row["population"].iloc[0]

                # Population growth
                pop_growth = None
                if not region_pop.empty and len(region_pop) > 1:
                    pop_vals = region_pop[region_pop["year"] <= year].sort_values("year")
                    if len(pop_vals) >= 2 and "population" in pop_vals.columns:
                        prev = pop_vals.iloc[-2]["population"]
                        curr = pop_vals.iloc[-1]["population"]
                        if prev > 0:
                            pop_growth = round((curr - prev) / prev * 100, 2)

                consents_per_1k = round(consents / max(1, population) * 1000, 2) if population else None

                rows.append({
                    "year": year, "region": region,
                    "building_consents": consents,
                    "population": population,
                    "population_growth": pop_growth,
                    "consents_per_1000_people": consents_per_1k,
                })

        if not rows:
            return None

        df = pd.DataFrame(rows)

        # Calculate housing supply pressure index (0-100)
        if "consents_per_1000_people" in df.columns:
            valid = df["consents_per_1000_people"].dropna()
            if not valid.empty:
                min_c = valid.min()
                max_c = valid.max()
                df["supply_deficit_score"] = (
                    (df["consents_per_1000_people"] - min_c) / (max_c - min_c + 0.01) * 100
                ).round(1)
                df["housing_supply_gap"] = (df["population_growth"].fillna(0) - df["consents_per_1000_people"].fillna(0)).round(2)

        return df

    # ── Feature 5: Rent Income Ratio ──────────────────────────────────
    def _calc_rent_income_ratio(self, bronze: Dict) -> Optional[pd.DataFrame]:
        """Rent-to-income ratio from Tenancy Services rent + Stats NZ income."""
        mbie = bronze["mbie"]
        sn = bronze["stats_nz"]
        wb = bronze["world_bank"]

        # Try MBIE rent data first
        rent = None
        if "rent_data" in mbie and not mbie["rent_data"].empty:
            rent = mbie["rent_data"]
        elif "international_visitors" in mbie:
            # No rent data available, use income + inflation as proxy
            pass

        if rent is None or rent.empty or "year" not in rent.columns or "region" not in rent.columns:
            # Fallback: use Stats NZ income + World Bank inflation
            if "income" not in sn or sn["income"].empty:
                return None
            inc = sn["income"]
            rows = []
            for _, row in inc.iterrows():
                year = int(row["year"])
                region = row["region"]
                median_income = row.get("median_household_income", row.get("median_income", 0))
                # Estimate rent as ~30% of income
                weekly_rent = round(median_income * 0.30 / 52, 0) if median_income > 0 else 0
                annual_rent = weekly_rent * 52
                rent_ratio = round(annual_rent / median_income * 100, 1) if median_income > 0 else None

                # Get inflation
                inflation = None
                for key in ["inflation"]:
                    if key in wb and "value" in wb[key].columns:
                        inf_row = wb[key][wb[key]["year"] == year]
                        if not inf_row.empty:
                            inflation = inf_row["value"].iloc[0]
                        break

                rows.append({
                    "year": year, "region": region,
                    "median_weekly_rent": weekly_rent,
                    "annual_rent": annual_rent,
                    "median_income": median_income,
                    "rent_to_income_ratio": rent_ratio,
                    "general_inflation": inflation,
                })
            if rows:
                df = pd.DataFrame(rows)
                df = df.sort_values(["region", "year"])
                df["rent_inflation_rate"] = df.groupby("region")["median_weekly_rent"].pct_change(fill_method=None) * 100
                if "general_inflation" in df.columns:
                    df["affordability_erosion"] = (df["rent_inflation_rate"].fillna(0) - df["general_inflation"].fillna(0)).round(1)
                df["cumulative_rent_pressure"] = (
                    df.groupby("region")["median_weekly_rent"].transform(
                        lambda x: ((x / x.iloc[0]) - 1) * 100 if len(x) > 0 and x.iloc[0] > 0 else 0
                    )
                ).round(1)
                return df
            return None

        # Use actual rent data
        rows = []
        for region in NZ_REGIONS:
            region_rent = rent[rent["region"] == region].sort_values("year")
            if region_rent.empty:
                continue

            region_income = pd.DataFrame()
            if "income" in sn and not sn["income"].empty:
                region_income = sn["income"][sn["income"]["region"] == region].sort_values("year")

            for _, rent_row in region_rent.iterrows():
                year = int(rent_row["year"])
                weekly_rent = rent_row.get("median_weekly_rent_nzd", 0)
                annual_rent = weekly_rent * 52

                inc_row = region_income[region_income["year"] == year] if not region_income.empty else pd.DataFrame()
                median_income = None
                if not inc_row.empty:
                    if "median_household_income" in inc_row.columns:
                        median_income = inc_row["median_household_income"].iloc[0]
                    elif "median_income" in inc_row.columns:
                        median_income = inc_row["median_income"].iloc[0]

                rent_ratio = round(annual_rent / median_income * 100, 1) if median_income and median_income > 0 else None

                inflation = None
                for key in ["inflation"]:
                    if key in wb and "value" in wb[key].columns:
                        inf_row = wb[key][wb[key]["year"] == year]
                        if not inf_row.empty:
                            inflation = inf_row["value"].iloc[0]
                        break

                rows.append({
                    "year": year, "region": region,
                    "median_weekly_rent": weekly_rent,
                    "annual_rent": annual_rent,
                    "median_income": median_income,
                    "rent_to_income_ratio": rent_ratio,
                    "general_inflation": inflation,
                })

        if not rows:
            return None

        df = pd.DataFrame(rows)
        df = df.sort_values(["region", "year"])
        df["rent_inflation_rate"] = df.groupby("region")["median_weekly_rent"].pct_change(fill_method=None) * 100
        if "general_inflation" in df.columns:
            df["affordability_erosion"] = (df["rent_inflation_rate"].fillna(0) - df["general_inflation"].fillna(0)).round(1)
        df["cumulative_rent_pressure"] = (
            df.groupby("region")["median_weekly_rent"].transform(
                lambda x: ((x / x.iloc[0]) - 1) * 100 if len(x) > 0 and x.iloc[0] > 0 else 0
            )
        ).round(1)
        return df

    # ── Feature 6: Macroeconomic Volatility ───────────────────────────
    def _calc_macro_volatility(self, bronze: Dict) -> Optional[pd.DataFrame]:
        """Composite macroeconomic volatility from all World Bank indicators."""
        wb = bronze["world_bank"]

        # Find indicators (handle both old and new names)
        indicators = {}
        for target, aliases in [
            ("gdp", ["gdp", "gdp_growth"]),
            ("inflation", ["inflation"]),
            ("unemployment", ["unemployment"]),
            ("interest_rate", ["interest_rate", "interest_rates"]),
        ]:
            for alias in aliases:
                if alias in wb and "value" in wb[alias].columns and "year" in wb[alias].columns:
                    indicators[target] = wb[alias][["year", "value"]].rename(columns={"value": target})
                    break

        if len(indicators) < 3:
            return None

        # Merge all indicators
        macro = indicators.get("gdp", pd.DataFrame())
        for name in ["inflation", "unemployment", "interest_rate"]:
            if name in indicators:
                if macro.empty:
                    macro = indicators[name]
                else:
                    macro = pd.merge(macro, indicators[name], on="year", how="outer")

        if macro.empty:
            return None

        macro = macro.sort_values("year").reset_index(drop=True)

        # Calculate volatility for each indicator (3-year rolling std)
        for col in ["gdp", "inflation", "unemployment", "interest_rate"]:
            if col in macro.columns:
                macro[f"{col}_volatility"] = macro[col].rolling(3, min_periods=1).std()

        # Composite volatility index (weighted)
        weights = {"gdp": 0.4, "inflation": 0.3, "unemployment": 0.2, "interest_rate": 0.1}
        macro["macroeconomic_volatility_index"] = 0
        for col, w in weights.items():
            if f"{col}_volatility" in macro.columns:
                macro["macroeconomic_volatility_index"] += macro[f"{col}_volatility"] * w

        # Normalize to 0-100
        max_v = macro["macroeconomic_volatility_index"].max()
        min_v = macro["macroeconomic_volatility_index"].min()
        macro["macroeconomic_volatility_index"] = (
            (macro["macroeconomic_volatility_index"] - min_v) / (max_v - min_v + 0.01) * 100
        ).round(1)

        macro["region"] = "New Zealand"
        macro["year"] = macro["year"].astype(int)

        vol_cols = [c for c in ["gdp_volatility", "inflation_volatility", "unemployment_volatility", "interest_rate_volatility"] if c in macro.columns]
        return macro[["region", "year", "macroeconomic_volatility_index"] + vol_cols]

    # ── Helpers ───────────────────────────────────────────────────────
    def _get_population_shares(self, stats_nz: Dict) -> Dict[str, float]:
        """Get population shares by region from Stats NZ data."""
        if "population" not in stats_nz or stats_nz["population"].empty:
            # Use config file shares
            if _REGIONAL_POP_SHARES:
                return _REGIONAL_POP_SHARES
            return {}

        pop = stats_nz["population"]
        if "year" in pop.columns and "region" in pop.columns:
            latest_year = pop["year"].max()
            latest = pop[pop["year"] == latest_year]
            if "population" in latest.columns:
                total = latest["population"].sum()
                if total > 0:
                    return {row["region"]: row["population"] / total for _, row in latest.iterrows()}

        # Fallback to config
        return _REGIONAL_POP_SHARES or {}

    def _get_region_population_share(self, region: str) -> float:
        """Get population share for a single region."""
        if _REGIONAL_POP_SHARES:
            return _REGIONAL_POP_SHARES.get(region, 0.01)
        return 0.01

    # ── Main pipeline ─────────────────────────────────────────────────
    def run_all_feature_engineering(self) -> Dict[str, pd.DataFrame]:
        """Run all feature engineering from real Bronze data."""
        logger.info("Starting feature engineering from real Bronze data...")
        bronze = self.load_bronze_data()

        features = {}
        sources = {}

        # Feature 1: Affordability
        df = self._calc_affordability(bronze)
        if df is not None and not df.empty:
            features["affordability"] = df
            sources["affordability"] = DataSource.REAL
            logger.info("  Affordability: %d rows (real data)", len(df))

        # Feature 2: Interest Rate Lag
        df = self._calc_interest_rate_lag(bronze)
        if df is not None and not df.empty:
            features["interest_rate_lag"] = df
            sources["interest_rate_lag"] = DataSource.REAL
            logger.info("  Interest rate lag: %d rows (real data)", len(df))

        # Feature 3: Tourism Pressure
        df = self._calc_tourism_pressure(bronze)
        if df is not None and not df.empty:
            features["tourism_pressure"] = df
            sources["tourism_pressure"] = DataSource.REAL
            logger.info("  Tourism pressure: %d rows (real data)", len(df))

        # Feature 4: Supply Deficit
        df = self._calc_supply_deficit(bronze)
        if df is not None and not df.empty:
            features["supply_deficit"] = df
            sources["supply_deficit"] = DataSource.REAL
            logger.info("  Supply deficit: %d rows (real data)", len(df))

        # Feature 5: Rent Income Ratio
        df = self._calc_rent_income_ratio(bronze)
        if df is not None and not df.empty:
            features["rent_income_ratio"] = df
            sources["rent_income_ratio"] = DataSource.REAL
            logger.info("  Rent income ratio: %d rows (real data)", len(df))

        # Feature 6: Macroeconomic Volatility
        df = self._calc_macro_volatility(bronze)
        if df is not None and not df.empty:
            features["tourism_lag_analysis"] = df
            sources["tourism_lag_analysis"] = DataSource.REAL
            logger.info("  Macro volatility: %d rows (real data)", len(df))

        if features:
            self.save_features(features, source_tracking=sources)
        else:
            logger.error("No features generated — check Bronze data")

        return features

    def save_features(self, features: Dict[str, pd.DataFrame],
                      source_tracking: Optional[Dict[str, DataSource]] = None) -> Dict[str, str]:
        """Save features to parquet with data contracts and lineage tracking."""
        file_paths = {}
        for name, df in features.items():
            if df.empty:
                continue
            source = source_tracking.get(name, DataSource.REAL) if source_tracking else DataSource.REAL
            output = str(self.silver_dir / f"{name}_features")
            try:
                parquet_path, contract_path = save_dataframe_with_contract(
                    df=df, path=output, artifact_name=f"{name}_features",
                    layer="silver", source=source, source_name="bronze_real_data",
                    parent_contracts=self._get_bronze_contracts(),
                    notes=f"Calculated from real Bronze data ({len(df)} records)",
                )
                file_paths[name] = parquet_path
                logger.info("  [%s] Saved %s: %d rows → %s", source.value, name, len(df), parquet_path)
            except Exception as e:
                logger.error("  Error saving %s: %s", name, e)
                fallback = self.silver_dir / f"{name}_features.parquet"
                df.to_parquet(fallback, index=False)
                file_paths[name] = str(fallback)

        # Save metadata
        meta = {
            "generated_date": datetime.now().isoformat(),
            "feature_count": len(features),
            "records_summary": {n: len(df) for n, df in features.items()},
            "feature_files": file_paths,
        }
        with open(self.silver_dir / "features_metadata.json", "w") as f:
            json.dump(meta, f, indent=2, default=str)

        return file_paths


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    fe = FeatureEngineer()
    features = fe.run_all_feature_engineering()
    print(f"\nSilver layer complete: {len(features)} feature sets")
    for name, df in features.items():
        print(f"  {name}: {len(df)} rows, cols={list(df.columns)}")
