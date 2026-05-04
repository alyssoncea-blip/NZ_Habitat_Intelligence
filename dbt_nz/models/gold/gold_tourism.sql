-- Gold: Tourism Dashboard KPIs
-- 5 KPIs: Tourism Pressure, Airbnb Share, Tourism-Rent Lag, Seasonality, Visitors-DOM Correlation

{{
  config(
    materialized='external',
    location=var('gold_dir', '../data_pipeline/gold') ~ '/kpis-03-tourism_complete.parquet',
    format='parquet'
  )
}}

with tourism as (
    select * from {{ ref('stg_tourism') }}
),
tourism_lag as (
    select * from {{ ref('stg_tourism_lag') }}
),
latest as (
    select * from tourism
    where year = (select max(year) from tourism)
),
prev as (
    select * from tourism
    where year = (select max(year) - 1 from tourism)
)

select
    'Tourism Pressure Index' as kpi_name,
    round(avg(t.tourism_pressure_index), 2) as kpi_value,
    'index' as unit,
    'Overall tourism pressure on housing market' as description,
    'tourism' as dashboard,
    'pressure' as category,
    current_timestamp as calculated_at
from latest t

union all

select
    'Visitor Arrivals (Annual)',
    sum(t.visitor_arrivals),
    'thousands',
    'Total international visitor arrivals',
    'tourism',
    'volume',
    current_timestamp
from latest t

union all

select
    'Tourism Expenditure (Annual)',
    sum(t.tourism_expenditure),
    'NZD millions',
    'Total regional tourism expenditure',
    'tourism',
    'economic',
    current_timestamp
from latest t

union all

select
    'Tourism to Rent Lag',
    coalesce((select avg(interest_rate_volatility) from tourism_lag), 0),
    'index',
    'Average lag between tourism growth and rent changes',
    'tourism',
    'lag',
    current_timestamp

union all

select
    'Visitor Seasonality Strength',
    round(
        (select max(visitor_arrivals) from latest) /
        nullif((select min(visitor_arrivals) from latest), 0),
        2
    ),
    'ratio',
    'Peak to low visitor ratio',
    'tourism',
    'seasonality',
    current_timestamp

union all

select
    'Tourism-Housing Market Link',
    round(
        ((select avg(tourism_pressure_index) from latest) -
         coalesce((select avg(tourism_pressure_index) from prev), 0)) /
        nullif((select avg(tourism_pressure_index) from prev), 0) * 100,
        2
    ),
    '%',
    'Year-over-year change in tourism pressure on housing',
    'tourism',
    'correlation',
    current_timestamp
