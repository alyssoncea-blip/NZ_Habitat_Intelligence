# ADR-003: Data Contracts with Provenance Tracking

**Status:** Accepted
**Date:** 2026-04-24
**Context:** Data quality and governance

## Decision
Every data artifact (Bronze JSON, Silver Parquet, Gold Parquet) must have an accompanying `.contract.json` file containing:
- Source classification (real, fallback, proxy, synthetic)
- Confidence score (0-100)
- Quality metrics (null %, completeness, record count)
- Parent contract references (data lineage)

## Rationale
- Prevents silent mixing of real and synthetic data
- Enables dashboard to display data quality indicators
- Provides audit trail for data provenance
- Consumers can make informed decisions about data trustworthiness

## Consequences
- **Positive:** Transparent data quality, easy debugging, consumer confidence
- **Negative:** Additional metadata storage, contract generation overhead
- **Tradeoff:** Contracts are JSON (human-readable) rather than protobuf (compact)
