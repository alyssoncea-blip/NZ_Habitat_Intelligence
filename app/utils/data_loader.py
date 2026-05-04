"""
Data loader for dashboard KPI files.
Interface with Gold parquet outputs.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from threading import Lock
from typing import Dict, List, Optional, Tuple, Any

import duckdb
import pandas as pd

from ..utils.logger import get_logger

logger = get_logger(__name__)


class DataLoader:
    """
    Loads dashboard KPI data from the Gold layer.

    Implements singleton pattern and caching to avoid repeated disk I/O.
    Use invalidate_cache() to clear cache when data is refreshed.
    """

    _instance = None
    _lock = Lock()

    DASHBOARD_CODE_MAP = {
        "executive": "01-executive",
        "housing": "02-housing",
        "tourism": "03-tourism",
        "macro": "04-macro",
        "affordability": "05-affordability",
        "forecast": "06-forecast",
    }

    REQUIRED_QUALITY_COLUMNS = ["name", "value", "unit", "description"]
    CONTRACT_COLUMNS = ["source", "quality", "confidence_score", "notes"]

    def __new__(cls):
        """Singleton pattern to ensure single DataLoader instance."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._cache = {}
                    cls._instance._cache_lock = Lock()
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self.base_dir = os.path.join(
            os.path.dirname(__file__), "..", "..", "data_pipeline", "gold"
        )
        self.last_loaded_file = {}
        self._initialized = True

    def invalidate_cache(self, dashboard_name: Optional[str] = None):
        """
        Clear cached KPI data.

        Args:
            dashboard_name: If provided, only invalidate cache for this dashboard.
                           If None, clear all cache.
        """
        with self._cache_lock:
            if dashboard_name:
                self._cache.pop(dashboard_name, None)
                logger.debug(f"Cache invalidated for dashboard: {dashboard_name}")
            else:
                self._cache.clear()
                logger.debug("Cache invalidated for all dashboards")

    def _load_from_disk(self, dashboard_name: str) -> Optional[pd.DataFrame]:
        """Load KPIs from disk (internal method)."""
        dashboard_code = self.DASHBOARD_CODE_MAP.get(dashboard_name)
        if not dashboard_code:
            logger.error(f"Unknown dashboard: {dashboard_name}")
            return None

        for filename in self._candidate_files(dashboard_code):
            filepath = os.path.join(self.base_dir, filename)
            if not os.path.exists(filepath):
                continue

            try:
                logger.info(f"Loading KPI file: {filepath}")
                df = pd.read_parquet(filepath)

                has_quality = self._has_quality_schema(df)
                if not has_quality:
                    df = self._normalize_quality_schema(df, dashboard_name)

                self.last_loaded_file[dashboard_name] = filepath
                return df

            except Exception as exc:
                logger.error(f"Error loading {filename}: {exc}")

        logger.error(f"No compatible KPI file found for dashboard {dashboard_name}")
        return None

    def _candidate_files(self, dashboard_code):
        return [
            f"kpis-{dashboard_code}_complete.parquet",
            f"kpis_dashboard-{dashboard_code}_quality.parquet",
            f"kpis_{dashboard_code}.parquet",
        ]

    def _has_quality_schema(self, df):
        return all(col in df.columns for col in self.REQUIRED_QUALITY_COLUMNS)

    def _normalize_quality_schema(self, df, dashboard_name):
        normalized = df.copy()

        if "name" not in normalized.columns:
            normalized["name"] = [
                f"{dashboard_name.title()} KPI {i + 1}" for i in range(len(normalized))
            ]
        if "value" not in normalized.columns:
            normalized["value"] = None
        if "unit" not in normalized.columns:
            normalized["unit"] = ""
        if "description" not in normalized.columns:
            normalized["description"] = ""
        if "category" not in normalized.columns:
            normalized["category"] = dashboard_name
        if "source" not in normalized.columns:
            normalized["source"] = "Legacy Gold Output"

        return normalized

    def load_kpis_for_dashboard(self, dashboard_name, use_quality_format=True):
        """
        Load KPIs for a specific dashboard with caching.

        Uses cached data if available to avoid repeated disk I/O.
        Cache can be cleared with invalidate_cache().

        Args:
            dashboard_name: Dashboard key (executive, housing, tourism, etc.)
            use_quality_format: If True, require quality schema

        Returns:
            DataFrame or None if file is not found
        """
        # Check cache first
        cache_key = f"{dashboard_name}_{use_quality_format}"
        with self._cache_lock:
            if cache_key in self._cache:
                logger.debug(f"Cache hit for dashboard: {dashboard_name}")
                return self._cache[cache_key]

        # Load from disk
        df = self._load_from_disk(dashboard_name)
        if df is not None:
            # Store in cache
            with self._cache_lock:
                self._cache[cache_key] = df
            return df

        return None

    def load_all_kpis(self):
        """Load KPIs across all dashboards."""
        all_kpis = []

        for dashboard in self.DASHBOARD_CODE_MAP:
            kpis = self.load_kpis_for_dashboard(dashboard)
            if kpis is not None and not kpis.empty:
                enriched = kpis.copy()
                enriched["dashboard"] = dashboard
                all_kpis.append(enriched)

        if not all_kpis:
            logger.warning("No KPI datasets were loaded")
            return pd.DataFrame()

        return pd.concat(all_kpis, ignore_index=True)

    def get_kpi_metadata(self):
        """Load KPI metadata JSON with fallback generation."""
        metadata_files = [
            os.path.join(self.base_dir, "kpis_metadata_complete.json"),
            os.path.join(self.base_dir, "kpis_metadata_quality.json"),
            os.path.join(self.base_dir, "kpis_metadata.json"),
        ]

        for filepath in metadata_files:
            if not os.path.exists(filepath):
                continue
            try:
                with open(filepath, "r", encoding="utf-8") as handle:
                    return json.load(handle)
            except Exception as exc:
                logger.error(f"Error loading metadata {filepath}: {exc}")

        all_kpis = self.load_all_kpis()
        return {
            "version": "1.0",
            "generated": datetime.now().isoformat(),
            "kpi_count": int(len(all_kpis)) if not all_kpis.empty else 0,
            "dashboards": sorted(self.DASHBOARD_CODE_MAP.keys()),
        }

    def query_kpis_with_duckdb(self, query):
        """Run SQL query over all loaded KPIs using DuckDB."""
        conn = None
        try:
            all_kpis = self.load_all_kpis()
            if all_kpis.empty:
                logger.error("No KPIs available for query")
                return None

            conn = duckdb.connect(":memory:")
            conn.register("kpis", all_kpis)
            return conn.execute(query).fetchdf()
        except Exception as exc:
            logger.error(f"DuckDB query error: {exc}")
            return None
        finally:
            if conn is not None:
                conn.close()

    def get_dashboard_summary(self):
        """Return quick health summary for all dashboards."""
        summary = {}

        for dashboard in self.DASHBOARD_CODE_MAP:
            kpis = self.load_kpis_for_dashboard(dashboard)
            loaded_file = self.last_loaded_file.get(dashboard)

            if kpis is None or kpis.empty:
                summary[dashboard] = {
                    "kpi_count": 0,
                    "has_quality_format": False,
                    "status": "not_found",
                    "file": loaded_file,
                    "data_source": "unknown",
                    "confidence": 0,
                    "is_trusted": False,
                }
                continue

            updated_at = None
            if loaded_file and os.path.exists(loaded_file):
                updated_at = datetime.fromtimestamp(
                    os.path.getmtime(loaded_file)
                ).isoformat()

            contract = (
                self._load_contract_for_file(loaded_file) if loaded_file else None
            )

            data_source = "unknown"
            confidence = 50
            is_trusted = False

            if contract:
                data_source = contract.get("source", "unknown")
                confidence = contract.get("confidence_score", 50)
                is_trusted = self._is_trusted(contract)
            elif "data_source" in kpis.columns:
                sources = kpis["data_source"].unique()
                data_source = sources[0] if len(sources) == 1 else "mixed"
                if data_source in ["World Bank", "REAL"]:
                    confidence = 85
                    is_trusted = True
                elif data_source == "FALLBACK":
                    confidence = 10
                    is_trusted = False

            summary[dashboard] = {
                "kpi_count": len(kpis),
                "has_quality_format": self._has_quality_schema(kpis),
                "status": "loaded",
                "file": loaded_file,
                "updated_at": updated_at,
                "data_source": data_source,
                "confidence": confidence,
                "is_trusted": is_trusted,
            }

        return summary

    def _load_contract_for_file(self, filepath: str) -> Optional[Dict[str, Any]]:
        """Load data contract JSON for a parquet file."""
        if not filepath or not os.path.exists(filepath):
            return None

        contract_path = str(Path(filepath).with_suffix(".contract.json"))
        if not os.path.exists(contract_path):
            return None

        try:
            with open(contract_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Could not load contract {contract_path}: {e}")
            return None

    def _is_trusted(
        self, contract: Dict[str, Any], min_confidence: float = 70.0
    ) -> bool:
        """Check if data meets trust threshold based on contract."""
        if not contract:
            return False

        confidence = contract.get("confidence_score", 0)
        source = contract.get("source", "")

        # Trust only if confidence is high AND source is real
        if source in ["real", "REAL"]:
            return confidence >= min_confidence

        return False

    def get_data_quality_warnings(self) -> List[Dict[str, Any]]:
        """Get warnings for all dashboards with untrusted data.

        Returns:
            List of warning dicts with dashboard, reason, and confidence.
        """
        warnings = []
        summary = self.get_dashboard_summary()

        for dashboard, info in summary.items():
            if not info.get("is_trusted", False) and info.get("status") == "loaded":
                reason = "low_confidence"
                if info.get("data_source") in ["FALLBACK", "SYNTHETIC"]:
                    reason = f"data_source_{info['data_source'].lower()}"

                warnings.append(
                    {
                        "dashboard": dashboard,
                        "reason": reason,
                        "confidence": info.get("confidence", 0),
                        "data_source": info.get("data_source", "unknown"),
                        "message": (
                            f"⚠️ {dashboard}: Data is from {info.get('data_source', 'unknown')} "
                            f"(confidence: {info.get('confidence', 0):.0f}%)"
                        ),
                    }
                )

        return warnings

    def load_kpis_with_confidence(
        self, dashboard_name: str
    ) -> Tuple[Optional[pd.DataFrame], Optional[Dict[str, Any]]]:
        """Load KPIs along with their data contract.

        Args:
            dashboard_name: Dashboard key

        Returns:
            Tuple of (DataFrame, contract dict or None)
        """
        df = self.load_kpis_for_dashboard(dashboard_name)
        if df is None:
            return None, None

        loaded_file = self.last_loaded_file.get(dashboard_name)
        contract = self._load_contract_for_file(loaded_file) if loaded_file else None

        return df, contract

    def filter_trusted_kpis(self, min_confidence: float = 70.0) -> pd.DataFrame:
        """Load all KPIs but only include rows from trusted sources.

        Args:
            min_confidence: Minimum confidence score to be considered trusted

        Returns:
            DataFrame with only trusted KPI data
        """
        all_kpis = self.load_all_kpis()
        if all_kpis.empty:
            return all_kpis

        # If DataFrame has data_source column, use it
        if "data_source" in all_kpis.columns:
            trusted_sources = ["World Bank", "REAL"]
            return all_kpis[all_kpis["data_source"].isin(trusted_sources)].copy()

        return all_kpis

    def get_data_source_summary(self) -> Dict[str, int]:
        """Get count of KPIs by data source across all dashboards.

        Returns:
            Dict mapping source name to count
        """
        all_kpis = self.load_all_kpis()
        if all_kpis.empty:
            return {}

        if "data_source" not in all_kpis.columns:
            return {"unknown": len(all_kpis)}

        return all_kpis["data_source"].value_counts().to_dict()


def load_kpis_for_dashboard(dashboard_name, use_quality_format=True):
    """Convenience wrapper for single-dashboard load."""
    loader = DataLoader()
    return loader.load_kpis_for_dashboard(dashboard_name, use_quality_format)


def get_dashboard_summary():
    """Convenience wrapper for summary."""
    loader = DataLoader()
    return loader.get_dashboard_summary()


def load_all_kpis():
    """Convenience wrapper for all dashboards."""
    loader = DataLoader()
    return loader.load_all_kpis()
