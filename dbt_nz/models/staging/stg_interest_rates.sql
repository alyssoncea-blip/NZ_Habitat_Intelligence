{{
  config(
    materialized='external',
    location=var('silver_dir', '../data_pipeline/silver') ~ '/interest_rate_lag_features.parquet',
    format='parquet'
  )
}}

select
    year,
    region,
    ocr_value,
    mortgage_rate_2yr,
    ocr_change_bps,
    rate_volatility,
    interest_rate_impact_score
from read_parquet('{{ var("silver_dir", "../data_pipeline/silver") }}/interest_rate_lag_features.parquet')
