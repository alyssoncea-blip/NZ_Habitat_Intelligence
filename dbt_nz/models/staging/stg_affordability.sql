{{
  config(
    materialized='external',
    location=var('silver_dir', '../data_pipeline/silver') ~ '/affordability_features.parquet',
    format='parquet'
  )
}}

select
    year,
    region,
    gdp_per_capita,
    median_income,
    affordability_index,
    price_to_income_ratio
from read_parquet('{{ var("silver_dir", "../data_pipeline/silver") }}/affordability_features.parquet')
