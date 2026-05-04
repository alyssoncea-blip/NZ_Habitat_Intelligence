{{
  config(
    materialized='external',
    location=var('silver_dir', '../data_pipeline/silver') ~ '/tourism_lag_analysis_features.parquet',
    format='parquet'
  )
}}

select *
from read_parquet('{{ var("silver_dir", "../data_pipeline/silver") }}/tourism_lag_analysis_features.parquet')
