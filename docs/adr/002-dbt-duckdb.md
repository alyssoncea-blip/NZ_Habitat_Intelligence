# ADR-002: dbt + DuckDB for Transformations

**Status:** Accepted
**Date:** 2026-04-24
**Context:** Analytics engineering stack selection

## Decision
Use dbt-core with dbt-duckdb adapter for Silver-to-Gold SQL transformations.

## Rationale
- DuckDB provides embedded, high-performance analytical SQL without server overhead
- dbt provides declarative SQL transformations with built-in testing and documentation
- Zero-config setup ideal for single-developer project
- Compatible with CI/CD (GitHub Actions) without external database

## Alternatives Considered
- **Spark:** Overkill for this data volume (< 1M rows)
- **PostgreSQL:** Requires server management, adds operational complexity
- **Python-only transformations:** Harder to test, document, and version

## Consequences
- **Positive:** SQL-first approach, easy testing, auto-generated docs
- **Negative:** DuckDB is single-process (not suitable for concurrent writes)
- **Future:** If scale increases, migrate dbt to Snowflake/BigQuery adapter
