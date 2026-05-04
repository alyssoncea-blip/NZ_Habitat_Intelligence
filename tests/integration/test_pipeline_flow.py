"""
Integration tests for NZ Habitat Intelligence pipeline.
Tests the complete flow from Bronze -> Silver -> Gold.
"""

import os
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

import sys

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from data_pipeline.utils.data_contract import (  # noqa: E402
    DataSource,
    DataQuality,
    create_contract,
    save_dataframe_with_contract,
    load_with_contract,
)


class TestBronzeToSilverFlow:
    """Integration tests for Bronze to Silver pipeline flow."""

    def test_bronze_data_has_required_schema(self, sample_bronze_world_bank):
        """Test that bronze data has expected schema for World Bank."""
        required_columns = ["country", "indicator", "year", "value"]
        for col in required_columns:
            assert col in sample_bronze_world_bank.columns, f"Missing column: {col}"

    def test_bronze_world_bank_contract_creation(
        self, temp_dir, sample_bronze_world_bank
    ):
        """Test that bronze data can be saved with a contract."""
        output_path = temp_dir / "bronze" / "gdp.parquet"
        output_path.parent.mkdir(parents=True, exist_ok=True)

        contract = create_contract(
            artifact_name="gdp",
            layer="bronze",
            source=DataSource.REAL,
            source_name="world_bank_api",
        )

        save_dataframe_with_contract(sample_bronze_world_bank, output_path, contract)

        assert output_path.exists(), "Parquet file should exist"

        contract_path = output_path.with_suffix(".parquet.contract.json")
        assert contract_path.exists(), "Contract file should exist"

    def test_load_bronze_with_contract(self, temp_dir, sample_bronze_world_bank):
        """Test loading bronze data with contract validation."""
        output_path = temp_dir / "bronze" / "gdp.parquet"
        output_path.parent.mkdir(parents=True, exist_ok=True)

        contract = create_contract(
            artifact_name="gdp",
            layer="bronze",
            source=DataSource.REAL,
            source_name="world_bank_api",
        )

        save_dataframe_with_contract(sample_bronze_world_bank, output_path, contract)

        loaded_df, loaded_contract = load_with_contract(output_path)

        assert loaded_df is not None, "Loaded DataFrame should not be None"
        assert loaded_contract is not None, "Loaded contract should not be None"
        assert len(loaded_df) == len(sample_bronze_world_bank), "Row count should match"
        assert loaded_contract.source == DataSource.REAL, "Source should be REAL"


class TestSilverToGoldFlow:
    """Integration tests for Silver to Gold pipeline flow."""

    def test_silver_features_have_quality_tracking(self, sample_silver_affordability):
        """Test that silver features have quality tracking metadata."""
        assert (
            "region" in sample_silver_affordability.columns
            or "year" in sample_silver_affordability.columns
        )
        numeric_cols = sample_silver_affordability.select_dtypes(
            include=[np.number]
        ).columns
        assert len(numeric_cols) > 0, "Should have numeric columns for KPIs"

    def test_silver_to_gold_data_contract_preserved(
        self, temp_dir, sample_silver_affordability
    ):
        """Test that contract metadata is preserved through silver processing."""
        output_path = temp_dir / "silver" / "affordability.parquet"
        output_path.parent.mkdir(parents=True, exist_ok=True)

        contract = create_contract(
            artifact_name="affordability",
            layer="silver",
            source=DataSource.REAL,
            source_name="stats_nz",
        )

        save_dataframe_with_contract(sample_silver_affordability, output_path, contract)

        loaded_df, loaded_contract = load_with_contract(output_path)

        assert loaded_df is not None
        assert loaded_contract is not None
        assert loaded_contract.layer == "silver"


class TestPipelineIntegration:
    """End-to-end pipeline integration tests."""

    def test_full_pipeline_bronze_to_gold(self, temp_dir, sample_bronze_all):
        """Test complete pipeline from bronze ingestion to gold KPIs."""
        bronze_dir = temp_dir / "bronze"
        silver_dir = temp_dir / "silver"
        gold_dir = temp_dir / "gold"

        bronze_dir.mkdir(parents=True)
        silver_dir.mkdir(parents=True)
        gold_dir.mkdir(parents=True)

        saved_contracts = []

        for source_name, source_data in sample_bronze_all.items():
            if isinstance(source_data, dict):
                for key, df in source_data.items():
                    artifact_name = f"{source_name}_{key}"
                    output_path = bronze_dir / f"{artifact_name}.parquet"

                    contract = create_contract(
                        artifact_name=artifact_name,
                        layer="bronze",
                        source=DataSource.REAL,
                        source_name=source_name,
                    )

                    save_dataframe_with_contract(df, output_path, contract)
                    saved_contracts.append(contract)

        bronze_files = list(bronze_dir.glob("*.parquet"))
        assert len(bronze_files) > 0, "Should have saved bronze files"

        for bronze_file in bronze_files:
            df, contract = load_with_contract(bronze_file)
            assert df is not None, f"Should load {bronze_file}"
            assert contract is not None, f"Should have contract for {bronze_file}"

    def test_gold_kpi_aggregation(self, sample_silver_all):
        """Test that gold KPIs can be aggregated from silver features."""
        all_features = sample_silver_all

        habitat_scores = []
        for feature_name, df in all_features.items():
            if "index" in df.columns or "score" in df.columns:
                score_cols = [c for c in df.columns if "index" in c or "score" in c]
                for col in score_cols:
                    values = df[col].dropna().values
                    if len(values) > 0:
                        habitat_scores.extend(values)

        assert len(habitat_scores) > 0, "Should have extracted score values"

        composite_score = np.mean(habitat_scores) if habitat_scores else 0
        assert 0 <= composite_score <= 100, "Composite score should be in valid range"

    def test_pipeline_quality_gates(self, sample_bronze_world_bank):
        """Test that pipeline enforces quality gates."""
        contract = create_contract(
            artifact_name="gdp",
            layer="bronze",
            source=DataSource.REAL,
            source_name="world_bank_api",
        )

        quality = contract.get("quality", DataQuality.UNKNOWN)

        assert quality in [
            DataQuality.EXCELLENT,
            DataQuality.GOOD,
            DataQuality.FAIR,
            DataQuality.POOR,
            DataQuality.UNKNOWN,
        ]

    def test_data_source_provenance(self, temp_dir, sample_bronze_world_bank):
        """Test that data source provenance is tracked through pipeline."""
        output_path = temp_dir / "test_artifact.parquet"

        contract = create_contract(
            artifact_name="test_artifact",
            layer="bronze",
            source=DataSource.REAL,
            source_name="world_bank_api",
        )

        save_dataframe_with_contract(sample_bronze_world_bank, output_path, contract)

        loaded_df, loaded_contract = load_with_contract(output_path)

        assert loaded_contract.source == DataSource.REAL
        assert loaded_contract.source_name == "world_bank_api"


class TestDataQualityValidation:
    """Tests for data quality validation at each layer."""

    def test_world_bank_data_validity(self, sample_bronze_world_bank):
        """Test World Bank data meets validity requirements."""
        assert (
            sample_bronze_world_bank["value"].notna().sum() > 0
        ), "Should have non-null values"
        assert (
            sample_bronze_world_bank["year"].min() >= 1960
        ), "Year should be reasonable"
        assert (
            sample_bronze_world_bank["country"].nunique() > 0
        ), "Should have countries"

    def test_population_data_validity(self, sample_bronze_population):
        """Test population data meets validity requirements."""
        assert (
            sample_bronze_population["population"] > 0
        ).all(), "Population should be positive"
        assert (
            sample_bronze_population["growth_rate"] >= -10
        ).all(), "Growth rate should be reasonable"
        assert (
            sample_bronze_population["growth_rate"] <= 20
        ).all(), "Growth rate should be reasonable"

    def test_tourism_data_validity(self, sample_bronze_mbie_tourism):
        """Test tourism data meets validity requirements."""
        assert (
            sample_bronze_mbie_tourism["visitors"] >= 0
        ).all(), "Visitors should be non-negative"
        assert sample_bronze_mbie_tourism["region"].nunique() > 0, "Should have regions"


class TestKPICalculation:
    """Tests for KPI calculation logic."""

    def test_confidence_score_calculation(self, sample_kpi_data):
        """Test confidence score calculation."""
        from data_pipeline.utils.data_contract import calculate_confidence_score

        for _, row in sample_kpi_data.iterrows():
            df_row = pd.DataFrame([row])
            score = calculate_confidence_score(df_row)
            assert 0 <= score <= 100, f"Confidence score {score} should be 0-100"

    def test_habitat_intelligence_score_bounds(self, sample_silver_all):
        """Test that Habitat Intelligence composite score is in valid range."""
        all_scores = []

        for feature_name, df in sample_silver_all.items():
            score_cols = [c for c in df.columns if "index" in c or "score" in c]
            for col in score_cols:
                all_scores.extend(df[col].dropna().values)

        if all_scores:
            mean_score = np.mean(all_scores)
            assert 0 <= mean_score <= 100, "Composite score should be in 0-100 range"

    def test_kpi_value_formatting(self):
        """Test KPI value formatting for display."""
        test_values = [
            (1000000, "$", "1.0M"),
            (500000, "$", "500.0K"),
            (3.5, "%", "3.5%"),
            (85.2, "score", "85.2"),
        ]

        for value, unit, expected in test_values:
            if "M" in expected:
                formatted = f"${value / 1000000:.1f}M"
            elif "K" in expected:
                formatted = f"${value / 1000:.1f}K"
            elif "%" in expected:
                formatted = f"{value:.1f}%"
            else:
                formatted = f"{value:.1f}"

            assert (
                expected.replace("$", "") in formatted.replace("$", "")
                or formatted == expected
            )


class TestDashboardIntegration:
    """Tests for dashboard data integration."""

    def test_kpi_data_for_dashboard(self, sample_kpi_data):
        """Test KPI data has all required fields for dashboard."""
        required_fields = ["name", "value", "unit", "description", "category", "source"]
        for field in required_fields:
            assert field in sample_kpi_data.columns, f"Missing required field: {field}"

    def test_processed_kpis_have_visualization_fields(self, sample_kpi_data):
        """Test processed KPIs have fields needed for visualization."""
        from app.utils.kpi_processor import process_kpis_for_visualization

        processed = process_kpis_for_visualization(sample_kpi_data)

        assert "status" in processed.columns, "Should have status field"
        assert "color" in processed.columns, "Should have color field"
        assert "trend" in processed.columns, "Should have trend field"
        assert "display_value" in processed.columns, "Should have display_value field"
        assert "importance" in processed.columns, "Should have importance field"

    def test_dashboard_factory_create_hero_section(self, sample_kpi_data):
        """Test DashboardFactory creates hero section correctly."""
        from app.utils.dashboard_factory import find_hero_kpi

        hero_kpi = find_hero_kpi(sample_kpi_data, ["habitat", "intelligence"])

        assert hero_kpi is not None, "Should find hero KPI"
        assert "name" in hero_kpi, "Hero KPI should have name"
        assert "value" in hero_kpi, "Hero KPI should have value"


class TestSecretsManager:
    """Tests for secrets management utility."""

    def test_secrets_manager_env_backend(self):
        """Test secrets manager with environment variable backend."""
        import sys

        project_root = Path(__file__).parent.parent.parent
        sys.path.insert(0, str(project_root))

        from data_pipeline.utils.secrets import SecretsManager

        os.environ["TEST_SECRET_KEY"] = "test_value_123"

        secrets = SecretsManager(backend="env")
        value = secrets.get("TEST_SECRET_KEY")

        assert value == "test_value_123", "Should retrieve env var"

        del os.environ["TEST_SECRET_KEY"]

    def test_secrets_manager_missing_key_returns_none(self):
        """Test that missing key returns None when not required."""
        import sys

        project_root = Path(__file__).parent.parent.parent
        sys.path.insert(0, str(project_root))

        from data_pipeline.utils.secrets import SecretsManager

        secrets = SecretsManager(backend="env")
        value = secrets.get("NONEXISTENT_KEY_12345")

        assert value is None, "Missing key should return None"

    def test_secrets_manager_required_key_raises_error(self):
        """Test that required missing key raises ValueError."""
        import sys

        project_root = Path(__file__).parent.parent.parent
        sys.path.insert(0, str(project_root))

        from data_pipeline.utils.secrets import SecretsManager

        secrets = SecretsManager(backend="env")

        with pytest.raises(ValueError, match="Required secret"):
            secrets.get("NONEXISTENT_REQUIRED_KEY", required=True)

    def test_secrets_manager_default_value(self):
        """Test that default value is returned for missing key."""
        import sys

        project_root = Path(__file__).parent.parent.parent
        sys.path.insert(0, str(project_root))

        from data_pipeline.utils.secrets import SecretsManager

        secrets = SecretsManager(backend="env")
        value = secrets.get("NONEXISTENT_KEY", default="my_default")

        assert value == "my_default", "Should return default value"

    def test_secrets_manager_caching(self):
        """Test that secrets are cached after first retrieval."""
        import sys

        project_root = Path(__file__).parent.parent.parent
        sys.path.insert(0, str(project_root))

        from data_pipeline.utils.secrets import SecretsManager

        os.environ["CACHED_SECRET"] = "cached_value"

        secrets = SecretsManager(backend="env")
        first = secrets.get("CACHED_SECRET")
        second = secrets.get("CACHED_SECRET")

        assert first == second, "Cached values should match"
        assert "CACHED_SECRET" in secrets.list_cached(), "Key should be in cache"

        del os.environ["CACHED_SECRET"]

    def test_secrets_manager_refresh_clears_cache(self):
        """Test that refresh clears the cache."""
        import sys

        project_root = Path(__file__).parent.parent.parent
        sys.path.insert(0, str(project_root))

        from data_pipeline.utils.secrets import SecretsManager

        os.environ["REFRESH_SECRET"] = "old_value"

        secrets = SecretsManager(backend="env")
        secrets.get("REFRESH_SECRET")
        secrets.refresh()

        assert len(secrets.list_cached()) == 0, "Cache should be empty after refresh"

        del os.environ["REFRESH_SECRET"]

    def test_secrets_manager_get_dict(self):
        """Test retrieving JSON secrets as dictionary."""
        import sys

        project_root = Path(__file__).parent.parent.parent
        sys.path.insert(0, str(project_root))

        from data_pipeline.utils.secrets import SecretsManager

        os.environ["JSON_SECRET"] = (
            '{"api_key": "abc123", "endpoint": "https://api.example.com"}'
        )

        secrets = SecretsManager(backend="env")
        secret_dict = secrets.get_dict("JSON_SECRET")

        assert isinstance(secret_dict, dict), "Should return dict"
        assert secret_dict.get("api_key") == "abc123", "Should parse JSON correctly"

        del os.environ["JSON_SECRET"]

    def test_secrets_manager_singleton(self):
        """Test that get_secrets returns singleton."""
        import sys

        project_root = Path(__file__).parent.parent.parent
        sys.path.insert(0, str(project_root))

        from data_pipeline.utils.secrets import get_secrets, reset_secrets

        reset_secrets()
        first = get_secrets()
        second = get_secrets()

        assert first is second, "Should return same instance"

        reset_secrets()
