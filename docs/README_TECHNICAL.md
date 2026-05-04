# NZ Habitat Intelligence - Technical Architecture

## Overview

NZ Habitat Intelligence is a 3-layer data pipeline (Bronze → Silver → Gold) that consumes real data from New Zealand government sources to generate 28 quality KPIs across 6 executive dashboards.

### Key Achievements
- **Real data integration** (World Bank API, Stats NZ)
- **28 quality KPIs** based on real data (1976-2021)
- **Data contracts** for provenance tracking and quality signals
- **Modular pipeline** with validation and logging
- **Standardized formats** (Parquet, JSON)

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    NZ HABITAT INTELLIGENCE                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐          │
│  │   EXTERNAL   │    │    BRONZE    │    │    SILVER    │          │
│  │    SOURCES   │───▶│  (Raw Data)  │───▶│  (Features)  │          │
│  └──────────────┘    └──────────────┘    └──────────────┘          │
│         │                   │                    │                  │
│         ▼                   ▼                    ▼                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐          │
│  │ World Bank   │    │    JSON      │    │   Parquet    │          │
│  │ Stats NZ     │    │   Files      │    │   Features   │          │
│  │ RBNZ         │    │   .contract  │    │   .contract  │          │
│  │ MBIE         │    └──────────────┘    └──────────────┘          │
│  └──────────────┘                                                   │
│                              │                    │                  │
│                              │                    ▼                  │
│                              │            ┌──────────────┐          │
│                              │            │    GOLD      │          │
│                              └───────────▶│   (KPIs)     │          │
│                                           └──────────────┘          │
│                                                 │                   │
│                                                 ▼                   │
│                                           ┌──────────────┐          │
│                                           │  DASHBOARDS  │          │
│                                           │   (6 KPIs)   │          │
│                                           └──────────────┘          │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Project Structure

```
NZ_Habitat_Intelligence/
├── app/                          # DASHBOARD SYSTEM
│   ├── components/               # Reusable dashboard components
│   │   ├── cards.py              # KPI cards with semantic colors
│   │   ├── charts.py             # Chart components (bar, line, etc.)
│   │   └── layout.py             # Layout components
│   ├── pages/                    # 6 Executive dashboards
│   │   ├── executive.py          # Main dashboard (6 KPIs)
│   │   ├── housing.py            # Housing market dashboard
│   │   ├── tourism.py            # Tourism impact dashboard
│   │   ├── macro.py              # Macro economics dashboard
│   │   ├── affordability.py      # Housing affordability
│   │   └── forecast.py           # Predictive analytics
│   ├── utils/                    # Dashboard utilities
│   │   ├── data_loader.py        # Data loading with contracts
│   │   └── kpi_formatter.py      # KPI value formatting
│   ├── main.py                   # Multi-page app entry
│   └── index.py                  # URL routing
│
├── data_pipeline/                # DATA PIPELINE (3 layers)
│   ├── bronze/                   # RAW DATA INGESTION
│   │   ├── ingestors/            # API ingestors
│   │   │   ├── world_bank_ingestor.py
│   │   │   ├── stats_nz_ingestor.py
│   │   │   ├── rbnz_ingestor.py
│   │   │   ├── trade_me_scraper.py
│   │   │   ├── mbie_tourism_ingestor.py
│   │   │   └── linz_ingestor.py
│   │   ├── bronze_orchestrator.py
│   │   └── *.json                # Raw data files
│   │
│   ├── silver/                   # FEATURE ENGINEERING
│   │   ├── feature_engineer.py   # Feature transformation
│   │   ├── features_metadata.json
│   │   └── *.parquet             # Processed features
│   │
│   ├── gold/                     # KPI CALCULATION
│   │   ├── kpi_calculator.py     # KPI formulas
│   │   ├── kpis_metadata.json
│   │   └── kpis_*.parquet        # 28 final KPIs
│   │
│   └── utils/                    # SHARED UTILITIES
│       ├── api_client.py         # HTTP client
│       ├── data_validator.py     # Schema validation
│       ├── data_contract.py      # Provenance tracking
│       ├── config_loader.py      # Configuration
│       └── logger.py             # Logging system
│
├── docs/                         # DOCUMENTATION
│   ├── README_DATA_ENGINEERING.md
│   └── README_DASHBOARDS.md
│
├── tests/                        # TEST SUITE
│   └── unit/
│       ├── test_data_contract.py # 31 tests
│       └── ...
│
├── run.ps1                       # PowerShell task runner
├── Makefile                      # Unix-like task runner
├── run_dashboard.py              # Dashboard launcher
├── check_data.py                 # Data verification
└── requirements.txt              # Dependencies
```

---

## Data Contracts - Provenance and Quality

### The Problem
Synthetic/fallback data was being saved silently alongside real data without clear distinction. This caused:
- KPIs generated from "fictitious" data being treated as real
- No traceability of data origin
- Inability to filter untrusted data in dashboards

### The Solution: Data Contracts
Each pipeline artifact (Bronze/Silver/Gold) now has an accompanying `.contract.json` file containing:

```json
{
  "artifact_name": "affordability_features",
  "artifact_path": "data_pipeline/silver/affordability_features.parquet",
  "layer": "silver",
  "source": "real",
  "source_name": "world_bank_api",
  "quality": "excellent",
  "confidence_score": 87.5,
  "record_count": 120,
  "column_count": 8,
  "null_percentage": 2.1,
  "created_at": "2026-04-25T12:00:00",
  "data_from_date": "1990-01-01",
  "data_to_date": "2021-12-31",
  "notes": "Calculated from real World Bank data"
}
```

### Data Source Classification

| Source      | Description                                      | Base Confidence |
|-------------|--------------------------------------------------|-----------------|
| `real`      | Government API data (World Bank, Stats NZ, RBNZ) | 50              |
| `proxy`     | Data used as proxy (OECD, etc.)                  | 35              |
| `fallback`  | Hardcoded values when source fails               | 10              |
| `synthetic` | Code-generated data (simulated)                  | 0               |

### Confidence Score Calculation (0-100)

```python
def calculate_confidence_score(df, source, null_percentage):
    score = 0.0

    # Source base score
    if source == DataSource.REAL:      score += 50
    elif source == DataSource.PROXY:   score += 35
    elif source == DataSource.FALLBACK: score += 10
    elif source == DataSource.SYNTHETIC: score += 0
    else:                              score += 15  # UNKNOWN

    # Null penalty (0-30)
    if null_percentage < 5:   score += 30
    elif null_percentage < 15: score += 20
    elif null_percentage < 30: score += 10

    # Completeness bonus (0-15)
    row_complete_pct = 100 - null_percentage
    if row_complete_pct > 95: score += 15
    elif row_complete_pct > 85: score += 10
    elif row_complete_pct > 70: score += 5

    # Record count bonus (0-5)
    if len(df) >= 100: score += 5
    elif len(df) >= 50: score += 3
    elif len(df) >= 20: score += 1

    return min(100.0, max(0.0, score))
```

---

## Data Sources

### Implemented (Real Data)

1. **World Bank API** - 5 main datasets:
   - `NY.GDP.MKTP.KD.ZG` - GDP growth (annual %)
   - `FP.CPI.TOTL.ZG` - Inflation, consumer prices
   - `SL.UEM.TOTL.ZS` - Unemployment rate
   - `FR.INR.LEND` - Lending interest rate
   - `SP.POP.TOTL` - Total population

2. **Stats NZ** (partial):
   - Income statistics
   - Population data

### In Development

1. **RBNZ** (Reserve Bank of New Zealand)
   - Interest rates
   - Monetary policy data

2. **LINZ** (Land Information New Zealand)
   - Property valuations
   - Land registry data

3. **MBIE Tourism**
   - Visitor statistics
   - Tourism expenditure

---

## Pipeline Execution

### Method 1: Complete Pipeline (Recommended)
```powershell
# Execute complete pipeline
.\run.ps1 all
```

### Method 2: Individual Stages
```bash
# 1. Collect Bronze data (World Bank)
python data_pipeline/bronze/bronze_orchestrator.py

# 2. Process Silver features
python data_pipeline/silver/feature_engineer.py

# 3. Calculate Gold KPIs
python data_pipeline/gold/kpi_calculator.py
```

### Method 3: Verification
```bash
# Quick schema + freshness validation
python check_data.py

# Check if data was generated
python check_gold.py
```

---

## Data Formats

### Bronze Layer (Raw)
```json
{
  "country": "NZL",
  "indicator": "NY.GDP.MKTP.KD.ZG",
  "data": [
    {"year": 2021, "value": 5.6},
    {"year": 2020, "value": -1.0}
  ]
}
```

### Silver Layer (Features)
```python
feature_df = pd.DataFrame({
    'year': [2021, 2020],
    'gdp_growth': [5.6, -1.0],
    'inflation_rate': [3.1, 1.5],
    'unemployment_rate': [4.0, 4.6],
    # ... 6 robust features
})
```

### Gold Layer (KPIs)
```python
kpi_data = {
    'name': 'Habitat Intelligence Score',
    'value': 85.0,
    'unit': 'pts',
    'description': 'Overall market health indicator',
    'category': 'executive',
    'source': 'real',
    'timestamp': '2024-01-01',
    'confidence': 87
}
```

---

## KPIs Generated (28 Total)

| Dashboard | KPIs | Description |
|-----------|------|-------------|
| Executive | 6 | Habitat Intelligence Score, Economic Growth, etc. |
| Housing | 5 | House Price Index, Rent Index, Supply Ratio, etc. |
| Tourism | 4 | Tourism Pressure Index, Short-Term Rental Penetration, etc. |
| Macro | 5 | GDP Growth, Inflation, Unemployment, Interest Rate, etc. |
| Affordability | 4 | Price-to-Income Ratio, Rent-to-Income Ratio, etc. |
| Forecast | 4 | 12-Month Price Forecast, Model Confidence, etc. |

---

## Using Data Contracts in Code

### Saving Data with Contract
```python
from data_pipeline.utils.data_contract import (
    DataSource, create_contract, save_dataframe_with_contract
)

# Save features with contract
save_dataframe_with_contract(
    df=features_df,
    path="/path/to/feature",
    artifact_name="affordability_features",
    layer="silver",
    source=DataSource.REAL,
    source_name="world_bank_api",
    notes="Calculated from real World Bank data"
)
```

### Loading Data with Contract
```python
from app.utils.data_loader import DataLoader

loader = DataLoader()
summary = loader.get_dashboard_summary()

# Each dashboard now has:
# - data_source: 'real' | 'synthetic' | 'fallback'
# - confidence: 0-100
# - is_trusted: True if confidence >= 70 AND source == 'real'

warnings = loader.get_data_quality_warnings()
# Returns warnings for dashboards with untrusted data
```

---

## Testing

### Run Unit Tests
```bash
cd NZ_Habitat_Intelligence
python -m pytest tests/unit/test_data_contract.py -v
```

### Test Results
```
======================= 31 passed, 2 warnings ========================
```

---

## Dashboard System

### Running the Dashboard
```bash
# Start all 6 dashboards
python run_dashboard.py

# Access at
http://127.0.0.1:8050/
```

### Dashboard Components
- **Semantic colors**: Green=positive, Yellow=moderate, Red=critical
- **KPI cards**: Premium design with status indicators
- **Charts**: Interactive Plotly visualizations
- **Automatic insights**: Executive-ready analysis

---

## System Health Check

```powershell
.\run.ps1 check
```

Output:
```
System Health Check
===================
[OK] Bronze: 16 raw data files found
[OK] Silver: 9 engineered features found
[OK] Gold: 9 KPI files found
[OK] Dashboard runner exists
[OK] Modular app exists
```

---

## Configuration

### Environment Variables
```bash
# World Bank API (optional, has fallback)
export WORLD_BANK_API_KEY="your-key"

# Data paths (default: data_pipeline/)
export NZ_HABITAT_DATA_PATH="./data_pipeline"
```

### Logging
- Pipeline logs: `logs/pipeline_*.log`
- Dashboard logs: `logs/dashboard_*.log`
- Debug mode: `python run_dashboard.py --debug`

---

## Troubleshooting

### "World Bank API not responding"
```bash
# Test connection
python -c "import requests; print(requests.get('https://api.worldbank.org/v2').status_code)"

# Use local cache - data already downloaded in data_pipeline/bronze/
```

### "Corrupted Parquet files"
```bash
# Regenerate complete pipeline
.\run.ps1 all

# Or regenerate specific layer
python data_pipeline/gold/kpi_calculator.py --regenerate
```

### "Missing KPI values"
```bash
# Check source data
python check_data.py

# Debug specific calculation
python -c "from data_pipeline.gold.kpi_calculator import calculate_executive_kpis; print(calculate_executive_kpis())"
```

---

## Development

### Project Status

#### Completed
- [x] World Bank API integration
- [x] 3-layer functional pipeline
- [x] 28 calculated KPIs
- [x] Validation and logging
- [x] Data contracts (provenance tracking)
- [x] 31 unit tests passing

#### In Progress
- [ ] Complete Stats NZ integration
- [ ] RBNZ scraping (403 Forbidden workaround)
- [ ] Intelligent API call caching
- [ ] Automatic alerting system

#### Planned
- [ ] Production pipeline (Airflow/Dagster)
- [ ] Data versioning (DVC)
- [ ] Data quality monitoring (Great Expectations)
- [ ] CI/CD for pipeline

---

## File Extensions

| Extension | Description |
|-----------|-------------|
| `.json` | Bronze raw data, metadata |
| `.parquet` | Silver/Gold processed data |
| `.contract.json` | Data contract for provenance |
| `.py` | Python source code |
| `.ps1` | PowerShell scripts |
| `.bat` | Windows batch scripts |

---

## API Reference

### Key Classes

#### DataContract
```python
@dataclass
class DataContract:
    artifact_name: str
    artifact_path: str
    layer: str  # 'bronze', 'silver', 'gold'
    source: DataSource
    source_name: str
    quality: DataQuality
    confidence_score: float
    record_count: int
    column_count: int
    null_percentage: float
    columns: List[ColumnContract]
    created_at: str
    data_from_date: Optional[str]
    data_to_date: Optional[str]
    parent_contracts: List[str]
    notes: str
```

#### DataSource Enum
```python
class DataSource(Enum):
    REAL = "real"           # From authenticated external API
    SYNTHETIC = "synthetic" # Generated by code
    FALLBACK = "fallback"   # Hardcoded fallback
    PROXY = "proxy"         # Used as proxy
    UNKNOWN = "unknown"     # Cannot be determined
```

#### DataQuality Enum
```python
class DataQuality(Enum):
    EXCELLENT = "excellent"  # Real data, no nulls
    GOOD = "good"            # Real data, minor gaps
    FAIR = "fair"            # Real data with gaps or synthetic
    POOR = "poor"            # Mostly synthetic/fallback
    UNKNOWN = "unknown"      # Cannot determine
```

---

## Contact

- **Pipeline Issues**: Check logs in `logs/`
- **Missing Data**: Run `.\run.ps1 all`
- **Calculation Errors**: Use `check_data.py`

---

*From complex government data to clear executive insights*