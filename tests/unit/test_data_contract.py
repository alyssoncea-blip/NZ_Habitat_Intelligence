"""Unit tests for data contract creation, loading, and validation."""
import json
from datetime import datetime
from pathlib import Path

import pandas as pd
import pytest

from data_pipeline.utils.data_contract import (
    DataContract,
    DataSource,
    DataQuality,
    create_contract,
    load_with_contract,
    save_dataframe_with_contract,
)


class TestDataContract:
    """Tests for DataContract dataclass."""

    def test_create_contract_minimal(self):
        """Test creating a contract with minimal fields."""
        contract = DataContract(
            artifact_name="test_artifact",
            artifact_path="/tmp/test.parquet",
            layer="bronze",
            source=DataSource.REAL,
            source_name="test_api",
        )
        assert contract.artifact_name == "test_artifact"
        assert contract.layer == "bronze"
        assert contract.source == DataSource.REAL
        assert contract.confidence_score >= 0
        assert contract.is_trusted is False

    def test_create_contract_with_quality(self):
        """Test creating a contract with quality metrics."""
        contract = DataContract(
            artifact_name="test_artifact",
            artifact_path="/tmp/test.parquet",
            layer="silver",
            source=DataSource.REAL,
            source_name="test_api",
            quality=DataQuality.GOOD,
            null_percentage=2.5,
            record_count=100,
        )
        assert contract.quality == DataQuality.GOOD
        assert contract.null_percentage == 2.5

    def test_confidence_score_calculation(self):
        """Test that confidence score is calculated correctly."""
        contract = DataContract(
            artifact_name="test",
            artifact_path="/tmp/test.parquet",
            layer="gold",
            source=DataSource.REAL,
            source_name="test",
            record_count=1000,
        )
        assert 0 <= contract.confidence_score <= 100

    def test_is_trusted_high_confidence_real(self):
        """Test trusted status for high confidence real data."""
        contract = DataContract(
            artifact_name="test",
            artifact_path="/tmp/test.parquet",
            layer="gold",
            source=DataSource.REAL,
            source_name="test",
            record_count=1000,
            quality=DataQuality.EXCELLENT,
            confidence_score=90.0,
        )
        assert contract.confidence_score >= 70
        assert contract.is_trusted is True

    def test_is_not_trusted_fallback(self):
        """Test not trusted status for fallback data."""
        contract = DataContract(
            artifact_name="test",
            artifact_path="/tmp/test.parquet",
            layer="bronze",
            source=DataSource.FALLBACK,
            source_name="test",
            record_count=100,
        )
        assert contract.is_trusted is False

    def test_to_dict_roundtrip(self):
        """Test serialization and deserialization."""
        original = DataContract(
            artifact_name="test",
            artifact_path="/tmp/test.parquet",
            layer="silver",
            source=DataSource.REAL,
            source_name="test_api",
            record_count=500,
        )
        d = original.to_dict()
        restored = DataContract.from_dict(d)
        assert restored.artifact_name == original.artifact_name
        assert restored.layer == original.layer
        assert restored.source == original.source
        assert restored.record_count == original.record_count

    def test_save_and_load(self, temp_dir):
        """Test saving and loading contract to file."""
        contract = DataContract(
            artifact_name="test",
            artifact_path=str(temp_dir / "test.parquet"),
            layer="gold",
            source=DataSource.REAL,
            source_name="test_api",
        )
        path = contract.save(str(temp_dir))
        assert Path(path).exists()
        loaded = DataContract.load(path)
        assert loaded.artifact_name == "test"

    def test_parent_contracts(self):
        """Test parent contracts tracking."""
        parent = DataContract(
            artifact_name="parent",
            artifact_path="/tmp/parent.json",
            layer="bronze",
            source=DataSource.REAL,
            source_name="api",
        )
        child = DataContract(
            artifact_name="child",
            artifact_path="/tmp/child.parquet",
            layer="silver",
            source=DataSource.REAL,
            source_name="derived",
            parent_contracts=[parent.to_dict()],
        )
        assert len(child.parent_contracts) == 1
        assert child.parent_contracts[0]["artifact_name"] == "parent"


class TestCreateContract:
    """Tests for create_contract helper function."""

    def test_create_contract_from_dataframe(self, temp_dir):
        """Test creating contract from a DataFrame."""
        df = pd.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})
        contract = create_contract(
            df=df,
            artifact_name="test_df",
            artifact_path=str(temp_dir / "test.parquet"),
            layer="silver",
            source=DataSource.REAL,
            source_name="test",
        )
        assert contract.record_count == 3
        assert contract.artifact_name == "test_df"

    def test_create_contract_empty_dataframe(self, temp_dir):
        """Test creating contract from empty DataFrame."""
        df = pd.DataFrame()
        contract = create_contract(
            df=df,
            artifact_name="empty",
            artifact_path=str(temp_dir / "empty.parquet"),
            layer="silver",
            source=DataSource.REAL,
            source_name="test",
        )
        assert contract.record_count == 0


class TestSaveDataframeWithContract:
    """Tests for save_dataframe_with_contract helper."""

    def test_save_parquet_and_contract(self, temp_dir):
        """Test saving both parquet and contract files."""
        df = pd.DataFrame({"col1": [1, 2], "col2": ["a", "b"]})
        parquet_path, contract_path = save_dataframe_with_contract(
            df=df,
            path=str(temp_dir / "test"),
            artifact_name="test",
            layer="silver",
            source=DataSource.REAL,
            source_name="test",
        )
        assert Path(parquet_path).exists()
        assert Path(contract_path).exists()
        loaded = pd.read_parquet(parquet_path)
        assert len(loaded) == 2

    def test_save_with_notes(self, temp_dir):
        """Test saving with notes."""
        df = pd.DataFrame({"x": [1]})
        _, contract_path = save_dataframe_with_contract(
            df=df,
            path=str(temp_dir / "test"),
            artifact_name="test",
            layer="gold",
            source=DataSource.REAL,
            source_name="test",
            notes="Test data",
        )
        contract = DataContract.load(contract_path)
        assert contract.notes == "Test data"
