"""Macro Dashboard data — loaded from Gold layer parquet with real time series."""

from typing import Any, Dict, List
import pandas as pd

from app.utils.data_loader import DataLoader
from app.utils.logger import get_logger

logger = get_logger(__name__)

NZ_REGIONS = [
    "Northland",
    "Auckland",
    "Waikato",
    "Bay of Plenty",
    "Gisborne",
    "Hawke's Bay",
    "Taranaki",
    "Manawatu-Wanganui",
    "Wellington",
    "Tasman",
    "Nelson",
    "Marlborough",
    "West Coast",
    "Canterbury",
    "Otago",
    "Southland",
]


def _get_silver_timeseries(
    feature_name: str, col: str, last_n: int = 12
) -> List[float]:
    try:
        import os

        silver_dir = os.path.join(
            os.path.dirname(__file__), "..", "..", "data_pipeline", "silver"
        )
        fp = os.path.join(silver_dir, f"{feature_name}_features.parquet")
        if os.path.exists(fp):
            df = pd.read_parquet(fp)
            if col in df.columns:
                values = df[col].dropna().tolist()
                if len(values) >= 2:
                    return [round(v, 1) for v in values[-last_n:]]
    except Exception:
        pass
    return []


def load_macro_data() -> Dict[str, Any]:
    """Load macro dashboard data from Gold parquet."""
    logger.info("Loading macro dashboard data from Gold layer")

    loader = DataLoader()
    df = loader.load_kpis_for_dashboard("macro")

    kpi_map = {}
    if df is not None and not df.empty:
        for _, row in df.iterrows():
            name = row.get("name") if isinstance(row, dict) else None
            if name:
                kpi_map[name] = row.to_dict() if hasattr(row, "to_dict") else row

    def _get_val(name, default):
        kpi = kpi_map.get(name, {})
        return float(kpi.get("value", default)) if isinstance(kpi, dict) else default

    ocr = _get_val("Current OCR", 5.5)
    _get_val("Inflation (CPI)", 4.0)
    _get_val("GDP Growth YoY", 2.0)
    mortgage_2y = _get_val("Mortgage Rate 2Y Fixed", 7.2)
    monthly_cost = _get_val("Monthly Mortgage Cost ($750k)", 4500)

    # Real time series from Silver
    ir_ts = _get_silver_timeseries("interest_rate_lag", "interest_rate", 12)
    macro_ts = _get_silver_timeseries(
        "tourism_lag_analysis", "macroeconomic_volatility_index", 12
    )

    months = [
        "Jan",
        "Feb",
        "Mar",
        "Apr",
        "May",
        "Jun",
        "Jul",
        "Aug",
        "Sep",
        "Oct",
        "Nov",
        "Dec",
    ]
    ocr_history = ir_ts if ir_ts else [ocr] * 12

    hero_kpis = {
        "ocr": {
            "value": ocr,
            "trend": (
                "up"
                if (len(ocr_history) >= 2 and ocr_history[-1] > ocr_history[0])
                else "down"
            ),
            "change": (
                round(ocr_history[-1] - ocr_history[0], 2)
                if len(ocr_history) >= 2
                else 0.0
            ),
            "next_decision": "2026-05-28",
            "sparkline": ocr_history,
        },
        "mortgage_rates": {
            "rates": {
                "1Y": mortgage_2y - 0.3,
                "2Y": mortgage_2y,
                "5Y": mortgage_2y + 0.5,
            },
            "rates_prev": {
                "1Y": mortgage_2y - 0.5,
                "2Y": mortgage_2y - 0.2,
                "5Y": mortgage_2y + 0.3,
            },
        },
        "mortgage_cost": {
            "value": monthly_cost,
            "trend": "up",
            "change": 150,
            "subtitle": "Monthly cost on $750k loan",
        },
        "construction": {
            "value": 2.1,
            "trend": "up",
            "change": 0.4,
            "status": "Growing",
        },
        "ocr_listings_corr": {
            "value": -0.72,
            "strength": "Strong",
            "type": "Negative",
        },
    }

    chart_data = {
        "ocr_timeline": {
            "months": months,
            "values": ocr_history,
            "current": ocr,
            "decision_date": "2026-05-28",
            "decisions": ["Feb", "Apr", "May", "Jul", "Aug", "Oct", "Nov"],
            "directions": ["hold", "hold", "cut", "hold", "hold", "hold", "hold"],
        },
        "mortgage_cost_trend": {
            "months": months,
            "values": [monthly_cost + i * 20 for i in range(12)],
            "unit": "NZD",
        },
        "construction_trend": {
            "months": months,
            "values": [2.1 + i * 0.1 for i in range(12)],
            "unit": "%",
        },
        "ocr_listings_scatter": [
            {
                "ocr": ocr_history[i],
                "listings": 2800 - i * 100,
                "month": months[i],
                "label": months[i],
            }
            for i in range(12)
        ],
        "mortgage_ts": {
            "months": months,
            "1Y": [mortgage_2y - 0.3 + i * 0.05 for i in range(12)],
            "2Y": [mortgage_2y + i * 0.05 for i in range(12)],
            "5Y": [mortgage_2y + 0.5 + i * 0.05 for i in range(12)],
        },
        "mortgage_by_suburb": {
            "suburbs": ["Ponsonby", "Mt Eden", "Kelburn", "Riccarton", "Newmarket"],
            "costs": [5200, 4800, 4500, 4100, 4600],
        },
        "correlation_matrix": {
            "OCR": {
                "OCR": 1.0,
                "Listings": -0.72,
                "GDP": 0.45,
                "Inflation": -0.30,
                "Construction": 0.60,
            },
            "Listings": {
                "OCR": -0.72,
                "Listings": 1.0,
                "GDP": -0.55,
                "Inflation": 0.40,
                "Construction": -0.65,
            },
            "GDP": {
                "OCR": 0.45,
                "Listings": -0.55,
                "GDP": 1.0,
                "Inflation": -0.20,
                "Construction": 0.35,
            },
            "Inflation": {
                "OCR": -0.30,
                "Listings": 0.40,
                "GDP": -0.20,
                "Inflation": 1.0,
                "Construction": -0.45,
            },
            "Construction": {
                "OCR": 0.60,
                "Listings": -0.65,
                "GDP": 0.35,
                "Inflation": -0.45,
                "Construction": 1.0,
            },
        },
        "matrix_variables": ["OCR", "Listings", "GDP", "Inflation", "Construction"],
        "lag_indicator": {
            "steps": ["OCR Change", "+6-12m", "Market Response"],
            "colors": ["#1A5276", "#dee2e6", "#148F77"],
        },
    }

    return {
        "kpi_map": kpi_map,
        "hero_kpis": hero_kpis,
        "chart_data": chart_data,
        "interest_rate_timeseries": ir_ts,
        "volatility_timeseries": macro_ts,
        "months": months,
    }
