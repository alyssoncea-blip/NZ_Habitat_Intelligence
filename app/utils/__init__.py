"""
Application utilities
Data loading, processing, and configuration
"""

from .data_loader import load_kpis_for_dashboard
from .kpi_processor import process_kpis_for_visualization
from .style_config import COLORS, FONTS, STYLES, get_kpi_color
from .quality_indicators import (
    get_data_quality_score,
    get_data_quality_score_legacy,
    show_data_source_info,
)

__all__ = [
    "load_kpis_for_dashboard",
    "process_kpis_for_visualization",
    "COLORS",
    "FONTS",
    "STYLES",
    "get_kpi_color",
    "get_data_quality_score",
    "get_data_quality_score_legacy",
    "show_data_source_info",
]
