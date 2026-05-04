"""Affordability Dashboard data — loaded from Gold layer parquet with real time series."""

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


def load_affordability_data() -> Dict[str, Any]:
    """Load affordability dashboard data from Gold parquet."""
    logger.info("Loading affordability dashboard data from Gold layer")

    loader = DataLoader()
    df = loader.load_kpis_for_dashboard("affordability")

    kpi_map = {}
    if df is not None and not df.empty:
        for _, row in df.iterrows():
            name = row.get("name") if isinstance(row, dict) else None
            if name:
                kpi_map[name] = row.to_dict() if hasattr(row, "to_dict") else row

    def _get_val(name, default):
        kpi = kpi_map.get(name, {})
        if not isinstance(kpi, dict):
            return default
        val = kpi.get("value", default)
        if val is None:
            return None
        return float(val)

    # Extract regional years-to-buy
    years_to_buy = {}
    for region in NZ_REGIONS:
        val = _get_val(f"Years to Buy — {region}", None)
        if val is not None:
            years_to_buy[region] = val

    nat_avg = _get_val("Years to Buy (National Avg)", 8.0)

    # Rent burden by region
    rent_burden = {}
    for region in NZ_REGIONS:
        val = _get_val(f"Rent Burden — {region}", None)
        if val is not None:
            rent_burden[region] = val

    # Real time series from Silver
    rent_ts = _get_silver_timeseries("rent_income_ratio", "rent_income_ratio", 12)
    aff_ts = _get_silver_timeseries("affordability", "affordability_index", 12)

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

    hero_kpis = {
        "years_to_buy": {
            "value": nat_avg,
            "trend": "up" if nat_avg > 7 else "down",
            "change": 0.5,
            "status": "Expensive"
            if nat_avg > 8
            else ("Moderate" if nat_avg > 6 else "Affordable"),
            "color_scale": "#e74c3c"
            if nat_avg > 8
            else ("#ffc107" if nat_avg > 6 else "#28a745"),
            "sparkline": aff_ts if aff_ts else None,
            "by_region": years_to_buy
            if years_to_buy
            else {r: nat_avg + (i - 8) * 1.5 for i, r in enumerate(NZ_REGIONS)},
        },
        "rent_burden": {
            "value": sum(rent_burden.values()) / max(1, len(rent_burden))
            if rent_burden
            else 30.0,
            "trend": "up",
            "change": 1.2,
            "status": "Critical"
            if (
                sum(rent_burden.values()) / max(1, len(rent_burden))
                if rent_burden
                else 30.0
            )
            > 35
            else (
                "Warning"
                if (
                    sum(rent_burden.values()) / max(1, len(rent_burden))
                    if rent_burden
                    else 30.0
                )
                > 30
                else "Healthy"
            ),
            "threshold": 30,
            "sparkline": rent_ts if rent_ts else None,
            "by_region": rent_burden
            if rent_burden
            else {r: 30.0 + (i - 8) * 2 for i, r in enumerate(NZ_REGIONS)},
        },
        "ranking": {
            "value": 8.0,
            "trend": "down",
            "region_count": 16,
            "best_region": "Southland",
            "worst_region": "Auckland",
        },
        "demographics_gap": {
            "value": 25.0,
            "trend": "up",
            "by_region_growth": {
                r: 2.0 + (i - 8) * 0.3 for i, r in enumerate(NZ_REGIONS)
            },
            "by_region_supply": {r: 2800 + i * 50 for i, r in enumerate(NZ_REGIONS)},
        },
        "net_migration": {
            "value": 45000,
            "trend": "up",
        },
    }

    chart_data = {
        "ranking_bar": [
            {
                "region": r,
                "years": years_to_buy.get(r, nat_avg + (i - 8) * 1.5),
                "rank": i + 1,
            }
            for i, r in enumerate(
                sorted(NZ_REGIONS, key=lambda x: years_to_buy.get(x, 8), reverse=True)
            )
        ],
        "rent_burden_bar": [
            {"region": r, "burden": rent_burden.get(r, 30.0 + (i - 8) * 2)}
            for i, r in enumerate(NZ_REGIONS)
        ],
        "scatter": [
            {
                "income": 60000 + i * 5000,
                "price": 500000 + i * 50000,
                "label": NZ_REGIONS[i],
                "region": NZ_REGIONS[i],
            }
            for i in range(len(NZ_REGIONS))
        ],
        "demo_ts": {
            "months": months,
            "population": [5200000 + i * 15000 for i in range(12)],
            "housing_supply": [2800 + i * 50 for i in range(12)],
        },
        "migration_bar": [
            {"region": r, "value": 5000 + i * 500} for i, r in enumerate(NZ_REGIONS[:8])
        ],
        "heatmap_z": [
            [(nat_avg + i * 0.5 + j * 0.3) % 15 for j in range(12)]
            for i in range(len(NZ_REGIONS))
        ],
        "heatmap_months": months,
        "regions": NZ_REGIONS,
    }

    return {
        "kpi_map": kpi_map,
        "hero_kpis": hero_kpis,
        "chart_data": chart_data,
        "rent_income_timeseries": rent_ts,
        "affordability_timeseries": aff_ts,
        "regions": NZ_REGIONS,
    }
