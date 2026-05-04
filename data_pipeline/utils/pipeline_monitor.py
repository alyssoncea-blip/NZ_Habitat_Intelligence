"""
Monitoring and Alerting for NZ Habitat Intelligence Pipeline.
Provides metrics collection, health checks, and alerting capabilities for production.
"""
import json
import logging
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field

import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


class AlertLevel(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class MetricType(Enum):
    """Types of metrics to track."""
    GAUGE = "gauge"  # Single value
    COUNTER = "counter"  # Incremental count
    HISTOGRAM = "histogram"  # Distribution
    TIMER = "timer"  # Duration


@dataclass
class Alert:
    """Represents a monitoring alert."""
    level: AlertLevel
    title: str
    message: str
    source: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "level": self.level.value,
            "title": self.title,
            "message": self.message,
            "source": self.source,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }


@dataclass
class Metric:
    """Represents a metric data point."""
    name: str
    value: float
    metric_type: MetricType
    timestamp: datetime = field(default_factory=datetime.now)
    tags: Dict[str, str] = field(default_factory=dict)
    unit: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "value": self.value,
            "type": self.metric_type.value,
            "timestamp": self.timestamp.isoformat(),
            "tags": self.tags,
            "unit": self.unit,
        }


class MonitoringClient:
    """
    Client for pipeline monitoring and alerting.
    Collects metrics, performs health checks, and triggers alerts.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize monitoring client.

        Args:
            config: Optional configuration dict with settings like
                   alert thresholds, check intervals, etc.
        """
        self.config = config or self._default_config()
        self.logger = logging.getLogger(__name__)
        self._metrics: List[Metric] = []
        self._alerts: List[Alert] = []

    def _default_config(self) -> Dict[str, Any]:
        """Return default configuration."""
        return {
            "alert_thresholds": {
                "low_confidence_kpi_threshold": 70.0,
                "null_percentage_threshold": 20.0,
                "pipeline_duration_max_seconds": 3600,
                "data_freshness_max_hours": 48,
            },
            "alert_channels": ["log"],  # Could add "slack", "email", etc.
            "health_check_interval_seconds": 300,
        }

    def record_metric(
        self,
        name: str,
        value: float,
        metric_type: MetricType = MetricType.GAUGE,
        tags: Optional[Dict[str, str]] = None,
        unit: str = ""
    ):
        """
        Record a metric value.

        Args:
            name: Metric name
            value: Metric value
            metric_type: Type of metric
            tags: Optional tags for categorization
            unit: Unit of measurement
        """
        metric = Metric(
            name=name,
            value=value,
            metric_type=metric_type,
            tags=tags or {},
            unit=unit
        )
        self._metrics.append(metric)
        self.logger.debug(f"Recorded metric: {name}={value} {unit}")

    def record_pipeline_metric(
        self,
        pipeline: str,
        stage: str,
        duration_seconds: float,
        success: bool,
        records_processed: int = 0,
        error_message: Optional[str] = None
    ):
        """
        Record a pipeline execution metric.

        Args:
            pipeline: Pipeline name (bronze, silver, gold)
            stage: Stage name (ingestion, transformation, etc.)
            duration_seconds: Execution duration
            success: Whether pipeline succeeded
            records_processed: Number of records processed
            error_message: Optional error message if failed
        """
        tags = {
            "pipeline": pipeline,
            "stage": stage,
            "status": "success" if success else "failure"
        }

        self.record_metric(
            f"pipeline.duration",
            duration_seconds,
            MetricType.TIMER,
            tags=tags,
            unit="seconds"
        )

        self.record_metric(
            f"pipeline.records",
            records_processed,
            MetricType.GAUGE,
            tags=tags,
            unit="records"
        )

        if not success:
            self.record_alert(
                AlertLevel.ERROR,
                f"Pipeline {pipeline}/{stage} failed",
                error_message or "Unknown error",
                source=f"{pipeline}.{stage}"
            )

    def record_kpi_metrics(self, kpis_df: pd.DataFrame):
        """
        Record metrics for all KPIs in a DataFrame.

        Args:
            kpis_df: DataFrame with KPI data
        """
        if kpis_df.empty:
            return

        for _, row in kpis_df.iterrows():
            tags = {
                "category": str(row.get("category", "unknown")),
                "source": str(row.get("source", "unknown")),
            }

            if "value" in row:
                self.record_metric(
                    "kpi.value",
                    float(row["value"]) if pd.notna(row["value"]) else 0,
                    MetricType.GAUGE,
                    tags=tags,
                    unit=str(row.get("unit", ""))
                )

            if "confidence" in row:
                self.record_metric(
                    "kpi.confidence",
                    float(row["confidence"]) if pd.notna(row["confidence"]) else 0,
                    MetricType.GAUGE,
                    tags=tags,
                    unit="score"
                )

    def record_data_quality_metrics(self, quality_report: Dict[str, Any]):
        """
        Record metrics from a data quality report.

        Args:
            quality_report: Report from generate_quality_report()
        """
        if "overall_quality_score" in quality_report:
            self.record_metric(
                "data_quality.overall_score",
                quality_report["overall_quality_score"],
                MetricType.GAUGE,
                unit="score"
            )

        if "artifacts_total" in quality_report:
            self.record_metric(
                "data_quality.artifact_count",
                quality_report["artifacts_total"],
                MetricType.GAUGE,
                unit="artifacts"
            )

    def record_alert(
        self,
        level: AlertLevel,
        title: str,
        message: str,
        source: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Record an alert.

        Args:
            level: Alert severity
            title: Alert title
            message: Alert message
            source: Source of alert
            metadata: Optional additional metadata
        """
        alert = Alert(
            level=level,
            title=title,
            message=message,
            source=source,
            metadata=metadata or {}
        )
        self._alerts.append(alert)

        # Log based on level
        log_msg = f"[{level.value.upper()}] {title}: {message} (source: {source})"
        if level == AlertLevel.CRITICAL or level == AlertLevel.ERROR:
            self.logger.error(log_msg)
        elif level == AlertLevel.WARNING:
            self.logger.warning(log_msg)
        else:
            self.logger.info(log_msg)

    def check_confidence_threshold(self, kpis_df: pd.DataFrame) -> List[Alert]:
        """
        Check if any KPIs fall below confidence threshold.

        Args:
            kpis_df: DataFrame with KPI data

        Returns:
            List of alerts generated
        """
        alerts = []
        threshold = self.config["alert_thresholds"]["low_confidence_kpi_threshold"]

        if "confidence" not in kpis_df.columns:
            return alerts

        low_confidence = kpis_df[kpis_df["confidence"] < threshold]
        if len(low_confidence) > 0:
            for _, row in low_confidence.iterrows():
                alert = Alert(
                    level=AlertLevel.WARNING,
                    title=f"Low confidence KPI: {row.get('name', 'Unknown')}",
                    message=f"Confidence score {row.get('confidence', 0):.1f} is below threshold {threshold}",
                    source="kpi_monitor",
                    metadata={"kpi_name": row.get("name"), "confidence": row.get("confidence")}
                )
                alerts.append(alert)
                self.logger.warning(f"Low confidence KPI: {row.get('name')} = {row.get('confidence')}")

        return alerts

    def check_data_freshness(
        self,
        contract_path: str,
        max_age_hours: Optional[int] = None
    ) -> Optional[Alert]:
        """
        Check if data is fresh enough.

        Args:
            contract_path: Path to data contract
            max_age_hours: Maximum age in hours (uses config default if None)

        Returns:
            Alert if data is stale, None otherwise
        """
        max_age = max_age_hours or self.config["alert_thresholds"]["data_freshness_max_hours"]

        try:
            contract_file = Path(contract_path)
            if not contract_file.exists():
                return None

            # Get file modification time
            mtime = datetime.fromtimestamp(contract_file.stat().st_mtime)
            age_hours = (datetime.now() - mtime).total_seconds() / 3600

            if age_hours > max_age:
                alert = Alert(
                    level=AlertLevel.WARNING,
                    title=f"Stale data detected: {contract_file.name}",
                    message=f"Data is {age_hours:.1f} hours old (max: {max_age})",
                    source="freshness_check",
                    metadata={"age_hours": age_hours, "max_age_hours": max_age}
                )
                self.logger.warning(f"Stale data: {contract_file.name} is {age_hours:.1f}h old")
                return alert

        except Exception as e:
            self.logger.error(f"Error checking data freshness: {e}")

        return None

    def check_pipeline_health(self, bronze_dir: str, silver_dir: str, gold_dir: str) -> Dict[str, Any]:
        """
        Perform comprehensive pipeline health check.

        Args:
            bronze_dir: Bronze layer directory
            silver_dir: Silver layer directory
            gold_dir: Gold layer directory

        Returns:
            Health check results dict
        """
        results = {
            "timestamp": datetime.now().isoformat(),
            "status": "healthy",
            "checks": {},
            "alerts": []
        }

        # Check bronze layer
        bronze_status = self._check_layer_health(Path(bronze_dir), "bronze")
        results["checks"]["bronze"] = bronze_status
        if bronze_status["status"] != "healthy":
            results["status"] = "degraded"

        # Check silver layer
        silver_status = self._check_layer_health(Path(silver_dir), "silver")
        results["checks"]["silver"] = silver_status
        if silver_status["status"] != "healthy":
            results["status"] = "degraded"

        # Check gold layer
        gold_status = self._check_layer_health(Path(gold_dir), "gold")
        results["checks"]["gold"] = gold_status
        if gold_status["status"] != "healthy":
            results["status"] = "degraded"

        # Overall data count check
        total_files = (
            bronze_status["file_count"] +
            silver_status["file_count"] +
            gold_status["file_count"]
        )
        if total_files == 0:
            results["status"] = "critical"
            results["alerts"].append({
                "level": "critical",
                "message": "No data files found in pipeline"
            })

        return results

    def _check_layer_health(self, layer_path: Path, layer_name: str) -> Dict[str, Any]:
        """Check health of a single pipeline layer."""
        status = {
            "layer": layer_name,
            "status": "healthy",
            "file_count": 0,
            "contract_count": 0,
            "latest_file": None
        }

        if not layer_path.exists():
            status["status"] = "missing"
            return status

        # Count parquet files
        parquet_files = list(layer_path.glob("*.parquet"))
        status["file_count"] = len(parquet_files)

        # Count contract files
        contract_files = list(layer_path.glob("*.contract.json"))
        status["contract_count"] = len(contract_files)

        # Find latest file
        if parquet_files:
            latest = max(parquet_files, key=lambda f: f.stat().st_mtime)
            status["latest_file"] = latest.name
            status["latest_modified"] = datetime.fromtimestamp(
                latest.stat().st_mtime
            ).isoformat()

        # Check for issues
        if status["file_count"] == 0:
            status["status"] = "empty"

        if status["file_count"] > 0 and status["contract_count"] == 0:
            status["status"] = "warning"
            self.logger.warning(f"Layer {layer_name} has files but no contracts")

        return status

    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get summary of collected metrics."""
        if not self._metrics:
            return {"count": 0, "metrics": []}

        # Group by name
        by_name: Dict[str, List[float]] = {}
        for m in self._metrics:
            if m.name not in by_name:
                by_name[m.name] = []
            by_name[m.name].append(m.value)

        summaries = []
        for name, values in by_name.items():
            summaries.append({
                "name": name,
                "count": len(values),
                "min": min(values),
                "max": max(values),
                "mean": np.mean(values),
                "latest": values[-1]
            })

        return {
            "count": len(self._metrics),
            "metrics": summaries
        }

    def get_alerts_summary(self) -> Dict[str, Any]:
        """Get summary of recorded alerts."""
        if not self._alerts:
            return {"count": 0, "alerts": [], "by_level": {}}

        by_level: Dict[str, int] = {}
        for alert in self._alerts:
            level = alert.level.value
            by_level[level] = by_level.get(level, 0) + 1

        return {
            "count": len(self._alerts),
            "alerts": [a.to_dict() for a in self._alerts[-10:]],  # Last 10
            "by_level": by_level
        }

    def export_metrics(self, output_path: str):
        """
        Export metrics to JSON file.

        Args:
            output_path: Path to output file
        """
        export_data = {
            "exported_at": datetime.now().isoformat(),
            "metrics": [m.to_dict() for m in self._metrics],
            "alerts": [a.to_dict() for a in self._alerts],
            "summary": {
                "metrics": self.get_metrics_summary(),
                "alerts": self.get_alerts_summary()
            }
        }

        with open(output_path, "w") as f:
            json.dump(export_data, f, indent=2, default=str)

        self.logger.info(f"Exported metrics to {output_path}")


def create_health_check_handler(monitoring_client: MonitoringClient) -> Callable:
    """
    Create a health check handler for the pipeline.

    Args:
        monitoring_client: Configured monitoring client

    Returns:
        Handler function that can be called periodically
    """
    def health_check(
        bronze_dir: str = "data_pipeline/bronze",
        silver_dir: str = "data_pipeline/silver",
        gold_dir: str = "data_pipeline/gold"
    ) -> Dict[str, Any]:
        """Run health check and return results."""
        results = monitoring_client.check_pipeline_health(
            bronze_dir, silver_dir, gold_dir
        )

        # Record health metrics
        monitoring_client.record_metric(
            "health.check.status",
            1 if results["status"] == "healthy" else 0,
            MetricType.GAUGE,
            tags={"status": results["status"]}
        )

        return results

    return health_check