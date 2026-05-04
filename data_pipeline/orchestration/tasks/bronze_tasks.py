"""Bronze layer ingestion tasks for Prefect orchestration."""

import logging
import sys
from datetime import datetime
from pathlib import Path

from prefect import task

project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from data_pipeline.bronze.bronze_orchestrator import BronzeOrchestrator  # noqa: E402
from data_pipeline.orchestration.config.settings import RETRY_CONFIG  # noqa: E402

logger = logging.getLogger(__name__)

INGESTOR_NAMES = ["world_bank", "rbnz", "stats_nz", "mbie_tourism", "linz", "reinz"]

retry_cfg = RETRY_CONFIG["bronze"]


@task(
    name="ingest-world-bank",
    retries=retry_cfg["retries"],
    retry_delay_seconds=retry_cfg["retry_delay_seconds"],
    log_prints=True,
)
def ingest_world_bank(force_refresh: bool = False) -> dict:
    """Ingest World Bank data (GDP, inflation, unemployment, interest rates, population)."""
    print(f"[{datetime.now().isoformat()}] Starting World Bank ingestion...")
    orchestrator = BronzeOrchestrator()
    result = orchestrator.run_ingestor("world_bank", force_refresh=force_refresh)
    print(f"World Bank ingestion: {'SUCCESS' if result.get('success') else 'FAILED'}")
    return {"source": "world_bank", "result": result}


@task(
    name="ingest-rbnz",
    retries=retry_cfg["retries"],
    retry_delay_seconds=retry_cfg["retry_delay_seconds"],
    log_prints=True,
)
def ingest_rbnz(force_refresh: bool = False) -> dict:
    """Ingest RBNZ data (OCR, CPI, mortgage rates)."""
    print(f"[{datetime.now().isoformat()}] Starting RBNZ ingestion...")
    orchestrator = BronzeOrchestrator()
    result = orchestrator.run_ingestor("rbnz", force_refresh=force_refresh)
    print(f"RBNZ ingestion: {'SUCCESS' if result.get('success') else 'FAILED'}")
    return {"source": "rbnz", "result": result}


@task(
    name="ingest-stats-nz",
    retries=retry_cfg["retries"],
    retry_delay_seconds=retry_cfg["retry_delay_seconds"],
    log_prints=True,
)
def ingest_stats_nz(force_refresh: bool = False) -> dict:
    """Ingest Stats NZ data (building consents, population, income)."""
    print(f"[{datetime.now().isoformat()}] Starting Stats NZ ingestion...")
    orchestrator = BronzeOrchestrator()
    result = orchestrator.run_ingestor("stats_nz", force_refresh=force_refresh)
    print(f"Stats NZ ingestion: {'SUCCESS' if result.get('success') else 'FAILED'}")
    return {"source": "stats_nz", "result": result}


@task(
    name="ingest-mbie-tourism",
    retries=retry_cfg["retries"],
    retry_delay_seconds=retry_cfg["retry_delay_seconds"],
    log_prints=True,
)
def ingest_mbie_tourism(force_refresh: bool = False) -> dict:
    """Ingest MBIE tourism data (visitor arrivals, regional tourism)."""
    print(f"[{datetime.now().isoformat()}] Starting MBIE tourism ingestion...")
    orchestrator = BronzeOrchestrator()
    result = orchestrator.run_ingestor("mbie_tourism", force_refresh=force_refresh)
    print(f"MBIE tourism ingestion: {'SUCCESS' if result.get('success') else 'FAILED'}")
    return {"source": "mbie_tourism", "result": result}


@task(
    name="ingest-linz",
    retries=retry_cfg["retries"],
    retry_delay_seconds=retry_cfg["retry_delay_seconds"],
    log_prints=True,
)
def ingest_linz(force_refresh: bool = False) -> dict:
    """Ingest LINZ data (property titles, boundaries)."""
    print(f"[{datetime.now().isoformat()}] Starting LINZ ingestion...")
    orchestrator = BronzeOrchestrator()
    result = orchestrator.run_ingestor("linz", force_refresh=force_refresh)
    print(f"LINZ ingestion: {'SUCCESS' if result.get('success') else 'FAILED'}")
    return {"source": "linz", "result": result}


@task(
    name="ingest-reinz",
    retries=retry_cfg["retries"],
    retry_delay_seconds=retry_cfg["retry_delay_seconds"],
    log_prints=True,
)
def ingest_reinz(force_refresh: bool = False) -> dict:
    """Ingest REINZ data (property sales, median prices)."""
    print(f"[{datetime.now().isoformat()}] Starting REINZ ingestion...")
    orchestrator = BronzeOrchestrator()
    result = orchestrator.run_ingestor("reinz", force_refresh=force_refresh)
    print(f"REINZ ingestion: {'SUCCESS' if result.get('success') else 'FAILED'}")
    return {"source": "reinz", "result": result}


@task(
    name="ingest-all-bronze",
    retries=retry_cfg["retries"],
    retry_delay_seconds=retry_cfg["retry_delay_seconds"],
    log_prints=True,
)
def ingest_all_bronze(force_refresh: bool = False) -> dict:
    """Run all bronze ingestors sequentially (fallback for non-parallel execution)."""
    print(f"[{datetime.now().isoformat()}] Starting all bronze ingestions...")
    orchestrator = BronzeOrchestrator()
    result = orchestrator.run_ingestor("all", force_refresh=force_refresh)
    success_count = sum(
        1 for r in result.get("results", {}).values() if r.get("success")
    )
    total_count = len(result.get("results", {}))
    print(f"All bronze ingestion: {success_count}/{total_count} successful")
    return {"source": "all_bronze", "result": result}
