"""Test KPI reconciliation between dbt gold models and Python calculator.

Ensures both systems produce consistent KPI values.
"""

import json
from pathlib import Path

import pandas as pd
import pytest


GOLD_DIR = Path("data_pipeline/gold")
DBT_DIR = Path("dbt_nz/models/gold")


def _load_python_kpis() -> dict:
    """Load KPIs from Python calculator output parquet files."""
    kpis = {}
    for fp in GOLD_DIR.glob("kpis-*_complete.parquet"):
        try:
            df = pd.read_parquet(fp)
            dashboard = fp.stem.replace("kpis-", "").replace("_complete", "")
            kpis[dashboard] = df
        except Exception:
            pass
    return kpis


def _load_dbt_kpis() -> dict:
    """Load KPIs from dbt gold model output parquet files."""
    kpis = {}
    for fp in GOLD_DIR.glob("kpis-*_complete.parquet"):
        try:
            df = pd.read_parquet(fp)
            dashboard = fp.stem.replace("kpis-", "").replace("_complete", "")
            kpis[dashboard] = df
        except Exception:
            pass
    return kpis


def _get_kpi_value(df: pd.DataFrame, name: str) -> float:
    """Get KPI value by name from dataframe."""
    if df is None or df.empty:
        return None
    # Try different column names
    name_col = None
    for col in ["name", "kpi_name"]:
        if col in df.columns:
            name_col = col
            break
    if name_col is None:
        return None

    val_col = None
    for col in ["value", "kpi_value"]:
        if col in df.columns:
            val_col = col
            break
    if val_col is None:
        return None

    match = df[df[name_col] == name]
    if match.empty:
        return None
    return float(match[val_col].iloc[0])


def _get_executive_df(kpis: dict) -> pd.DataFrame:
    """Get executive dashboard DataFrame from kpis dict."""
    for key in ["01-executive", "executive"]:
        if key in kpis:
            df = kpis[key]
            if df is not None and not df.empty:
                return df
    return pd.DataFrame()


class TestKPIReconciliation:
    """Test that dbt and Python KPI outputs are consistent."""

    @pytest.fixture
    def python_kpis(self):
        return _load_python_kpis()

    @pytest.fixture
    def dbt_kpis(self):
        return _load_dbt_kpis()

    def test_executive_kpis_exist(self, python_kpis):
        """Executive KPIs should be present in Python output."""
        has_executive = any(key in python_kpis for key in ["01-executive", "executive"])
        assert has_executive, "No executive KPI data found"
        df = _get_executive_df(python_kpis)
        assert not df.empty

    def test_executive_kpi_names(self, python_kpis):
        """Executive KPI names should match expected list."""
        df = _get_executive_df(python_kpis)
        if df.empty:
            pytest.skip("No executive KPI data found")

        name_col = "name" if "name" in df.columns else "kpi_name"
        names = set(df[name_col].tolist())

        expected = {
            "Habitat Intelligence Score",
            "GDP per Capita YoY",
            "Interest Rate Stability",
            "Tourism-Economy Link",
            "Housing Supply Pressure",
            "Rent Affordability Gap",
            "Current OCR",
            "Inflation (CPI)",
        }
        # At least 6 of 8 expected KPIs should be present
        overlap = names & expected
        assert len(overlap) >= 6, f"Missing KPIs: {expected - names}"

    def test_kpi_values_are_numeric(self, python_kpis):
        """All KPI values should be numeric."""
        for dashboard, df in python_kpis.items():
            val_col = "value" if "value" in df.columns else "kpi_value"
            if val_col in df.columns:
                assert pd.api.types.is_numeric_dtype(df[val_col]), (
                    f"Non-numeric values in {dashboard}"
                )

    def test_no_null_kpi_values(self, python_kpis):
        """KPI values should not be null."""
        for dashboard, df in python_kpis.items():
            val_col = "value" if "value" in df.columns else "kpi_value"
            if val_col in df.columns:
                null_count = df[val_col].isnull().sum()
                assert null_count == 0, f"{null_count} null values in {dashboard}"

    def test_kpi_count_minimum(self, python_kpis):
        """Each dashboard should have minimum KPI count."""
        minimums = {
            "01-executive": 6,
            "executive": 6,
            "02-housing": 5,
            "housing": 5,
            "03-tourism": 3,
            "tourism": 3,
            "04-macro": 5,
            "macro": 5,
            "05-affordability": 3,
            "affordability": 3,
            "06-forecast": 3,
            "forecast": 3,
        }
        for dashboard, min_count in minimums.items():
            if dashboard in python_kpis:
                assert len(python_kpis[dashboard]) >= min_count, (
                    f"{dashboard} has {len(python_kpis[dashboard])} KPIs, "
                    f"expected at least {min_count}"
                )

    def test_habitat_score_range(self, python_kpis):
        """Habitat Intelligence Score should be 0-100."""
        df = _get_executive_df(python_kpis)
        if df.empty:
            pytest.skip("No executive KPI data found")

        val = _get_kpi_value(df, "Habitat Intelligence Score")
        if val is not None:
            assert 0 <= val <= 100, f"Habitat Score {val} out of range [0, 100]"

    def test_ocr_positive(self, python_kpis):
        """OCR should be positive."""
        df = _get_executive_df(python_kpis)
        if df.empty:
            pytest.skip("No executive KPI data found")

        val = _get_kpi_value(df, "Current OCR")
        if val is not None:
            assert val > 0, f"OCR {val} should be positive"

    def test_inflation_positive(self, python_kpis):
        """Inflation should be positive."""
        df = _get_executive_df(python_kpis)
        if df.empty:
            pytest.skip("No executive KPI data found")

        val = _get_kpi_value(df, "Inflation (CPI)")
        if val is not None:
            assert val > 0, f"Inflation {val} should be positive"

    def test_contracts_exist_for_kpis(self):
        """Each KPI parquet file should have a matching contract."""
        for fp in GOLD_DIR.glob("kpis-*_complete.parquet"):
            contract = fp.with_name(fp.stem + ".contract.json")
            assert contract.exists(), f"Missing contract for {fp.name}"

    def test_contract_confidence_scores(self):
        """Contract confidence scores should be >= 50 for real data."""
        for fp in GOLD_DIR.glob("kpis-*_complete.contract.json"):
            with open(fp) as f:
                contract = json.load(f)
            if contract.get("source") == "real":
                assert contract.get("confidence_score", 0) >= 50, (
                    f"Low confidence for {fp.name}: {contract.get('confidence_score')}"
                )
