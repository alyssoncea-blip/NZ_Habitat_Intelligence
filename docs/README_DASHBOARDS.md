# NZ HABITAT INTELLIGENCE - DASHBOARD SYSTEM

## OVERVIEW

Premium executive dashboard system with 6 interactive dashboards, 34 real-time KPIs, and consulting-inspired design (McKinsey/Deloitte style). Modular architecture with Plotly Dash frontend and DuckDB backend. All KPIs come from real data (World Bank, Stats NZ, MBIE) with provenance data contracts.

### KEY FEATURES
- **6 Complete dashboards** with 34 KPIs
- **Premium executive design** with semantic colors
- **Modular and scalable architecture**
- **Real New Zealand data** (World Bank API, Stats NZ, MBIE)
- **Fluid navigation** between dashboards
- **Data contracts** on all artifacts (provenance + confidence)
- **Responsive and accessible**

---

## SYSTEM ARCHITECTURE

### FILE STRUCTURE
```
app/                           # MODULAR APPLICATION
|
├── components/                # REUSABLE COMPONENTS
│   ├── layout.py             # Base layout, header, footer
│   ├── cards.py              # Premium KPI cards (PremiumCard, HeroKPICard)
│   ├── charts.py             # Plotly chart components
│   ├── navigation.py         # Navbar, sidebar, navigation
│   └── __init__.py           # Exports
│
├── pages/                     # 6 DASHBOARDS
│   ├── executive.py          # Executive Dashboard
│   ├── housing.py            # Housing Dashboard
│   ├── tourism.py            # Tourism Dashboard
│   ├── macro.py              # Macro Dashboard
│   ├── affordability.py      # Affordability Dashboard
│   ├── forecast.py           # Forecast Dashboard
│   └── __init__.py
│
├── data/                      # DATA MODULES (load from Gold)
│   ├── executive_kpi_data.py # Executive dashboard data
│   ├── housing_kpi_data.py   # Housing dashboard data
│   ├── tourism_kpi_data.py   # Tourism dashboard data
│   ├── macro_kpi_data.py     # Macro dashboard data
│   ├── affordability_kpi_data.py
│   └── forecast_kpi_data.py
│
├── utils/                     # UTILITIES
│   ├── data_loader.py        # Interface with gold pipeline + contracts
│   ├── style_config.py       # Premium style system
│   ├── kpi_processor.py      # KPI processing and formatting
│   ├── kpi_labels.py         # KPI labels and descriptions
│   ├── quality_indicators.py # Data quality indicators
│   ├── dashboard_factory.py  # Dashboard factory
│   ├── logger.py             # Logging system
│   └── __init__.py
│
└── assets/                    # STATIC ASSETS
    └── style.css             # Premium CSS styles
```

---

## THE 6 DASHBOARDS

### 1. EXECUTIVE DASHBOARD (/executive)
Main dashboard with hero KPI and 8 executive metrics.

**KPIs:**
- Habitat Intelligence Score (composite index)
- Economic Growth Per Capita
- Monetary Stability Index
- Tourism Economic Impact
- Housing Supply Deficit
- Rent vs Inflation Gap
- Construction Activity Index
- Interest Rate Impact

**Features:**
- Hero KPI card with automatic status coloring
- Scatter plot: Tourism Pressure vs Affordability
- Line chart: Price Change Month-over-Month
- Dual-axis chart: OCR vs Pressure Index
- Executive insights with automatic recommendations

### 2. HOUSING DASHBOARD (/housing)
Housing market analysis with 18 KPIs.

**KPIs:**
- House Price Index Growth
- Rent Price Index Growth
- Housing Supply Ratio
- Construction Activity Index
- Vacancy Rate
- Price Growth YoY
- Rent Growth YoY
- Supply-Demand Balance
- Building Consents Trend
- Construction Momentum
- Housing Affordability Pressure
- Price-to-Rent Ratio
- Rental Yield
- Housing Stock Growth
- New Build Rate
- Market Tightness Index
- Price Momentum
- Rent Momentum

### 3. TOURISM DASHBOARD (/tourism)
Tourism impact on housing market with 5 KPIs.

**KPIs:**
- Tourism Pressure Index
- Short-Term Rental Penetration
- Tourism-Housing Correlation
- Visitor Seasonality Strength
- International Visitor Impact

### 4. MACRO DASHBOARD (/macro)
Macroeconomic indicators with 10 KPIs.

**KPIs:**
- GDP Growth Rate
- Inflation Rate
- Unemployment Rate
- Interest Rate
- Economic Confidence Index
- GDP Per Capita
- Economic Growth YoY
- Monetary Policy Impact
- Macroeconomic Volatility
- Inflation-Unemployment Tradeoff

### 5. AFFORDABILITY DASHBOARD (/affordability)
Housing affordability analysis with 5 KPIs.

**KPIs:**
- Price-to-Income Ratio
- Rent-to-Income Ratio
- Affordability Index
- Debt Service Ratio
- Affordability Erosion Rate

### 6. FORECAST DASHBOARD (/forecast)
Predictive analysis with 13 KPIs.

**KPIs:**
- 12-Month Price Forecast
- Overall Model Confidence
- Forecast Confidence Range
- Regions with High Forecast Risk
- Trend Direction
- Forecast Accuracy
- Scenario Analysis

---

## DESIGN SYSTEM

### SEMANTIC COLORS
- **Green** (#10b981): Positive/healthy metrics
- **Yellow** (#f59e0b): Moderate/warning metrics
- **Red** (#ef4444): Critical/at-risk metrics
- **Blue** (#3b82f6): Neutral/informational metrics

### TYPOGRAPHY
- **Font:** Manrope (Google Fonts)
- **Weights:** 400 (regular), 500 (medium), 600 (semibold), 700 (bold), 800 (extrabold)

### CARD COMPONENTS
- **PremiumCard:** Standard KPI card with status indicator
- **HeroKPICard:** Large hero KPI for executive dashboard
- **InsightCard:** Executive insight with recommendation
- **ChartCard:** Chart container with title and description

---

## DATA FLOW

```
Gold Parquet Files → DataLoader (singleton + LRU cache)
  → KPI Processor (formatting + filtering)
    → Dashboard Pages (rendering)
      → Plotly Charts (visualization)
```

### Data Loading
- `DataLoader` singleton with LRU caching
- Loads from `data_pipeline/gold/kpis-*_complete.parquet`
- Falls back to default data if files missing
- Contracts loaded alongside data for quality indicators

---

## RUNNING THE DASHBOARDS

```bash
# Quick start
python run_dashboard.py

# With custom host/port
python run_dashboard.py 0.0.0.0 8080

# Via Makefile
make dashboard

# Via Docker
make docker-run
```

**URL:** http://127.0.0.1:8050

---

## DASHBOARD SCREENSHOTS

The following screenshots were captured from the live dashboard system and represent the current production state of each page.

### Executive Dashboard
![Executive Dashboard](../../docs/screenshots/dashboard_executive.png)

### Housing Dashboard
![Housing Dashboard](../../docs/screenshots/dashboard_housing.png)

### Tourism Dashboard
![Tourism Dashboard](../../docs/screenshots/dashboard_tourism.png)

### Macro Dashboard
![Macro Dashboard](../../docs/screenshots/dashboard_macro.png)

### Affordability Dashboard
![Affordability Dashboard](../../docs/screenshots/dashboard_affordability.png)

### Forecast Dashboard
![Forecast Dashboard](../../docs/screenshots/dashboard_forecast.png)

---

## CUSTOMIZATION

### Adding a New Dashboard
1. Create page in `app/pages/new_dashboard.py`
2. Create data module in `app/data/new_kpi_data.py`
3. Register in `app/pages/__init__.py`
4. Add route in `app/main.py`

### Adding a New KPI
1. Add calculation in `data_pipeline/gold/kpi_calculator.py`
2. Add label in `app/utils/kpi_labels.py`
3. Add data loading in appropriate `app/data/*_kpi_data.py`
4. Add card in `app/components/cards.py`

### Styling
All styles are in `app/assets/style.css`. Use CSS variables for theming.

---

## TROUBLESHOOTING

### "Error loading data"
Run the pipeline first:
```bash
python data_pipeline/run_enhanced_pipeline.py --force
```

### "Dashboard doesn't start"
Check dependencies:
```bash
pip install dash dash-bootstrap-components pandas duckdb
```

### "KPIs don't appear"
Check data files:
```bash
python -c "
import glob
files = glob.glob('data_pipeline/gold/*.parquet')
print(f'{len(files)} data files found')
"
```
