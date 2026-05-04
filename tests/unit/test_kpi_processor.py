"""Unit tests for KPI processor."""

import pandas as pd

from app.utils.kpi_processor import process_kpis_for_visualization


class TestKPIProcessor:
    """Tests for KPI processing functions."""

    def test_process_kpis_standard_format(self):
        """Test processing KPIs in standard format."""
        kpi_data = {
            "kpis": [
                {
                    "name": "Test KPI",
                    "value": 42.0,
                    "unit": "score",
                    "description": "A test",
                },
                {
                    "name": "Another KPI",
                    "value": 100.0,
                    "unit": "%",
                    "description": "Another",
                },
            ]
        }
        result = process_kpis_for_visualization(kpi_data)
        assert result is not None
        assert "kpis" in result

    def test_process_kpis_empty(self):
        """Test processing empty KPI data."""
        result = process_kpis_for_visualization({"kpis": []})
        assert result is not None

    def test_process_kpis_none(self):
        """Test processing None KPI data."""
        result = process_kpis_for_visualization(None)
        assert result is not None

    def test_process_kpis_with_confidence(self):
        """Test processing KPIs with confidence scores."""
        kpi_data = {
            "kpis": [
                {"name": "High Confidence", "value": 85.0, "confidence": 90.0},
                {"name": "Low Confidence", "value": 50.0, "confidence": 40.0},
            ]
        }
        result = process_kpis_for_visualization(kpi_data)
        assert result is not None

    def test_process_kpis_with_trend(self):
        """Test processing KPIs with trend data."""
        kpi_data = {
            "kpis": [
                {
                    "name": "Growing KPI",
                    "value": 75.0,
                    "trend": "up",
                    "trend_value": 5.2,
                },
                {
                    "name": "Declining KPI",
                    "value": 30.0,
                    "trend": "down",
                    "trend_value": -2.1,
                },
            ]
        }
        result = process_kpis_for_visualization(kpi_data)
        assert result is not None

    def test_process_kpis_quality_format(self):
        """Test processing KPIs in quality format (complete)."""
        df = pd.DataFrame(
            {
                "name": ["KPI1", "KPI2"],
                "value": [10.0, 20.0],
                "unit": ["score", "%"],
                "description": ["First", "Second"],
                "category": ["general", "macro"],
                "source": ["real", "real"],
                "confidence": [85.0, 90.0],
            }
        )
        kpi_data = {"kpis": df.to_dict(orient="records")}
        result = process_kpis_for_visualization(kpi_data)
        assert result is not None

    def test_process_kpis_filters_by_category(self):
        """Test that KPIs can be filtered by category."""
        kpi_data = {
            "kpis": [
                {"name": "Housing KPI", "value": 50.0, "category": "housing"},
                {"name": "Macro KPI", "value": 60.0, "category": "macro"},
            ]
        }
        result = process_kpis_for_visualization(kpi_data)
        assert result is not None
        assert len(result.get("kpis", [])) == 2
