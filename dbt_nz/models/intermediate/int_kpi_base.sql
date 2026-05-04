-- Intermediate: unified KPI base from all silver features
-- Joins affordability, interest rates, tourism, supply deficit, rent/income
-- Adds window functions for YoY changes and rolling averages

with affordability as (
    select * from {{ ref('stg_affordability') }}
),
interest_rates as (
    select * from {{ ref('stg_interest_rates') }}
),
tourism as (
    select * from {{ ref('stg_tourism') }}
),
supply as (
    select * from {{ ref('stg_supply_deficit') }}
),
rent_income as (
    select * from {{ ref('stg_rent_income') }}
),
base as (
    select
        coalesce(a.year, ir.year, t.year, s.year, ri.year) as year,
        coalesce(a.region, s.region, ri.region) as region,

        -- Affordability metrics
        a.gdp_per_capita,
        a.price_to_income_ratio,
        a.affordability_index,

        -- Interest rate metrics
        ir.ocr_value,
        ir.mortgage_rate_2yr,
        ir.ocr_change_bps,
        ir.rate_volatility,

        -- Tourism metrics
        t.visitor_arrivals,
        t.tourism_expenditure,
        t.tourism_pressure_index,

        -- Supply metrics
        s.building_consents,
        s.population_growth,
        s.supply_deficit_score,

        -- Rent/income metrics
        ri.median_weekly_rent,
        ri.rent_to_income_ratio,
        ri.rent_inflation_rate

    from affordability a
    full outer join interest_rates ir on a.year = ir.year
    full outer join tourism t on a.year = t.year
    full outer join supply s on a.year = s.year and a.region = s.region
    full outer join rent_income ri on a.year = ri.year and a.region = ri.region
)

select
    year,
    region,

    -- Core metrics
    gdp_per_capita,
    price_to_income_ratio,
    affordability_index,
    ocr_value,
    mortgage_rate_2yr,
    ocr_change_bps,
    rate_volatility,
    visitor_arrivals,
    tourism_expenditure,
    tourism_pressure_index,
    building_consents,
    population_growth,
    supply_deficit_score,
    median_weekly_rent,
    rent_to_income_ratio,
    rent_inflation_rate,

    -- YoY changes using window functions
    round(
        (gdp_per_capita - lag(gdp_per_capita, 1) over (partition by region order by year))
        / nullif(lag(gdp_per_capita, 1) over (partition by region order by year), 0) * 100,
        2
    ) as gdp_per_capita_yoy_pct,

    round(
        (affordability_index - lag(affordability_index, 1) over (partition by region order by year)),
        2
    ) as affordability_index_yoy_change,

    round(
        (building_consents - lag(building_consents, 1) over (partition by region order by year))
        / nullif(lag(building_consents, 1) over (partition by region order by year), 0) * 100,
        2
    ) as building_consents_yoy_pct,

    round(
        (median_weekly_rent - lag(median_weekly_rent, 1) over (partition by region order by year))
        / nullif(lag(median_weekly_rent, 1) over (partition by region order by year), 0) * 100,
        2
    ) as rent_yoy_pct,

    -- 3-year rolling averages
    round(
        avg(gdp_per_capita) over (partition by region order by year rows between 2 preceding and current row),
        0
    ) as gdp_per_capita_3yr_avg,

    round(
        avg(affordability_index) over (partition by region order by year rows between 2 preceding and current row),
        2
    ) as affordability_index_3yr_avg,

    round(
        avg(tourism_pressure_index) over (partition by region order by year rows between 2 preceding and current row),
        2
    ) as tourism_pressure_3yr_avg,

    -- Rank within year
    rank() over (partition by year order by affordability_index desc) as affordability_rank

from base
