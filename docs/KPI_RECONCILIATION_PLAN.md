# KPI Calculator Reconciliation Plan

## Problem
Two parallel systems calculate KPIs:
1. **Python KPI Calculator** (`data_pipeline/gold/kpi_calculator.py`) — 34 KPIs from Silver/Bronze
2. **dbt Gold Models** (`dbt_nz/models/gold/*.sql`) — SQL-based KPI calculations

This creates:
- Inconsistent KPI values between systems
- Maintenance burden (two codebases to update)
- Unclear source of truth for dashboards

## Solution: dbt as Single Source of Truth

### Architecture After Reconciliation
```
Silver Features → dbt Gold Models (SQL) → Gold Parquet Files → Dashboard
                      ↑
                Python Calculator (reads dbt output, adds derived KPIs)
```

### Implementation Steps

#### Step 1: Align KPI Names
Ensure dbt and Python use identical KPI names. Current discrepancies:

| Python Name | dbt Name | Action |
|-------------|----------|--------|
| `Habitat Intelligence Score` | `Habitat Intelligence Score` | Match |
| `GDP per Capita YoY` | `GDP per Capita YoY` | Match |
| `Interest Rate Stability` | `Interest Rate Stability` | Match |
| `Tourism-Economy Link` | `Tourism Pressure Index` | Rename dbt |
| `Housing Supply Pressure` | `Housing Supply Pressure` | Match |
| `Rent Affordability Gap` | `Rent Affordability Gap` | Match |
| `Current OCR` | `Current OCR` | Match |
| `Inflation (CPI)` | _(missing)_ | Add to dbt |

#### Step 2: Update dbt Models
Add missing KPIs to dbt gold models:
- `gold_executive.sql`: Add Inflation (CPI)
- `gold_tourism.sql`: Rename to match Python names
- `gold_macro.sql`: Add all 10 macro KPIs
- `gold_forecast.sql`: Add all 13 forecast KPIs

#### Step 3: Update Python Calculator
Change Python calculator to:
1. Read from dbt-generated Parquet files as primary source
2. Add derived KPIs that require Python (regional estimates, complex calculations)
3. Validate output matches dbt expectations

#### Step 4: Add Validation Test
Create `tests/unit/test_kpi_reconciliation.py`:
- Compare dbt output vs Python output for overlapping KPIs
- Fail if values differ by more than 1%
- Report discrepancies

#### Step 5: Update Pipeline
Change `run_enhanced_pipeline.py` to:
1. Run dbt after Silver stage
2. Run Python calculator (reads dbt output)
3. Run GE validation on final output

## KPI Mapping (34 Total)

### Executive Dashboard (8 KPIs)
| # | KPI Name | Source | Formula |
|---|----------|--------|---------|
| 1 | Habitat Intelligence Score | dbt | IR(30%) + Supply(35%) + GDP/capita(35%) |
| 2 | GDP per Capita YoY | dbt | (GDP_pc_current - GDP_pc_prev) / GDP_pc_prev |
| 3 | Interest Rate Stability | dbt | 100 - rate_volatility |
| 4 | Tourism-Economy Link | dbt | \|correlation(tourism_growth, supply_pressure)\| * 100 |
| 5 | Housing Supply Pressure | dbt | supply_deficit_score |
| 6 | Rent Affordability Gap | dbt | rent_to_income_ratio |
| 7 | Current OCR | dbt | ocr_value |
| 8 | Inflation (CPI) | dbt | cpi_annual_change |

### Housing Dashboard (18 KPIs)
| # | KPI Name | Source | Formula |
|---|----------|--------|---------|
| 1 | Median House Price (National) | Python | income × price-to-income ratio |
| 2-16 | Regional Median Prices | Python | region-specific estimates |
| 17 | Average Days on Market | Python | 55 - supply_pressure × 0.3 |
| 18 | New Listings per Week | Python | 3200 - (OCR - 4) × 300 |

### Tourism Dashboard (5 KPIs)
| # | KPI Name | Source | Formula |
|---|----------|--------|---------|
| 1 | Tourism Pressure Index | dbt | tourism_expenditure / housing_stock |
| 2 | Short-Term Rental Penetration | dbt | str_listings / total_listings |
| 3 | Tourism-Housing Correlation | dbt | correlation(tourism, prices) |
| 4 | Visitor Seasonality Strength | dbt | std(monthly_visitors) / mean(monthly_visitors) |
| 5 | International Visitor Impact | dbt | international_visitors × avg_spend |

### Macro Dashboard (10 KPIs)
| # | KPI Name | Source | Formula |
|---|----------|--------|---------|
| 1 | GDP Growth Rate | dbt | gdp_yoy_change |
| 2 | Inflation Rate | dbt | cpi_annual_change |
| 3 | Unemployment Rate | dbt | unemployment_rate |
| 4 | Interest Rate | dbt | lending_rate |
| 5 | Economic Confidence Index | Python | composite(gdp, inflation, unemployment) |
| 6 | GDP Per Capita | dbt | gdp / population |
| 7 | Economic Growth YoY | dbt | gdp_yoy_change |
| 8 | Monetary Policy Impact | Python | ocr_change × housing_price_sensitivity |
| 9 | Macroeconomic Volatility | dbt | rolling_std(gdp, inflation, unemployment) |
| 10 | Inflation-Unemployment Tradeoff | Python | inflation_rate - unemployment_rate |

### Affordability Dashboard (5 KPIs)
| # | KPI Name | Source | Formula |
|---|----------|--------|---------|
| 1 | Price-to-Income Ratio | dbt | median_price / median_income |
| 2 | Rent-to-Income Ratio | dbt | annual_rent / median_income |
| 3 | Affordability Index | dbt | 100 - (price_to_income / 10) × 100 |
| 4 | Debt Service Ratio | Python | mortgage_payment / income |
| 5 | Affordability Erosion Rate | dbt | rent_inflation - wage_growth |

### Forecast Dashboard (13 KPIs)
| # | KPI Name | Source | Formula |
|---|----------|--------|---------|
| 1 | 12-Month Price Forecast | Python | linear_regression(prices, 12 months) |
| 2 | Overall Model Confidence | Python | r_squared × data_quality_score |
| 3 | Forecast Confidence Range | Python | ±1.96 × std(residuals) |
| 4 | Regions with High Forecast Risk | Python | top 3 by prediction_error |
| 5 | Trend Direction | Python | sign(slope) |
| 6 | Forecast Accuracy | Python | 1 - MAPE |
| 7-13 | Scenario Analysis | Python | bull/base/bear scenarios |

## Priority Order
1. **P0**: Align executive dashboard KPIs (8 KPIs) — highest visibility
2. **P1**: Align tourism + macro KPIs (15 KPIs) — second highest visibility
3. **P2**: Align housing + affordability KPIs (23 KPIs) — complex regional calculations
4. **P3**: Align forecast KPIs (13 KPIs) — Python-only for now

## Success Criteria
- [ ] All 34 KPIs have a single source of truth (dbt or Python)
- [ ] Python calculator reads from dbt output where applicable
- [ ] Validation test passes with <1% discrepancy
- [ ] Pipeline runs dbt before Python calculator
- [ ] Documentation updated to reflect new architecture
