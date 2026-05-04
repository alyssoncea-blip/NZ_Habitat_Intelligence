-- Gold: Affordability Dashboard KPIs
-- Regional affordability: years to buy, rent burden, affordability ranking

{{
  config(
    materialized='external',
    location=var('gold_dir', '../data_pipeline/gold') ~ '/kpis-05-affordability_complete.parquet',
    format='parquet'
  )
}}

with rent_income as (
    select * from {{ ref('stg_rent_income') }}
),
affordability as (
    select * from {{ ref('stg_affordability') }}
),
regions as (
    select * from {{ ref('nz_regions') }}
),
latest_ri as (
    select * from rent_income
    where year = (select max(year) from rent_income)
),
latest_aff as (
    select * from affordability
    where year = (select max(year) from affordability)
)

select
    'Years to Buy - ' || laf.region as kpi_name,
    round(coalesce(laf.price_to_income_ratio, 0), 1) as kpi_value,
    'years' as unit,
    'Estimated years of median income to buy median home in ' || laf.region,
    'affordability' as dashboard,
    'purchase' as category,
    current_timestamp as calculated_at
from latest_aff laf

union all

select
    'Rent Burden - ' || lri.region,
    round(coalesce(lri.rent_to_income_ratio, 0), 1),
    '%',
    'Rent as percentage of median income in ' || lri.region,
    'affordability',
    'rental',
    current_timestamp
from latest_ri lri

union all

select
    'Median Weekly Rent - ' || lri.region,
    coalesce(lri.median_weekly_rent, 0),
    'NZD',
    'Median weekly rent in ' || lri.region,
    'affordability',
    'rental',
    current_timestamp
from latest_ri lri

union all

select
    'National Affordability Index',
    round(coalesce(avg(laf.affordability_index), 0), 2),
    'index',
    'National housing affordability composite index',
    'affordability',
    'composite',
    current_timestamp
from latest_aff laf

union all

select
    'National Price-to-Income Ratio',
    round(coalesce(avg(laf.price_to_income_ratio), 0), 1),
    'ratio',
    'National average price-to-income ratio',
    'affordability',
    'purchase',
    current_timestamp
from latest_aff laf

union all

select
    'National Rent Burden',
    round(coalesce(avg(lri.rent_to_income_ratio), 0), 1),
    '%',
    'National average rent as percentage of income',
    'affordability',
    'rental',
    current_timestamp
from latest_ri lri

union all

select
    'Affordability Erosion Rate',
    round(avg(coalesce(lri.rent_inflation_rate, 0)), 1),
    '%',
    'Rate at which affordability is declining due to rent inflation',
    'affordability',
    'trend',
    current_timestamp
from latest_ri lri
