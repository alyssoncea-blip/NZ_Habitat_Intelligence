"""Logging system for the dashboard."""

import logging
import sys
from datetime import datetime
import os

# Create logs directory if it doesn't exist
log_dir = os.path.join(os.path.dirname(__file__), "..", "..", "logs")
os.makedirs(log_dir, exist_ok=True)


def setup_logger(name, level=logging.INFO):
    """
    Configure a custom logger.

    Args:
        name: Logger name (typically __name__)
        level: Logging level

    Returns:
        Configured logging.Logger
    """
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Remove existing handlers to avoid duplication
    logger.handlers.clear()

    # Log format
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler (always shows)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler (warnings and errors only)
    log_file = os.path.join(
        log_dir, f"dashboard_{datetime.now().strftime('%Y%m%d')}.log"
    )
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.WARNING)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger


# Main loggers
dashboard_logger = setup_logger("dashboard", logging.INFO)
data_logger = setup_logger("dashboard.data", logging.INFO)
ui_logger = setup_logger("dashboard.ui", logging.INFO)


# Convenience function for general use
def get_logger(name):
    """Return a configured logger."""
    return setup_logger(name, logging.INFO)


class DashboardLogManager:
    """Dashboard log manager with extra functionality."""

    def __init__(self, component_name):
        self.logger = get_logger(component_name)
        self.component = component_name
        self.start_time = datetime.now()

    def log_component_start(self, description=""):
        """Log component start."""
        self.logger.info(f"[{self.component}] Starting {description}")

    def log_component_end(self, success=True, message=""):
        """Log component completion."""
        duration = (datetime.now() - self.start_time).total_seconds()
        status = "SUCCESS" if success else "FAILED"
        self.logger.info(
            f"[{self.component}] Completed [{status}] ({duration:.2f}s) {message}"
        )

    def log_data_load(self, data_source, record_count):
        """Log data loading."""
        self.logger.info(
            f"[{self.component}] Data loaded: {data_source} ({record_count} records)"
        )

    def log_kpi_processed(self, kpi_count, dashboard_name):
        """Log KPI processing."""
        self.logger.info(
            f"[{self.component}] KPIs processed: {kpi_count} for {dashboard_name}"
        )

    def log_error(self, error_type, details):
        """Log structured error."""
        self.logger.error(f"[{self.component}] ERROR [{error_type}] {details}")

    def log_warning(self, warning_type, details):
        """Log structured warning."""
        self.logger.warning(f"[{self.component}] WARNING [{warning_type}] {details}")

    def log_performance(self, operation, duration_ms):
        """Log performance metrics."""
        if duration_ms > 1000:
            self.logger.warning(
                f"[{self.component}] PERFORMANCE: {operation} took {duration_ms:.0f}ms (slow)"
            )
        else:
            self.logger.debug(
                f"[{self.component}] PERFORMANCE: {operation} took {duration_ms:.0f}ms"
            )


# Utility for user interaction logging
def log_user_interaction(component, action, details=None):
    """Log user interactions."""
    ui_logger.info(f"USER_INTERACTION: {component} - {action} - {details or ''}")


# Utility for logging data operations
def log_data_operation(operation, data_source, result=None, error=None):
    """Log data operations."""
    if error:
        data_logger.error(f"DATA_OP [{operation}] - {data_source} - ERROR: {error}")
    else:
        success_msg = f" - Result: {result}" if result else ""
        data_logger.info(f"DATA_OP [{operation}] - {data_source}{success_msg}")


# Backward compatibility aliases
DashboardLogManager.log_error_legacy = DashboardLogManager.log_error
