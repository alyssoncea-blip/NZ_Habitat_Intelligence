"""Unit tests for Great Expectations validator."""

import json
import sys
from pathlib import Path

import pandas as pd
import pytest

# Add project root to path to import local great_expectations module
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Import using importlib to avoid conflict with installed great_expectations package
import importlib.util  # noqa: E402

spec = importlib.util.spec_from_file_location(
    "nz_ge_validator",
    str(project_root / "great_expectations" / "validate.py"),
)
ge_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ge_module)
NZHabitatValidator = ge_module.NZHabitatValidator


class TestNZHabitatValidator:
    """Tests for NZHabitatValidator class."""

    @pytest.fixture
    def validator(self, tmp_path):
        """Create validator with temporary directories."""
        project_root = tmp_path
        (project_root / "great_expectations" / "expectations").mkdir(parents=True)
        (project_root / "great_expectations" / "validations").mkdir(parents=True)
        (project_root / "data_pipeline" / "bronze").mkdir(parents=True)
        (project_root / "data_pipeline" / "silver").mkdir(parents=True)
        (project_root / "data_pipeline" / "gold").mkdir(parents=True)
        return NZHabitatValidator(str(project_root))

    @pytest.fixture
    def sample_expectation_suite(self):
        """Create a sample expectation suite."""
        return {
            "expectations": [
                {
                    "expectation_type": "expect_table_row_count_to_be_between",
                    "kwargs": {"min_value": 1, "max_value": 10000},
                },
                {
                    "expectation_type": "expect_table_columns_to_match_set",
                    "kwargs": {"column_set": ["name", "value"]},
                },
                {
                    "expectation_type": "expect_column_values_to_not_be_null",
                    "kwargs": {"column": "name", "mostly": 1.0},
                },
            ]
        }

    def test_validator_initialization(self, validator):
        """Test validator initializes correctly."""
        assert validator is not None
        assert validator.project_root is not None

    def test_expectations_dir_exists(self, validator):
        """Test expectations directory is created."""
        assert validator.expectations_dir.exists()
        assert validator.results_dir.exists()

    def test_validate_parquet_passing(
        self, validator, sample_expectation_suite, tmp_path
    ):
        """Test validating a parquet file that passes expectations."""
        # Create expectation suite
        suite_path = validator.expectations_dir / "silver_features.json"
        with open(suite_path, "w") as f:
            json.dump(sample_expectation_suite, f)

        # Create test parquet file
        df = pd.DataFrame({"name": ["A", "B", "C"], "value": [1.0, 2.0, 3.0]})
        parquet_path = tmp_path / "test.parquet"
        df.to_parquet(parquet_path, index=False)

        result = validator.validate_parquet(parquet_path, "silver_features")
        assert result["success"] is True
        assert result["summary"]["passed"] >= 1

    def test_validate_parquet_failing(
        self, validator, sample_expectation_suite, tmp_path
    ):
        """Test validating a parquet file that fails expectations."""
        # Create expectation suite requiring specific columns
        suite = {
            "expectations": [
                {
                    "expectation_type": "expect_table_columns_to_match_set",
                    "kwargs": {"column_set": ["required_col"]},
                }
            ]
        }
        suite_path = validator.expectations_dir / "silver_features.json"
        with open(suite_path, "w") as f:
            json.dump(suite, f)

        # Create test parquet file without required column
        df = pd.DataFrame({"other_col": [1, 2, 3]})
        parquet_path = tmp_path / "test.parquet"
        df.to_parquet(parquet_path, index=False)

        result = validator.validate_parquet(parquet_path, "silver_features")
        assert result["success"] is False

    def test_run_expectations_row_count(self, validator):
        """Test row count expectation."""
        df = pd.DataFrame({"a": [1, 2, 3]})
        suite = {
            "expectations": [
                {
                    "expectation_type": "expect_table_row_count_to_be_between",
                    "kwargs": {"min_value": 1, "max_value": 10},
                }
            ]
        }
        result = validator._run_expectations(df, suite, "test")
        assert result["success"] is True
        assert result["summary"]["passed"] == 1

    def test_run_expectations_columns(self, validator):
        """Test columns expectation."""
        df = pd.DataFrame({"name": ["A"], "value": [1.0]})
        suite = {
            "expectations": [
                {
                    "expectation_type": "expect_table_columns_to_match_set",
                    "kwargs": {"column_set": ["name", "value"]},
                }
            ]
        }
        result = validator._run_expectations(df, suite, "test")
        assert result["success"] is True

    def test_run_expectations_not_null(self, validator):
        """Test not null expectation."""
        df = pd.DataFrame({"name": ["A", "B", None]})
        suite = {
            "expectations": [
                {
                    "expectation_type": "expect_column_values_to_not_be_null",
                    "kwargs": {"column": "name", "mostly": 0.66},
                }
            ]
        }
        result = validator._run_expectations(df, suite, "test")
        assert result["success"] is True

    def test_run_expectations_between(self, validator):
        """Test between expectation."""
        df = pd.DataFrame({"value": [1.0, 2.0, 3.0]})
        suite = {
            "expectations": [
                {
                    "expectation_type": "expect_column_values_to_be_between",
                    "kwargs": {"column": "value", "min_value": 0, "max_value": 10},
                }
            ]
        }
        result = validator._run_expectations(df, suite, "test")
        assert result["success"] is True

    def test_run_expectations_unique(self, validator):
        """Test unique expectation."""
        df = pd.DataFrame({"id": [1, 2, 3]})
        suite = {
            "expectations": [
                {
                    "expectation_type": "expect_column_values_to_be_unique",
                    "kwargs": {"column": "id", "mostly": 1.0},
                }
            ]
        }
        result = validator._run_expectations(df, suite, "test")
        assert result["success"] is True

    def test_validate_bronze_layer_empty(self, validator):
        """Test validating empty bronze layer."""
        results = validator.validate_bronze_layer()
        assert isinstance(results, list)
        assert len(results) == 0

    def test_validate_silver_layer_empty(self, validator):
        """Test validating empty silver layer."""
        results = validator.validate_silver_layer()
        assert isinstance(results, list)
        assert len(results) == 0

    def test_validate_gold_layer_empty(self, validator):
        """Test validating empty gold layer."""
        results = validator.validate_gold_layer()
        assert isinstance(results, list)
        assert len(results) == 0

    def test_run_all_validations(self, validator):
        """Test running all validations on empty layers."""
        results = validator.run_all_validations()
        assert isinstance(results, dict)
        assert "bronze" in results
        assert "silver" in results
        assert "gold" in results
        assert "summary" in results
