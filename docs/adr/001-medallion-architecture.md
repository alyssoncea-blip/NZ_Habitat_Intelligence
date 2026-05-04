# ADR-001: Medallion Architecture (Bronze/Silver/Gold)

**Status:** Accepted
**Date:** 2026-04-24
**Context:** Data pipeline design

## Decision
Adopt the medallion architecture pattern with three layers:
- **Bronze:** Raw data from APIs, stored as JSON with data contracts
- **Silver:** Feature-engineered parquet files with validated schemas
- **Gold:** KPI aggregates ready for dashboard consumption

## Rationale
- Clear separation of concerns between raw ingestion, transformation, and consumption
- Each layer has independent validation (Great Expectations)
- Data contracts provide provenance tracking across layers
- Enables reprocessing from any layer without full pipeline rerun

## Consequences
- **Positive:** Reproducible pipelines, clear data lineage, easy debugging
- **Negative:** Additional storage cost for intermediate layers
- **Tradeoff:** Chose Parquet over CSV for Silver/Gold (better compression, schema enforcement)
