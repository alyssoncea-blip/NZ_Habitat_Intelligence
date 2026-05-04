# ── Base stage ─────────────────────────────────────────────────────────────
FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# ── Application ─────────────────────────────────────────────────────────────
COPY app/ ./app/
COPY data_pipeline/ ./data_pipeline/
COPY dbt_nz/ ./dbt_nz/
COPY great_expectations/ ./great_expectations/
COPY run_dashboard.py ./run_dashboard.py
COPY prefect.yaml ./prefect.yaml

# Create data directories
RUN mkdir -p /app/data/duckdb \
    /app/data_pipeline/bronze \
    /app/data_pipeline/silver \
    /app/data_pipeline/gold \
    /app/logs \
    /app/great_expectations/validations

# ── Runtime ─────────────────────────────────────────────────────────────────
EXPOSE 8050

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8050')" || exit 1

# Default: run dashboard
# Override with: prefect worker start -p nz-habitat
ENTRYPOINT ["python"]
CMD ["run_dashboard.py"]
