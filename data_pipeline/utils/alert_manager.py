"""Pipeline Alert Manager — multi-channel failure notifications.

Supports log file, console, email, and webhook notification channels.
Alerts are deduplicated within a cooldown window to prevent spam.
"""
import json
import logging
import os
import time
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertChannel(Enum):
    LOG = "log"
    CONSOLE = "console"
    FILE = "file"
    WEBHOOK = "webhook"


class Alert:
    """Represents a pipeline alert."""

    def __init__(
        self,
        severity: AlertSeverity,
        title: str,
        message: str,
        source: str = "",
        pipeline_stage: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.severity = severity
        self.title = title
        self.message = message
        self.source = source
        self.pipeline_stage = pipeline_stage
        self.metadata = metadata or {}
        self.timestamp = datetime.now()
        self.dispatched = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "severity": self.severity.value,
            "title": self.title,
            "message": self.message,
            "source": self.source,
            "pipeline_stage": self.pipeline_stage,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }

    def __repr__(self):
        return f"Alert({self.severity.value.upper()}: {self.title})"


class AlertManager:
    """Manages pipeline alerts with multi-channel dispatch and deduplication."""

    def __init__(
        self,
        log_dir: str = "logs",
        webhook_url: Optional[str] = None,
        email_recipients: Optional[List[str]] = None,
        cooldown_seconds: int = 300,
        max_alerts_per_run: int = 50,
    ):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.webhook_url = webhook_url
        self.email_recipients = email_recipients or []
        self.cooldown_seconds = cooldown_seconds
        self.max_alerts_per_run = max_alerts_per_run

        self._alerts: List[Alert] = []
        self._alert_history: Dict[str, float] = {}  # dedup key -> last dispatched time
        self._alerts_this_run = 0

    def alert(
        self,
        severity: AlertSeverity,
        title: str,
        message: str,
        source: str = "",
        pipeline_stage: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Alert:
        """Create and dispatch an alert."""
        alert = Alert(
            severity=severity,
            title=title,
            message=message,
            source=source,
            pipeline_stage=pipeline_stage,
            metadata=metadata,
        )
        self._alerts.append(alert)
        self._dispatch(alert)
        return alert

    def info(self, title: str, message: str, **kwargs) -> Alert:
        return self.alert(AlertSeverity.INFO, title, message, **kwargs)

    def warning(self, title: str, message: str, **kwargs) -> Alert:
        return self.alert(AlertSeverity.WARNING, title, message, **kwargs)

    def error(self, title: str, message: str, **kwargs) -> Alert:
        return self.alert(AlertSeverity.ERROR, title, message, **kwargs)

    def critical(self, title: str, message: str, **kwargs) -> Alert:
        return self.alert(AlertSeverity.CRITICAL, title, message, **kwargs)

    def _dedup_key(self, alert: Alert) -> str:
        return f"{alert.pipeline_stage}:{alert.title}:{alert.message[:80]}"

    def _is_cooldown(self, alert: Alert) -> bool:
        key = self._dedup_key(alert)
        last = self._alert_history.get(key, 0)
        return (time.time() - last) < self.cooldown_seconds

    def _dispatch(self, alert: Alert):
        """Dispatch alert to all configured channels."""
        if self._alerts_this_run >= self.max_alerts_per_run:
            return

        # Skip if in cooldown (except CRITICAL)
        if alert.severity != AlertSeverity.CRITICAL and self._is_cooldown(alert):
            return

        self._alerts_this_run += 1
        key = self._dedup_key(alert)
        self._alert_history[key] = time.time()

        # Always log
        self._dispatch_log(alert)
        self._dispatch_console(alert)

        # Write to alert log file
        self._dispatch_file(alert)

        # Webhook (if configured)
        if self.webhook_url:
            self._dispatch_webhook(alert)

    def _dispatch_log(self, alert: Alert):
        msg = f"[PIPELINE ALERT] [{alert.severity.value.upper()}] {alert.title}: {alert.message}"
        if alert.pipeline_stage:
            msg = f"[{alert.pipeline_stage}] {msg}"
        if alert.severity == AlertSeverity.CRITICAL:
            logger.critical(msg)
        elif alert.severity == AlertSeverity.ERROR:
            logger.error(msg)
        elif alert.severity == AlertSeverity.WARNING:
            logger.warning(msg)
        else:
            logger.info(msg)

    def _dispatch_console(self, alert: Alert):
        severity_colors = {
            AlertSeverity.INFO: "",
            AlertSeverity.WARNING: "\033[33m",
            AlertSeverity.ERROR: "\033[31m",
            AlertSeverity.CRITICAL: "\033[31m\033[1m",
        }
        reset = "\033[0m"
        color = severity_colors.get(alert.severity, "")
        print(f"{color}[{alert.severity.value.upper()}] {alert.title}: {alert.message}{reset}")

    def _dispatch_file(self, alert: Alert):
        alert_log = self.log_dir / "pipeline_alerts.jsonl"
        with open(alert_log, "a", encoding="utf-8") as f:
            f.write(json.dumps(alert.to_dict(), default=str) + "\n")

    def _dispatch_webhook(self, alert: Alert):
        """Send alert to webhook URL (Slack, Discord, Teams, etc.)."""
        try:
            import urllib.request
            payload = json.dumps({
                "text": f"[{alert.severity.value.upper()}] {alert.title}",
                "attachments": [{
                    "color": self._severity_color(alert.severity),
                    "fields": [
                        {"title": "Message", "value": alert.message, "short": False},
                        {"title": "Stage", "value": alert.pipeline_stage, "short": True},
                        {"title": "Source", "value": alert.source, "short": True},
                        {"title": "Time", "value": alert.timestamp.isoformat(), "short": True},
                    ],
                }],
            }).encode("utf-8")

            req = urllib.request.Request(
                self.webhook_url,
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                logger.debug("Webhook alert sent: %s", resp.status)
        except Exception as e:
            logger.warning("Failed to send webhook alert: %s", e)

    @staticmethod
    def _severity_color(severity: AlertSeverity) -> str:
        return {
            AlertSeverity.INFO: "#2196F3",
            AlertSeverity.WARNING: "#FF9800",
            AlertSeverity.ERROR: "#F44336",
            AlertSeverity.CRITICAL: "#B71C1C",
        }.get(severity, "#9E9E9E")

    def get_alerts(self, severity: Optional[AlertSeverity] = None) -> List[Alert]:
        """Get all alerts, optionally filtered by severity."""
        if severity:
            return [a for a in self._alerts if a.severity == severity]
        return list(self._alerts)

    def get_summary(self) -> Dict[str, Any]:
        """Get alert summary."""
        by_severity = {}
        for alert in self._alerts:
            key = alert.severity.value
            by_severity[key] = by_severity.get(key, 0) + 1
        return {
            "total": len(self._alerts),
            "by_severity": by_severity,
            "alerts_this_run": self._alerts_this_run,
            "latest": self._alerts[-1].to_dict() if self._alerts else None,
        }

    def export_report(self, output_path: Optional[str] = None) -> str:
        """Export alert report to JSON."""
        path = output_path or str(self.log_dir / "pipeline_alert_report.json")
        report = {
            "generated_at": datetime.now().isoformat(),
            "summary": self.get_summary(),
            "alerts": [a.to_dict() for a in self._alerts],
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, default=str)
        return path

    def reset_run_counter(self):
        """Reset the per-run alert counter."""
        self._alerts_this_run = 0


def create_alert_manager_from_env() -> AlertManager:
    """Create AlertManager from environment variables."""
    return AlertManager(
        log_dir=os.getenv("LOG_DIR", "logs"),
        webhook_url=os.getenv("ALERT_WEBHOOK_URL"),
        email_recipients=[
            r.strip()
            for r in os.getenv("ALERT_EMAIL_RECIPIENTS", "").split(",")
            if r.strip()
        ] or None,
        cooldown_seconds=int(os.getenv("ALERT_COOLDOWN_SECONDS", "300")),
        max_alerts_per_run=int(os.getenv("ALERT_MAX_PER_RUN", "50")),
    )


class SLATracker:
    """Tracks pipeline SLA compliance and triggers alerts on violations.

    Monitors:
    - Pipeline start time vs expected schedule
    - Stage completion deadlines
    - Total pipeline duration limits
    """

    def __init__(
        self,
        alert_manager: AlertManager,
        max_duration_minutes: int = 60,
        stage_deadlines: Optional[Dict[str, int]] = None,
        expected_start_time: Optional[str] = None,
    ):
        self.alert_manager = alert_manager
        self.max_duration_minutes = max_duration_minutes
        self.stage_deadlines = stage_deadlines or {
            "bronze": 15,
            "silver": 15,
            "dbt_gold": 15,
            "kpi_calculator": 10,
            "great_expectations": 5,
        }
        self.expected_start_time = expected_start_time
        self.start_time: Optional[datetime] = None
        self.stage_start_times: Dict[str, datetime] = {}
        self.stage_end_times: Dict[str, datetime] = {}

    def start_pipeline(self) -> None:
        """Record pipeline start time."""
        self.start_time = datetime.now()
        self.alert_manager.info(
            "Pipeline Started",
            f"Pipeline execution started at {self.start_time.strftime('%H:%M:%S')}",
            pipeline_stage="sla",
        )

    def start_stage(self, stage_name: str) -> None:
        """Record stage start time."""
        self.stage_start_times[stage_name] = datetime.now()

    def end_stage(self, stage_name: str, success: bool = True) -> None:
        """Record stage end time and check deadline."""
        self.stage_end_times[stage_name] = datetime.now()
        deadline_minutes = self.stage_deadlines.get(stage_name, 15)

        if self.start_time:
            elapsed = (self.stage_end_times[stage_name] - self.start_time).total_seconds() / 60
            if elapsed > deadline_minutes:
                self.alert_manager.warning(
                    "Stage SLA Exceeded",
                    f"Stage '{stage_name}' took {elapsed:.1f}min (SLA: {deadline_minutes}min)",
                    pipeline_stage="sla",
                    metadata={"stage": stage_name, "elapsed_min": round(elapsed, 1), "sla_min": deadline_minutes},
                )
            else:
                self.alert_manager.info(
                    "Stage SLA Met",
                    f"Stage '{stage_name}' completed in {elapsed:.1f}min (SLA: {deadline_minutes}min)",
                    pipeline_stage="sla",
                )

    def check_total_duration(self) -> bool:
        """Check if total pipeline duration exceeds SLA.

        Returns:
            True if SLA is met, False if violated.
        """
        if not self.start_time:
            return True

        elapsed = (datetime.now() - self.start_time).total_seconds() / 60
        if elapsed > self.max_duration_minutes:
            self.alert_manager.critical(
                "Pipeline SLA Violated",
                f"Pipeline running for {elapsed:.1f}min (SLA: {self.max_duration_minutes}min)",
                pipeline_stage="sla",
                metadata={"elapsed_min": round(elapsed, 1), "sla_min": self.max_duration_minutes},
            )
            return False
        return True

    def get_sla_report(self) -> Dict[str, Any]:
        """Generate SLA compliance report."""
        report = {
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "max_duration_minutes": self.max_duration_minutes,
            "stages": {},
            "sla_met": True,
        }

        if self.start_time:
            total_elapsed = (datetime.now() - self.start_time).total_seconds() / 60
            report["total_elapsed_minutes"] = round(total_elapsed, 1)
            if total_elapsed > self.max_duration_minutes:
                report["sla_met"] = False

        for stage in self.stage_deadlines:
            stage_info = {"sla_minutes": self.stage_deadlines[stage]}
            if stage in self.stage_start_times:
                stage_info["started_at"] = self.stage_start_times[stage].isoformat()
            if stage in self.stage_end_times:
                stage_info["ended_at"] = self.stage_end_times[stage].isoformat()
                if stage in self.stage_start_times:
                    elapsed = (self.stage_end_times[stage] - self.stage_start_times[stage]).total_seconds() / 60
                    stage_info["elapsed_minutes"] = round(elapsed, 1)
                    stage_info["sla_met"] = elapsed <= self.stage_deadlines[stage]
                    if not stage_info["sla_met"]:
                        report["sla_met"] = False
            report["stages"][stage] = stage_info

        return report
