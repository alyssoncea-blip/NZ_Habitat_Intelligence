"""Unit tests for Silver layer feature engineering."""
import json
from pathlib import Path

import pandas as pd
import pytest

from data_pipeline.silver.feature_engineer import FeatureEngineer


class TestFeatureEngineer:
    """Tests for FeatureEngineer class."""

    @pytest.fixture
    def engineer(self, tmp_path):
        """Create FeatureEngineer with temporary directories."""
        bronze_dir = tmp_path / "bronze"
        silver_dir = tmp_path / "silver"
        bronze_dir.mkdir()
        silver_dir.mkdir()
        return FeatureEngineer(bronze_dir=str(bronze_dir), silver_dir=str(silver_dir))

    @pytest.fixture
    def sample_bronze_data(self):
        """Create sample bronze data for testing."""
        return {
            "world_bank": {
                "gdp": pd.DataFrame({
                    "year": [2020, 2021, 2022, 2023],
                    "value": [40000000000.0, 42000000000.0, 44000000000.0, 45000000000.0],
                }),
                "population": pd.DataFrame({
                    "year": [2020, 2021, 2022, 2023],
                    "value": [5000000, 5060000, 5120000, 5190000],
                }),
                "inflation": pd.DataFrame({
                    "year": [2020, 2021, 2022, 2023],
                    "value": [1.5, 4.0, 7.2, 5.7],
                }),
                "unemployment": pd.DataFrame({
                    "year": [2020, 2021, 2022, 2023],
                    "value": [4.5, 4.0, 3.3, 3.9],
                }),
                "interest_rate": pd.DataFrame({
                    "year": [2020, 2021, 2022, 2023],
                    "value": [2.5, 2.5, 4.5, 7.0],
                }),
            },
            "rbnz": {
                "ocr": pd.DataFrame({
                    "date": pd.date_range("2020-01-01", periods=48, freq="M"),
                    "ocr_rate": [0.25] * 24 + [0.50] * 24,
                }),
            },
            "stats_nz": {
                "income": pd.DataFrame({
                    "region": ["Auckland", "Wellington", "Canterbury"] * 2,
                    "year": [2020, 2020, 2020, 2021, 2021, 2021],
                    "median_household_income": [92000, 85000, 72000, 95000, 88000, 75000],
                }),
                "building_consents": pd.DataFrame({
                    "region": ["Auckland", "Wellington", "Canterbury"] * 2,
                    "year": [2020, 2020, 2020, 2021, 2021, 2021],
                    "consents": [14500, 4200, 3800, 15200, 4500, 4000],
                }),
                "population": pd.DataFrame({
                    "region": ["Auckland", "Wellington", "Canterbury"] * 2,
                    "year": [2020, 2020, 2020, 2021, 2021, 2021],
                    "population": [1570000, 500000, 600000, 1590000, 510000, 610000],
                }),
            },
            "mbie": {
                "regional_tourism": pd.DataFrame({
                    "region": ["Auckland", "Queenstown", "Rotorua"] * 2,
                    "year": [2020, 2020, 2020, 2021, 2021, 2021],
                    "tourism_expenditure_nzd_millions": [4500, 2100, 950, 3800, 1800, 800],
                }),
            },
        }

    def test_load_bronze_data_empty(self, engineer):
        """Test loading bronze data when no files exist."""
        data = engineer.load_bronze_data()
        assert isinstance(data, dict)
        assert "world_bank" in data
        assert "rbnz" in data
        assert "stats_nz" in data
        assert "mbie" in data

    def test_load_bronze_data_with_files(self, engineer, sample_bronze_data):
        """Test loading bronze data from JSON files."""
        # Write sample data as JSON files
        for source, datasets in sample_bronze_data.items():
            for name, df in datasets.items():
                # Convert Timestamp columns to strings for JSON serialization
                df_copy = df.copy()
                for col in df_copy.columns:
                    if pd.api.types.is_datetime64_any_dtype(df_copy[col]):
                        df_copy[col] = df_copy[col].astype(str)
                records = df_copy.to_dict(orient="records")
                data = {"data": records, "metadata": {"source": source, "indicator": name}}
                filepath = engineer.bronze_dir / f"{source}_{name}_raw.json"
                with open(filepath, "w") as f:
                    json.dump(data, f)

        data = engineer.load_bronze_data()
        assert isinstance(data, dict)
        # Should have loaded at least some data
        total_dfs = sum(len(v) for v in data.values() if isinstance(v, dict))
        assert total_dfs > 0

    def test_calc_affordability_with_data(self, engineer, sample_bronze_data):
        """Test affordability calculation with sample data."""
        df = engineer._calc_affordability(sample_bronze_data)
        assert df is not None
        assert not df.empty
        assert "affordability_index" in df.columns
        assert "gdp_per_capita" in df.columns

    def test_calc_affordability_empty_data(self, engineer):
        """Test affordability calculation with empty data."""
        empty_data = {"world_bank": {}, "stats_nz": {}}
        df = engineer._calc_affordability(empty_data)
        assert df is None

    def test_calc_interest_rate_lag_with_data(self, engineer, sample_bronze_data):
        """Test interest rate lag calculation with sample data."""
        df = engineer._calc_interest_rate_lag(sample_bronze_data)
        assert df is not None
        assert not df.empty
        assert "ocr_value" in df.columns
        assert "interest_rate_impact_score" in df.columns

    def test_calc_interest_rate_lag_empty_data(self, engineer):
        """Test interest rate lag calculation with empty data."""
        empty_data = {"rbnz": {}, "world_bank": {}}
        df = engineer._calc_interest_rate_lag(empty_data)
        assert df is None

    def test_calc_supply_deficit_with_data(self, engineer, sample_bronze_data):
        """Test supply deficit calculation with sample data."""
        df = engineer._calc_supply_deficit(sample_bronze_data)
        assert df is not None
        assert not df.empty
        assert "building_consents" in df.columns
        assert "region" in df.columns

    def test_calc_supply_deficit_empty_data(self, engineer):
        """Test supply deficit calculation with empty data."""
        empty_data = {"stats_nz": {}}
        df = engineer._calc_supply_deficit(empty_data)
        assert df is None

    def test_calc_tourism_pressure_with_data(self, engineer, sample_bronze_data):
        """Test tourism pressure calculation with sample data."""
        df = engineer._calc_tourism_pressure(sample_bronze_data)
        assert df is not None
        assert not df.empty
        assert "tourism_pressure_index" in df.columns
        assert "region" in df.columns

    def test_calc_rent_income_ratio_with_data(self, engineer, sample_bronze_data):
        """Test rent income ratio calculation with sample data."""
        df = engineer._calc_rent_income_ratio(sample_bronze_data)
        assert df is not None
        assert not df.empty
        assert "rent_to_income_ratio" in df.columns or "annual_rent" in df.columns

    def test_calc_macro_volatility_with_data(self, engineer, sample_bronze_data):
        """Test macro volatility calculation with sample data."""
        df = engineer._calc_macro_volatility(sample_bronze_data)
        assert df is not None
        assert not df.empty
        assert "macroeconomic_volatility_index" in df.columns

    def test_calc_macro_volatility_empty_data(self, engineer):
        """Test macro volatility calculation with insufficient data."""
        empty_data = {"world_bank": {}}
        df = engineer._calc_macro_volatility(empty_data)
        assert df is None

    def test_get_region_population_share(self, engineer):
        """Test region population share helper."""
        shares = {
            "Auckland": 0.330, "Wellington": 0.108, "Canterbury": 0.125,
            "Waikato": 0.088, "Bay of Plenty": 0.065, "Otago": 0.045,
        }
        for region, expected in shares.items():
            assert engineer._get_region_population_share(region) == expected

    def test_save_features(self, engineer, sample_bronze_data):
        """Test saving features to parquet."""
        features = {}
        df = engineer._calc_affordability(sample_bronze_data)
        if df is not None and not df.empty:
            features["affordability"] = df

        if features:
            file_paths = engineer.save_features(features)
            assert "affordability" in file_paths
            assert Path(file_paths["affordability"]).exists()
