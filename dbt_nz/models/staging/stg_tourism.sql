{{
  config(
    materialized='external',
    location=var('silver_dir', '../data_pipeline/silver') ~ '/tourism_pressure_features.parquet',
    format='parquet'
  )
}}

select
    year,
    region,
    tourism_expenditure,
    visitor_arrivals,
    tourism_pressure_index,
    unemployment_rate,
    tourism_growth_yoy
from read_parquet('{{ var("silver_dir", "../data_pipeline/silver") }}/tourism_pressure_features.parquet')
