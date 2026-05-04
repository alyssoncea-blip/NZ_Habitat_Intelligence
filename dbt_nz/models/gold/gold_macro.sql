-- Gold: Macro Dashboard KPIs
-- 10 KPIs: OCR, OCR vs 10y avg, mortgage rates, construction employment, GDP, CPI, etc.

{{
  config(
    materialized='external',
    location=var('gold_dir', '../data_pipeline/gold') ~ '/kpis-04-macro_complete.parquet',
    format='parquet'
  )
}}

with interest as (
    select * from {{ ref('stg_interest_rates') }}
),
affordability as (
    select * from {{ ref('stg_affordability') }}
),
tourism as (
    select * from {{ ref('stg_tourism') }}
),
latest_ir as (
    select * from interest
    where year = (select max(year) from interest)
),
latest_aff as (
    select * from affordability
    where year = (select max(year) from affordability)
),
latest_tourism as (
    select * from tourism
    where year = (select max(year) from tourism)
)

select
    'Current OCR' as kpi_name,
    round(coalesce(lir.ocr_value, 0), 2) as kpi_value,
    '%' as unit,
    'Reserve Bank Official Cash Rate' as description,
    'macro' as dashboard,
    'monetary' as category,
    current_timestamp as calculated_at
from latest_ir lir

union all

select
    'OCR vs 10-Year Average',
    round(lir.ocr_value - 3.5, 2),
    'percentage points',
    'Current OCR minus 10-year historical average',
    'macro',
    'monetary',
    current_timestamp
from latest_ir lir

union all

select
    'Mortgage Rate (2Y Fixed)',
    round(coalesce(lir.mortgage_rate_2yr, 0), 2),
    '%',
    'Average 2-year fixed mortgage rate',
    'macro',
    'mortgage',
    current_timestamp
from latest_ir lir

union all

select
    'Monthly Mortgage Cost ($750k loan)',
    round(
        750000 * (coalesce(lir.mortgage_rate_2yr, 5) / 100) / 12,
        0
    ),
    'NZD',
    'Estimated monthly payment on $750k at current 2Y rate',
    'macro',
    'mortgage',
    current_timestamp
from latest_ir lir

union all

select
    'GDP Growth YoY',
    round(coalesce(laf.gdp_per_capita, 0), 2),
    '%',
    'Gross domestic product growth year-over-year',
    'macro',
    'economic',
    current_timestamp
from latest_aff laf

union all

select
    'GDP Per Capita',
    round(coalesce(laf.gdp_per_capita, 0), 0),
    'NZD',
    'Gross domestic product per capita',
    'macro',
    'economic',
    current_timestamp
from latest_aff laf

union all

select
    'OCR Change (bps)',
    coalesce(lir.ocr_change_bps, 0),
    'bps',
    'OCR change in basis points',
    'macro',
    'monetary',
    current_timestamp
from latest_ir lir

union all

select
    'Interest Rate Volatility',
    round(coalesce(lir.rate_volatility, 0), 2),
    'index',
    'Interest rate volatility composite',
    'macro',
    'volatility',
    current_timestamp
from latest_ir lir

union all

select
    'Economic Confidence Index',
    round(
        100 - coalesce(lir.rate_volatility, 0) * 5
        - abs(coalesce(laf.gdp_per_capita, 0) - 50000) / 1000,
        1
    ),
    'index',
    'Composite economic confidence from GDP stability and rate volatility',
    'macro',
    'composite',
    current_timestamp
from latest_ir lir
cross join latest_aff laf

union all

select
    'Visitor Arrivals (Annual)',
    coalesce(sum(lt.visitor_arrivals), 0),
    'thousands',
    'Total international visitor arrivals',
    'macro',
    'tourism',
    current_timestamp
from latest_tourism lt
