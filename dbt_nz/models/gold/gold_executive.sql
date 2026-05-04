-- Gold: Executive Dashboard KPIs
-- 8 KPIs: Habitat Score, GDP YoY, IR Stability, Tourism Link, Supply Pressure, Rent Gap, OCR, CPI
-- Supports incremental loading for historical data

{{
  config(
    materialized='incremental',
    unique_key='kpi_name',
    on_schema_change='sync_all_columns',
    location=var('gold_dir', '../data_pipeline/gold') ~ '/kpis-01-executive_complete.parquet',
    format='parquet'
  )
}}

with base as (
    select * from {{ ref('int_kpi_base') }}
),
regions as (
    select * from {{ ref('nz_regions') }}
),
latest as (
    select *
    from base
    where year = (select max(year) from base)
)

select
    'Habitat Intelligence Score' as kpi_name,
    round(
        coalesce(l.ocr_value, 0) * 0.30 +
        coalesce(l.supply_deficit_score, 0) * 0.35 +
        coalesce(l.gdp_per_capita, 0) * 0.35,
        2
    ) as kpi_value,
    'score' as unit,
    'Weighted composite: IR impact (30%) + supply pressure (35%) + GDP/capita (35%)' as description,
    'executive' as dashboard,
    'composite' as category,
    current_timestamp as calculated_at,
    md5(concat('habitat_score', '-', l.year)) as kpi_id
from latest l

union all

select
    'GDP per Capita YoY',
    round(l.gdp_per_capita, 2),
    'NZD',
    'Gross domestic product per capita',
    'executive',
    'economic',
    current_timestamp,
    md5(concat('gdp_per_capita', '-', l.year))
from latest l

union all

select
    'Interest Rate Stability',
    round(100 - coalesce(l.rate_volatility, 0), 2),
    'index',
    '100 minus interest rate volatility score',
    'executive',
    'monetary',
    current_timestamp,
    md5(concat('ir_stability', '-', l.year))
from latest l

union all

select
    'Tourism-Economy Link',
    round(coalesce(l.tourism_pressure_index, 0), 2),
    'index',
    'Tourism impact on housing market',
    'executive',
    'tourism',
    current_timestamp,
    md5(concat('tourism_link', '-', l.year))
from latest l

union all

select
    'Housing Supply Pressure',
    round(coalesce(l.supply_deficit_score, 0), 2),
    'score',
    'Supply deficit feature from building consents vs population',
    'executive',
    'supply',
    current_timestamp,
    md5(concat('supply_pressure', '-', l.year))
from latest l

union all

select
    'Rent Affordability Gap',
    round(coalesce(l.rent_to_income_ratio, 0), 2),
    'ratio',
    'Rent-to-income ratio indicating affordability gap',
    'executive',
    'affordability',
    current_timestamp,
    md5(concat('rent_gap', '-', l.year))
from latest l

union all

select
    'Current OCR',
    round(coalesce(l.ocr_value, 0), 2),
    '%',
    'Reserve Bank Official Cash Rate',
    'executive',
    'monetary',
    current_timestamp,
    md5(concat('ocr', '-', l.year))
from latest l

union all

select
    'Inflation (CPI)',
    round(coalesce(l.ocr_change_bps, 0), 2),
    '%',
    'Consumer price index annual change',
    'executive',
    'inflation',
    current_timestamp,
    md5(concat('cpi', '-', l.year))
from latest l

union all

select
    'Building Consents (Annual)',
    coalesce(l.building_consents, 0),
    'count',
    'Total building consents issued',
    'executive',
    'supply',
    current_timestamp,
    md5(concat('building_consents', '-', l.year))
from latest l
