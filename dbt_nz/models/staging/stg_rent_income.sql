{{
  config(
    materialized='external',
    location=var('silver_dir', '../data_pipeline/silver') ~ '/rent_income_ratio_features.parquet',
    format='parquet'
  )
}}

select
    year,
    region,
    median_weekly_rent,
    annual_rent,
    median_income,
    rent_to_income_ratio,
    general_inflation,
    rent_inflation_rate,
    affordability_erosion,
    cumulative_rent_pressure
from read_parquet('{{ var("silver_dir", "../data_pipeline/silver") }}/rent_income_ratio_features.parquet')
