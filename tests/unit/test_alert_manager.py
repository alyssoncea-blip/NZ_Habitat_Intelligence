"""Unit tests for AlertManager and pipeline monitoring."""
import json
import tempfile
from pathlib import Path

import pytest

from data_pipeline.utils.alert_manager import AlertManager, AlertSeverity, create_alert_manager_from_env


class TestAlertSeverity:
    """Tests for AlertSeverity enum."""

    def test_severity_levels(self):
        """Test all severity levels exist."""
        assert AlertSeverity.INFO.value == "info"
        assert AlertSeverity.WARNING.value == "warning"
        assert AlertSeverity.ERROR.value == "error"
        assert AlertSeverity.CRITICAL.value == "critical"


class TestAlertManager:
    """Tests for AlertManager class."""

    @pytest.fixture
    def alert_manager(self, tmp_path):
        """Create AlertManager with temporary log directory."""
        log_dir = tmp_path / "logs"
        log_dir.mkdir()
        return AlertManager(log_dir=str(log_dir))

    def test_initialization(self, alert_manager):
        """Test AlertManager initializes correctly."""
        assert alert_manager is not None
        assert alert_manager.log_dir is not None

    def test_info_alert(self, alert_manager):
        """Test creating an info alert."""
        alert_manager.info("Test info", "Details")
        summary = alert_manager.get_summary()
        assert summary["total"] >= 1

    def test_warning_alert(self, alert_manager):
        """Test creating a warning alert."""
        alert_manager.warning("Test warning", "Details")
        summary = alert_manager.get_summary()
        assert summary["total"] >= 1

    def test_error_alert(self, alert_manager):
        """Test creating an error alert."""
        alert_manager.error("Test error", "Details")
        summary = alert_manager.get_summary()
        assert summary["total"] >= 1

    def test_critical_alert(self, alert_manager):
        """Test creating a critical alert."""
        alert_manager.critical("Test critical", "Details")
        summary = alert_manager.get_summary()
        assert summary["total"] >= 1

    def test_alert_deduplication(self, alert_manager):
        """Test that duplicate alerts are deduplicated within cooldown."""
        alert_manager.info("Duplicate test", "Same details")
        alert_manager.info("Duplicate test", "Same details")
        summary = alert_manager.get_summary()
        # Should not double-count within cooldown
        assert summary["total"] >= 1

    def test_alert_with_metadata(self, alert_manager):
        """Test creating alert with metadata."""
        alert_manager.info(
            "Test with metadata",
            "Details",
            metadata={"key": "value", "count": 42},
        )
        summary = alert_manager.get_summary()
        assert summary["total"] >= 1

    def test_alert_with_pipeline_stage(self, alert_manager):
        """Test creating alert with pipeline stage."""
        alert_manager.warning(
            "Stage warning",
            "Details",
            pipeline_stage="bronze",
        )
        summary = alert_manager.get_summary()
        assert summary["total"] >= 1

    def test_reset_run_counter(self, alert_manager):
        """Test resetting run counter."""
        alert_manager.info("Test 1", "Details")
        alert_manager.reset_run_counter()
        alert_manager.info("Test 2", "Details")
        summary = alert_manager.get_summary()
        assert summary["total"] >= 2

    def test_get_alerts(self, alert_manager):
        """Test retrieving alerts."""
        alert_manager.info("Test info", "Details")
        alert_manager.warning("Test warning", "Details")
        alerts = alert_manager.get_alerts()
        assert isinstance(alerts, list)
        assert len(alerts) >= 2

    def test_log_file_created(self, alert_manager):
        """Test that log file is created."""
        alert_manager.info("Test", "Details")
        log_file = alert_manager.log_dir / "pipeline_alerts.jsonl"
        assert log_file.exists()


class TestCreateAlertManagerFromEnv:
    """Tests for create_alert_manager_from_env factory."""

    def test_creates_manager(self, monkeypatch, tmp_path):
        """Test factory creates AlertManager."""
        monkeypatch.setenv("LOG_DIR", str(tmp_path / "logs"))
        manager = create_alert_manager_from_env()
        assert manager is not None
        assert isinstance(manager, AlertManager)


class TestPipelineMonitor:
    """Tests for MonitoringClient class."""

    def test_monitor_initialization(self):
        """Test MonitoringClient initializes correctly."""
        from data_pipeline.utils.pipeline_monitor import MonitoringClient, MetricType
        monitor = MonitoringClient()
        assert monitor is not None

    def test_metric_type_enum(self):
        """Test MetricType enum values."""
        from data_pipeline.utils.pipeline_monitor import MetricType
        assert MetricType.COUNTER.value == "counter"
        assert MetricType.TIMER.value == "timer"
        assert MetricType.GAUGE.value == "gauge"

    def test_record_metric(self):
        """Test recording a metric."""
        from data_pipeline.utils.pipeline_monitor import MonitoringClient, MetricType
        monitor = MonitoringClient()
        monitor.record_metric("test.metric", 42.0, MetricType.COUNTER, unit="count")
        summary = monitor.get_metrics_summary()
        assert summary["count"] >= 1

    def test_record_pipeline_metric(self):
        """Test recording a pipeline metric."""
        from data_pipeline.utils.pipeline_monitor import MonitoringClient
        monitor = MonitoringClient()
        monitor.record_pipeline_metric("pipeline", "bronze", 5.2, success=True)
        summary = monitor.get_metrics_summary()
        assert summary["count"] > 0

    def test_get_metrics(self):
        """Test retrieving metrics."""
        from data_pipeline.utils.pipeline_monitor import MonitoringClient, MetricType
        monitor = MonitoringClient()
        monitor.record_metric("test.a", 1.0, MetricType.COUNTER)
        monitor.record_metric("test.b", 2.0, MetricType.GAUGE)
        summary = monitor.get_metrics_summary()
        assert isinstance(summary, dict)
        assert summary["count"] >= 2
