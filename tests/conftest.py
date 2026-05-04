"""
Shared pytest fixtures for NZ Habitat Intelligence tests.
Provides reusable test data and mocks across all test modules.
"""
import json
import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

import numpy as np
import pandas as pd
import pytest


@pytest.fixture(scope="session")
def project_root():
    """Return project root directory."""
    return Path(__file__).parent.parent.parent


@pytest.fixture(scope="session")
def data_pipeline_root(project_root):
    """Return data_pipeline directory."""
    return project_root / "data_pipeline"


@pytest.fixture(scope="function")
def temp_dir():
    """Create a temporary directory for testing file operations."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture(scope="function")
def sample_bronze_world_bank():
    """Sample World Bank GDP data for testing."""
    return pd.DataFrame({
        "country": ["NZL"] * 10,
        "indicator": ["NY.GDP.MKTP.KD.ZG"] * 10,
        "year": list(range(2013, 2023)),
        "value": [2.5, 3.0, 2.2, 3.1, 2.8, 1.2, -1.0, 5.6, 2.4, 2.8],
    })


@pytest.fixture(scope="function")
def sample_bronze_population():
    """Sample Stats NZ population data for testing."""
    return pd.DataFrame({
        "region": ["Auckland", "Wellington", "Christchurch", "Hamilton", "Tauranga"] * 2,
        "year": [2020] * 5 + [2021] * 5,
        "population": [1570000, 500000, 380000, 175000, 140000] * 2,
        "growth_rate": [2.1, 1.5, 1.8, 2.5, 3.0] * 2,
    })


@pytest.fixture(scope="function")
def sample_bronze_rbnz_ocr():
    """Sample RBNZ OCR data for testing."""
    dates = pd.date_range("2020-01-01", periods=24, freq="M")
    return pd.DataFrame({
        "date": dates,
        "indicator": ["OCR"] * 24,
        "value": [1.75, 1.75, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25,
                  0.25, 0.25, 0.50, 0.50, 0.50, 0.50, 0.50, 0.50, 0.50, 0.50,
                  0.50, 0.50, 0.50, 0.50],
    })


@pytest.fixture(scope="function")
def sample_bronze_mbie_tourism():
    """Sample MBIE regional tourism data for testing."""
    return pd.DataFrame({
        "region": ["Auckland", "Queenstown", "Rotorua", "Wellington", "Christchurch"] * 2,
        "year": [2020] * 5 + [2021] * 5,
        "visitors": [4100000, 2100000, 950000, 1200000, 1050000] * 2,
        "growth_yoy": [3.2, 8.5, 2.1, 1.5, 2.3] * 2,
        "seasonal_index": [1.0, 1.8, 0.9, 0.7, 0.8] * 2,
    })


@pytest.fixture(scope="function")
def sample_bronze_stats_nz_building_consents():
    """Sample Stats NZ building consents data for testing."""
    return pd.DataFrame({
        "region": ["Auckland", "Wellington", "Christchurch", "Hamilton", "Tauranga"] * 2,
        "year": [2020] * 5 + [2021] * 5,
        "consents": [14500, 4200, 3800, 2100, 1800] * 2,
        "growth_yoy": [5.2, 3.1, 2.8, 8.5, 12.3] * 2,
    })


@pytest.fixture(scope="function")
def sample_bronze_all(sample_bronze_world_bank, sample_bronze_population,
                      sample_bronze_rbnz_ocr, sample_bronze_mbie_tourism,
                      sample_bronze_stats_nz_building_consents):
    """Combined bronze data from all sources."""
    return {
        "world_bank": {"gdp": sample_bronze_world_bank},
        "stats_nz": {
            "population": sample_bronze_population,
            "building_consents": sample_bronze_stats_nz_building_consents,
        },
        "rbnz": {"ocr": sample_bronze_rbnz_ocr},
        "mbie": {"regional_tourism": sample_bronze_mbie_tourism},
    }


@pytest.fixture(scope="function")
def sample_silver_affordability():
    """Sample silver layer affordability feature."""
    return pd.DataFrame({
        "region": ["Auckland", "Wellington", "Christchurch", "Hamilton", "Tauranga"] * 2,
        "year": [2020] * 5 + [2021] * 5,
        "affordability_index": [45.2, 52.1, 48.5, 58.3, 55.1] * 2,
        "median_price": [1050000, 780000, 520000, 485000, 620000] * 2,
        "median_income": [92000, 85000, 72000, 68000, 71000] * 2,
        "price_to_income_ratio": [11.4, 9.2, 7.2, 7.1, 8.7] * 2,
    })


@pytest.fixture(scope="function")
def sample_silver_tourism_pressure():
    """Sample silver layer tourism pressure feature."""
    return pd.DataFrame({
        "region": ["Auckland", "Queenstown", "Rotorua", "Wellington", "Christchurch"] * 2,
        "year": [2020] * 5 + [2021] * 5,
        "pressure_index": [72.5, 89.2, 65.8, 58.3, 55.1] * 2,
        "visitor_density": [0.42, 1.85, 0.58, 0.31, 0.28] * 2,
        "seasonal_variation": [0.15, 0.45, 0.22, 0.12, 0.18] * 2,
    })


@pytest.fixture(scope="function")
def sample_silver_interest_rate_lag():
    """Sample silver layer interest rate lag feature."""
    return pd.DataFrame({
        "region": ["Auckland", "Wellington", "Christchurch", "Hamilton", "Tauranga"] * 2,
        "year": [2020] * 5 + [2021] * 5,
        "ocr": [0.25, 0.25, 0.25, 0.25, 0.25] * 2,
        "mortgage_rate": [4.5, 4.3, 4.2, 4.4, 4.5] * 2,
        "lag_effect": [0.72, 0.68, 0.65, 0.70, 0.71] * 2,
    })


@pytest.fixture(scope="function")
def sample_silver_supply_deficit():
    """Sample silver layer supply deficit feature."""
    return pd.DataFrame({
        "region": ["Auckland", "Wellington", "Christchurch", "Hamilton", "Tauranga"] * 2,
        "year": [2020] * 5 + [2021] * 5,
        "deficit_score": [68.5, 45.2, 38.1, 72.8, 78.3] * 2,
        "consent_growth": [5.2, 3.1, 2.8, 8.5, 12.3] * 2,
        "population_growth": [2.1, 1.5, 1.8, 2.5, 3.0] * 2,
    })


@pytest.fixture(scope="function")
def sample_silver_all(sample_silver_affordability, sample_silver_tourism_pressure,
                     sample_silver_interest_rate_lag, sample_silver_supply_deficit):
    """Combined silver features from all sources."""
    return {
        "affordability": sample_silver_affordability,
        "tourism_pressure": sample_silver_tourism_pressure,
        "interest_rate_lag": sample_silver_interest_rate_lag,
        "supply_deficit": sample_silver_supply_deficit,
    }


@pytest.fixture(scope="function")
def sample_kpi_data():
    """Sample KPI data for dashboard testing."""
    return pd.DataFrame({
        "name": [
            "Habitat Intelligence Score",
            "Auckland Affordability Index",
            "Tourism Pressure Index",
            "Supply Deficit Score",
            "GDP Growth Rate",
        ],
        "value": [72.5, 45.2, 68.8, 58.3, 3.2],
        "unit": ["score", "ratio", "index", "score", "%"],
        "description": [
            "Composite housing market health indicator",
            "Price-to-income ratio for Auckland",
            "Tourism demand pressure on housing",
            "Housing supply deficit relative to demand",
            "Annual GDP growth rate",
        ],
        "category": ["general", "affordability", "tourism", "supply", "macro"],
        "source": ["real", "real", "synthetic", "real", "real"],
        "confidence": [85.0, 78.5, 62.0, 82.0, 90.0],
    })


@pytest.fixture(scope="function")
def sample_contract_dict():
    """Sample contract dictionary."""
    return {
        "artifact_name": "test_indicator",
        "artifact_path": "/tmp/test.parquet",
        "layer": "silver",
        "source": "real",
        "source_name": "test_api",
        "generated_date": datetime.now().isoformat(),
        "version": "1.0",
    }


@pytest.fixture(scope="function")
def sample_contract_file(temp_dir, sample_contract_dict):
    """Create a temporary contract file."""
    contract_path = temp_dir / "test_indicator.contract.json"
    with open(contract_path, "w") as f:
        json.dump(sample_contract_dict, f)
    return contract_path


@pytest.fixture(scope="function")
def mock_data_loader():
    """Mock DataLoader for dashboard testing."""
    from app.utils.data_loader import DataLoader

    class MockDataLoader(DataLoader):
        def __init__(self):
            self._cache = {}
            self._initialized = True
            self.base_dir = ""
            self.last_loaded_file = {}

    return MockDataLoader()


@pytest.fixture
def sample_quality_indicators():
    """Sample quality indicators data."""
    return {
        "data_sources": {
            "world_bank": {"records": 5000, "freshness_days": 30, "confidence": 85},
            "stats_nz": {"records": 12000, "freshness_days": 14, "confidence": 92},
            "rbnz": {"records": 800, "freshness_days": 7, "confidence": 95},
        },
        "overall_quality": "good",
        "total_kpis": 28,
        "high_confidence_kpis": 22,
    }


@pytest.fixture
def sample_executive_summary():
    """Sample executive summary data."""
    return {
        "habitat_intelligence_score": 72.5,
        "score_trend": "up",
        "top_regions": ["Auckland", "Wellington", "Christchurch"],
        "key_insights": [
            "Housing affordability remains a challenge in Auckland",
            "Tourism pressure easing in Queenstown",
            "Supply deficit improving in Christchurch",
        ],
        "alerts": [],
    }