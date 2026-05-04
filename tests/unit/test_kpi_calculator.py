"""Unit tests for Gold layer KPI calculator."""
import tempfile
from pathlib import Path

import pandas as pd
import pytest

from data_pipeline.gold.kpi_calculator import KPICalculator


class TestKPICalculator:
    """Tests for KPICalculator class."""

    @pytest.fixture
    def calculator(self, tmp_path):
        """Create KPICalculator with temporary directories."""
        bronze_dir = tmp_path / "bronze"
        silver_dir = tmp_path / "silver"
        gold_dir = tmp_path / "gold"
        bronze_dir.mkdir()
        silver_dir.mkdir()
        gold_dir.mkdir()
        return KPICalculator(
            bronze_dir=str(bronze_dir),
            silver_dir=str(silver_dir),
            gold_dir=str(gold_dir),
        )

    @pytest.fixture
    def sample_silver_features(self):
        """Create sample silver features for testing."""
        return {
            "affordability": pd.DataFrame({
                "region": ["Auckland", "Wellington", "Canterbury"] * 2,
                "year": [2020, 2020, 2020, 2021, 2021, 2021],
                "affordability_index": [45.2, 52.1, 48.5, 43.8, 50.5, 47.2],
                "gdp_per_capita": [8000, 8500, 7200, 8200, 8700, 7400],
                "median_income": [92000, 85000, 72000, 95000, 88000, 75000],
            }),
            "interest_rate_lag": pd.DataFrame({
                "region": ["New Zealand"] * 4,
                "year": [2020, 2021, 2022, 2023],
                "interest_rate": [0.25, 0.50, 2.50, 5.50],
                "interest_rate_3y_volatility": [0.1, 0.2, 1.0, 2.5],
                "interest_rate_yoy_change": [0.0, 100.0, 400.0, 120.0],
                "interest_rate_impact_score": [5.0, 10.0, 40.0, 100.0],
            }),
            "tourism_pressure": pd.DataFrame({
                "region": ["Auckland", "Queenstown", "Rotorua"] * 2,
                "year": [2020, 2020, 2020, 2021, 2021, 2021],
                "tourism_expenditure_millions": [4500, 2100, 950, 3800, 1800, 800],
                "tourism_pressure_index": [72.5, 89.2, 65.8, 68.0, 82.0, 60.0],
                "unemployment_rate": [4.5, 3.0, 4.0, 4.0, 2.5, 3.5],
                "tourism_growth_yoy": [3.2, 8.5, 2.1, -15.5, -14.3, -15.8],
            }),
            "supply_deficit": pd.DataFrame({
                "region": ["Auckland", "Wellington", "Canterbury"] * 2,
                "year": [2020, 2020, 2020, 2021, 2021, 2021],
                "building_consents": [14500, 4200, 3800, 15200, 4500, 4000],
                "population": [1570000, 500000, 600000, 1590000, 510000, 610000],
                "population_growth_yoy": [2.1, 1.5, 1.8, 2.3, 1.7, 2.0],
                "consents_per_1000_people": [9.2, 8.4, 6.3, 9.6, 8.8, 6.6],
                "housing_supply_pressure": [68.5, 45.2, 38.1, 72.8, 50.0, 42.0],
                "housing_supply_gap": [-7.1, -6.9, -4.5, -7.3, -7.1, -4.6],
            }),
            "rent_income_ratio": pd.DataFrame({
                "region": ["Auckland", "Wellington", "Canterbury"] * 2,
                "year": [2020, 2020, 2020, 2021, 2021, 2021],
                "weekly_rent": [520, 450, 380, 550, 470, 400],
                "annual_rent": [27040, 23400, 19760, 28600, 24440, 20800],
                "median_income": [92000, 85000, 72000, 95000, 88000, 75000],
                "rent_income_ratio": [29.4, 27.5, 27.4, 30.1, 27.8, 27.7],
                "general_inflation": [1.5, 1.5, 1.5, 4.0, 4.0, 4.0],
                "rent_inflation": [5.0, 4.5, 5.2, 5.8, 4.4, 5.3],
                "affordability_erosion": [3.5, 3.0, 3.7, 1.8, 0.4, 1.3],
                "cumulative_rent_pressure": [0.0, 0.0, 0.0, 5.8, 4.4, 5.3],
            }),
            "tourism_lag_analysis": pd.DataFrame({
                "region": ["New Zealand"] * 4,
                "year": [2020, 2021, 2022, 2023],
                "macroeconomic_volatility_index": [25.0, 35.0, 65.0, 55.0],
                "gdp_volatility": [0.5, 0.8, 2.0, 1.5],
                "inflation_volatility": [0.3, 0.5, 1.5, 1.2],
                "unemployment_volatility": [0.2, 0.3, 0.8, 0.6],
                "interest_rate_volatility": [0.1, 0.2, 1.0, 2.5],
            }),
        }

    def test_calculator_initialization(self, calculator):
        """Test KPICalculator initializes correctly."""
        assert calculator is not None
        assert calculator.silver_dir is not None
        assert calculator.gold_dir is not None

    def test_safe_float(self, calculator):
        """Test safe float conversion helper."""
        assert calculator._safe_float(42.0) == 42.0
        assert calculator._safe_float(None) == 0.0
        assert calculator._safe_float(float("nan")) == 0.0

    def test_safe_latest(self, calculator):
        """Test safe latest value extraction helper."""
        df = pd.DataFrame({"value": [1.0, 2.0, 3.0]})
        assert calculator._safe_latest(df, "value") == 3.0
        assert calculator._safe_latest(pd.DataFrame(), "value") == 0.0
        assert calculator._safe_latest(None, "value") == 0.0

    def test_calculate_all_with_features(self, calculator, sample_silver_features):
        """Test calculating all KPIs with sample features."""
        # Save sample features to silver directory
        for name, df in sample_silver_features.items():
            filepath = calculator.silver_dir / f"{name}_features.parquet"
            df.to_parquet(filepath, index=False)

        kpis = calculator.calculate_all()
        assert isinstance(kpis, dict)
        assert len(kpis) > 0

    def test_calculate_executive_kpis(self, calculator, sample_silver_features):
        """Test executive KPI calculation."""
        for name, df in sample_silver_features.items():
            filepath = calculator.silver_dir / f"{name}_features.parquet"
            df.to_parquet(filepath, index=False)

        kpis = calculator.calculate_all()
        executive = kpis.get("executive", {})
        assert isinstance(executive, dict)

    def test_calculate_housing_kpis(self, calculator, sample_silver_features):
        """Test housing KPI calculation."""
        for name, df in sample_silver_features.items():
            filepath = calculator.silver_dir / f"{name}_features.parquet"
            df.to_parquet(filepath, index=False)

        kpis = calculator.calculate_all()
        housing = kpis.get("housing", {})
        assert isinstance(housing, dict)

    def test_calculate_tourism_kpis(self, calculator, sample_silver_features):
        """Test tourism KPI calculation."""
        for name, df in sample_silver_features.items():
            filepath = calculator.silver_dir / f"{name}_features.parquet"
            df.to_parquet(filepath, index=False)

        kpis = calculator.calculate_all()
        tourism = kpis.get("tourism", {})
        assert isinstance(tourism, dict)

    def test_calculate_macro_kpis(self, calculator, sample_silver_features):
        """Test macro KPI calculation."""
        for name, df in sample_silver_features.items():
            filepath = calculator.silver_dir / f"{name}_features.parquet"
            df.to_parquet(filepath, index=False)

        kpis = calculator.calculate_all()
        macro = kpis.get("macro", {})
        assert isinstance(macro, dict)

    def test_calculate_affordability_kpis(self, calculator, sample_silver_features):
        """Test affordability KPI calculation."""
        for name, df in sample_silver_features.items():
            filepath = calculator.silver_dir / f"{name}_features.parquet"
            df.to_parquet(filepath, index=False)

        kpis = calculator.calculate_all()
        affordability = kpis.get("affordability", {})
        assert isinstance(affordability, dict)

    def test_calculate_forecast_kpis(self, calculator, sample_silver_features):
        """Test forecast KPI calculation."""
        for name, df in sample_silver_features.items():
            filepath = calculator.silver_dir / f"{name}_features.parquet"
            df.to_parquet(filepath, index=False)

        kpis = calculator.calculate_all()
        forecast = kpis.get("forecast", {})
        assert isinstance(forecast, dict)
