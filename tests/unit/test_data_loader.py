"""Unit tests for DataLoader."""

from pathlib import Path

import pandas as pd
import pytest

from app.utils.data_loader import DataLoader


class TestDataLoader:
    """Tests for DataLoader class."""

    @pytest.fixture
    def loader(self, tmp_path):
        """Create a DataLoader with a temporary gold directory."""
        gold_dir = tmp_path / "gold"
        gold_dir.mkdir()
        loader = DataLoader()
        loader.base_dir = str(gold_dir)
        loader._cache.clear()
        loader.last_loaded_file.clear()
        return loader

    def test_load_kpis_for_dashboard_empty(self, loader):
        """Test loading KPIs when no data files exist."""
        result = loader.load_kpis_for_dashboard("executive")
        assert result is None or (isinstance(result, pd.DataFrame) and result.empty)

    def test_load_kpis_for_dashboard_with_data(self, loader, tmp_path):
        """Test loading KPIs when data files exist."""
        gold_dir = Path(loader.base_dir)
        df = pd.DataFrame(
            {
                "name": ["Test KPI"],
                "value": [42.0],
                "unit": ["score"],
                "description": ["A test KPI"],
                "category": ["general"],
                "source": ["real"],
                "confidence": [85.0],
            }
        )
        df.to_parquet(gold_dir / "kpis-01-executive_complete.parquet", index=False)
        loader._cache.clear()

        result = loader.load_kpis_for_dashboard("executive")
        assert result is not None
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 1

    def test_cache_prevents_reload(self, loader, tmp_path):
        """Test that caching prevents redundant file reads."""
        gold_dir = Path(loader.base_dir)
        df = pd.DataFrame(
            {
                "name": ["Cached KPI"],
                "value": [10.0],
                "unit": ["score"],
                "description": ["Cached"],
                "category": ["general"],
                "source": ["real"],
                "confidence": [90.0],
            }
        )
        df.to_parquet(gold_dir / "kpis-01-executive_complete.parquet", index=False)
        loader._cache.clear()

        first = loader.load_kpis_for_dashboard("executive")
        second = loader.load_kpis_for_dashboard("executive")
        assert first is second

    def test_get_dashboard_summary(self, loader):
        """Test getting summary of all dashboards."""
        summary = loader.get_dashboard_summary()
        assert isinstance(summary, dict)

    def test_singleton_pattern(self):
        """Test that DataLoader uses singleton pattern."""
        loader1 = DataLoader()
        loader2 = DataLoader()
        assert loader1 is loader2

    def test_load_kpis_for_housing(self, loader, tmp_path):
        """Test loading housing KPIs."""
        gold_dir = Path(loader.base_dir)
        df = pd.DataFrame(
            {
                "name": ["House Price Index"],
                "value": [125.5],
                "unit": ["index"],
                "description": ["House price index"],
                "category": ["housing"],
                "source": ["real"],
                "confidence": [88.0],
            }
        )
        df.to_parquet(gold_dir / "kpis-02-housing_complete.parquet", index=False)
        loader._cache.clear()

        result = loader.load_kpis_for_dashboard("housing")
        assert result is not None
        assert isinstance(result, pd.DataFrame)

    def test_load_kpis_for_tourism(self, loader, tmp_path):
        """Test loading tourism KPIs."""
        gold_dir = Path(loader.base_dir)
        df = pd.DataFrame(
            {
                "name": ["Tourism Pressure"],
                "value": [65.0],
                "unit": ["index"],
                "description": ["Tourism pressure index"],
                "category": ["tourism"],
                "source": ["real"],
                "confidence": [75.0],
            }
        )
        df.to_parquet(gold_dir / "kpis-03-tourism_complete.parquet", index=False)
        loader._cache.clear()

        result = loader.load_kpis_for_dashboard("tourism")
        assert result is not None
        assert isinstance(result, pd.DataFrame)
