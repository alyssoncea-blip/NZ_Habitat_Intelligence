# KPI Formulas Reference

## Executive Dashboard

| KPI | Formula | Source | Frequency | Benchmark |
|-----|---------|--------|-----------|-----------|
| Habitat Intelligence Score | Weighted composite of all 5 sub-indices | Multiple | Monthly | 50-100 (higher = healthier) |
| Economic Growth Per Capita | GDP growth / Population growth | World Bank | Annual | > 2% = healthy |
| Monetary Stability Index | 100 - |OCR - target OCR| / target OCR * 100 | RBNZ | Monthly | > 80 = stable |
| Tourism Economic Impact | Tourism expenditure / GDP * 100 | MBIE + World Bank | Annual | 5-10% = significant |
| Housing Supply Deficit | (Population growth * 0.3) - Building consents | Stats NZ | Annual | < 0 = surplus, > 0 = deficit |
| Rent vs Inflation Gap | Rent growth % - CPI % | Tenancy Services + RBNZ | Quarterly | < 2% = stable |
| Construction Activity Index | Building consents YoY growth | Stats NZ | Monthly | > 5% = active |
| Interest Rate Impact | Mortgage rate change * Housing stock | RBNZ + LINZ | Monthly | < 3% = low impact |

## Housing Dashboard

| KPI | Formula | Source | Frequency | Benchmark |
|-----|---------|--------|-----------|-----------|
| House Price Index Growth | (Current HPI - Previous HPI) / Previous HPI * 100 | REINZ | Monthly | 3-5% annual = stable |
| Rent Price Index Growth | (Current RPI - Previous RPI) / Previous RPI * 100 | Tenancy Services | Quarterly | 2-4% annual = stable |
| Housing Supply Ratio | Building consents / Household formation | Stats NZ | Annual | > 1.0 = surplus |
| Price-to-Rent Ratio | Median house price / Annual median rent | REINZ + Tenancy | Monthly | < 15 = affordable, > 20 = expensive |
| Rental Yield | Annual rent / Median house price * 100 | REINZ + Tenancy | Monthly | > 5% = good yield |

## Tourism Dashboard

| KPI | Formula | Source | Frequency | Benchmark |
|-----|---------|--------|-----------|-----------|
| Tourism Pressure Index | Visitor arrivals / Local population * 100 | MBIE + Stats NZ | Monthly | < 50 = low, > 100 = high |
| Visitor Seasonality Strength | Std(Monthly visitors) / Mean(Monthly visitors) | MBIE | Monthly | < 0.3 = low seasonality |
| Tourism-Housing Correlation | Pearson(visitor arrivals, house prices) | MBIE + REINZ | Annual | > 0.5 = strong correlation |

## Macro Dashboard

| KPI | Formula | Source | Frequency | Benchmark |
|-----|---------|--------|-----------|-----------|
| GDP Growth Rate | (GDP_t - GDP_t-1) / GDP_t-1 * 100 | World Bank | Annual | 2-4% = healthy |
| Inflation Rate | CPI YoY change | RBNZ | Quarterly | 1-3% = target range |
| Unemployment Rate | Unemployed / Labor force * 100 | World Bank | Quarterly | 3-5% = full employment |
| Macroeconomic Volatility | Weighted std of GDP, inflation, unemployment | World Bank | Annual | < 2 = stable |

## Affordability Dashboard

| KPI | Formula | Source | Frequency | Benchmark |
|-----|---------|--------|-----------|-----------|
| Price-to-Income Ratio | Median house price / Median household income | REINZ + Stats NZ | Annual | < 5 = affordable, > 8 = unaffordable |
| Rent-to-Income Ratio | Annual rent / Median household income * 100 | Tenancy + Stats NZ | Annual | < 30% = affordable, > 40% = stressed |
| Debt Service Ratio | Mortgage payment / Income * 100 | RBNZ + Stats NZ | Quarterly | < 30% = manageable |

## Forecast Dashboard

| KPI | Formula | Source | Frequency | Benchmark |
|-----|---------|--------|-----------|-----------|
| 12-Month Price Forecast | Linear regression + seasonal adjustment | Historical data | Monthly | N/A (prediction) |
| Model Confidence | R-squared * 100 | Model fit | Monthly | > 70% = reliable |
| Forecast Accuracy | 1 - |Actual - Forecast| / Actual * 100 | Backtesting | Quarterly | > 80% = accurate |
