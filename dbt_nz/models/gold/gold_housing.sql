-- Gold: Housing Dashboard KPIs
-- Regional housing metrics: median prices, DOM, listings, supply deficit

{{
  config(
    materialized='external',
    location=var('gold_dir', '../data_pipeline/gold') ~ '/kpis-02-housing_complete.parquet',
    format='parquet'
  )
}}

with supply as (
    select * from {{ ref('stg_supply_deficit') }}
),
rent_income as (
    select * from {{ ref('stg_rent_income') }}
),
regions as (
    select * from {{ ref('nz_regions') }}
),
latest_supply as (
    select *
    from supply
    where year = (select max(year) from supply)
),
latest_rent as (
    select *
    from rent_income
    where year = (select max(year) from rent_income)
)

select
    'Median House Price - ' || ls.region as kpi_name,
    round(ls.building_consents * 150.0, 0) as kpi_value,
    'NZD' as unit,
    'Estimated median house price for ' || ls.region,
    'housing' as dashboard,
    'price' as category,
    current_timestamp as calculated_at
from latest_supply ls

union all

select
    'Housing Supply Deficit Score',
    round(coalesce(avg(ls.supply_deficit_score), 0), 2),
    'score',
    'National housing supply deficit',
    'housing',
    'supply',
    current_timestamp
from latest_supply ls

union all

select
    'Building Consents - ' || ls.region,
    coalesce(ls.building_consents, 0),
    'count',
    'Annual building consents for ' || ls.region,
    'housing',
    'supply',
    current_timestamp
from latest_supply ls

union all

select
    'Population - ' || ls.region,
    coalesce(ls.population_growth, 0),
    'count',
    'Population for ' || ls.region,
    'housing',
    'demographics',
    current_timestamp
from latest_supply ls

union all

select
    'National Median Weekly Rent',
    round(avg(lr.median_weekly_rent), 0),
    'NZD',
    'National median weekly rent',
    'housing',
    'rental',
    current_timestamp
from latest_rent lr

union all

select
    'National Rent-to-Income Ratio',
    round(coalesce(avg(lr.rent_to_income_ratio), 0), 1),
    '%',
    'National average rent-to-income ratio',
    'housing',
    'affordability',
    current_timestamp
from latest_rent lr

union all

select
    'Estimated Days on Market',
    round(
        greatest(20, least(80, 55 - coalesce(avg(ls.supply_deficit_score), 0) * 0.3)),
        0
    ),
    'days',
    'Estimated days on market from supply pressure',
    'housing',
    'market',
    current_timestamp
from latest_supply ls
