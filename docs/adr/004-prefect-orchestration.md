# ADR-004: Prefect for Production Orchestration

**Status:** Accepted
**Date:** 2026-04-28
**Context:** Pipeline scheduling and monitoring

## Decision
Use Prefect 2.x as the production orchestration engine, replacing sequential CLI execution.

## Rationale
- Python-native API matches existing codebase
- Built-in retry, caching, and scheduling
- Prefect UI provides observability without additional infrastructure
- Local mode works without server (development), Cloud mode for production
- Lightweight compared to Airflow (no JVM, no complex setup)

## Alternatives Considered
- **Airflow:** More enterprise-standard but heavier, requires more infrastructure
- **Cron:** Too simple, no retry/observability
- **Makefile:** Good for development, not suitable for production scheduling

## Consequences
- **Positive:** Production-grade scheduling, retries, UI monitoring
- **Negative:** Additional dependency, learning curve for team
- **Future:** Can migrate to Prefect Cloud for enterprise features (RBAC, SSO)
