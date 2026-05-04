{{
  config(
    materialized='external',
    location=var('silver_dir', '../data_pipeline/silver') ~ '/supply_deficit_features.parquet',
    format='parquet'
  )
}}

select
    year,
    region,
    building_consents,
    population,
    population_growth,
    consents_per_1000_people,
    supply_deficit_score,
    housing_supply_gap
from read_parquet('{{ var("silver_dir", "../data_pipeline/silver") }}/supply_deficit_features.parquet')
