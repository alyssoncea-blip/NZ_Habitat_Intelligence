-- Macro: ensure all gold models have required columns
{% test gold_kpi_schema(model) %}

select *
from {{ model }}
where kpi_name is null
   or kpi_value is null
   or unit is null
   or description is null
   or dashboard is null
   or category is null

{% endtest %}
