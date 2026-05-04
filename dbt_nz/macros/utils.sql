-- Macro: Generate surrogate key for deduplication
-- Usage: {{ dbt_utils.generate_surrogate_key(['year', 'region', 'kpi_name']) }}

{% macro generate_surrogate_key(fields) -%}
    {{ return(adapter.dispatch('generate_surrogate_key', 'dbt_nz')(fields)) }}
{%- endmacro %}

{% macro default__generate_surrogate_key(fields) %}
    md5({{ dbt_nz.concat_fields(fields) }})
{% endmacro %}

{% macro concat_fields(fields) %}
    {% set concatenated = namespace(value='') %}
    {% for field in fields %}
        {% set concatenated.value = concatenated.value ~ "coalesce(cast(" ~ field ~ " as varchar), '')" %}
        {% if not loop.last %}
            {% set concatenated.value = concatenated.value ~ " || '|'" %}
        {% endif %}
    {% endfor %}
    {{ return(concatenated.value) }}
{% endmacro %}


-- Macro: Check if this is an incremental run
{% macro is_incremental_run() %}
    {% if is_incremental() %}
        true
    {% else %}
        false
    {% endif %}
{% endmacro %}


-- Macro: Get the maximum date from the target table for incremental filtering
{% macro get_max_date(column_name='year', table_name=None) %}
    {% set target_table = table_name or this %}
    {% set query %}
        select max({{ column_name }}) from {{ target_table }}
    {% endset %}
    
    {% if execute %}
        {% set result = run_query(query) %}
        {% set max_val = result.columns[0].values()[0] %}
        {{ return(max_val) }}
    {% else %}
        {{ return(None) }}
    {% endif %}
{% endmacro %}


-- Macro: Apply incremental filter
{% macro incremental_filter(column_name='year', lookback_periods=1) %}
    {% if is_incremental() %}
        {% set max_val = dbt_nz.get_max_date(column_name) %}
        {% if max_val is not none %}
            where {{ column_name }} > ({{ max_val }} - {{ lookback_periods }})
        {% else %}
            where 1=1
        {% endif %}
    {% else %}
        where 1=1
    {% endif %}
{% endmacro %}


-- Macro: Deduplicate records
{% macro deduplicate(table_name, partition_by, order_by='year desc') %}
    with ranked as (
        select *,
            row_number() over (
                partition by {{ partition_by }}
                order by {{ order_by }}
            ) as rn
        from {{ table_name }}
    )
    select * exclude rn
    from ranked
    where rn = 1
{% endmacro %}
