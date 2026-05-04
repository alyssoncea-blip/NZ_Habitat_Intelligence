-- Generic test: all KPI values must be non-negative
{% test kpi_values_non_negative(model) %}

select *
from {{ model }}
where kpi_value < 0

{% endtest %}
