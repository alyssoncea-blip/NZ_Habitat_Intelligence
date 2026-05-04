"""
Dashboard filter utilities — centralized time and region filtering.

All dashboards use these helpers to filter data by timeframe (3M, 6M, 12M, 1Y, 5Y)
and region. Ensures consistent behavior across all 6 dashboard pages.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import pandas as pd

TIMEFRAME_MONTHS = {
    "3M": 3,
    "6M": 6,
    "12M": 12,
    "1Y": 12,
    "5Y": 60,
}


def filter_timeseries_by_months(
    months: List[str],
    values: List[float],
    timeframe: str = "12M",
) -> Dict[str, List]:
    """
    Trim time series data to the selected timeframe.

    Args:
        months: List of month labels (e.g. ["Jan", "Feb", ...])
        values: List of numeric values aligned with months
        timeframe: One of "3M", "6M", "12M", "1Y", "5Y"

    Returns:
        Dict with filtered "months" and "values" lists.
    """
    n = TIMEFRAME_MONTHS.get(timeframe, 12)

    if len(months) == 0 or len(values) == 0:
        return {"months": [], "values": []}

    last_n = min(n, len(months))
    return {
        "months": months[-last_n:],
        "values": values[-last_n:],
    }


def filter_dataframe_by_timeframe(
    df: pd.DataFrame,
    timeframe: str = "12M",
    date_col: str = "date",
) -> pd.DataFrame:
    """
    Filter a DataFrame to only include rows within the selected timeframe.

    Args:
        df: DataFrame with a date column
        timeframe: One of "3M", "6M", "12M", "1Y", "5Y"
        date_col: Name of the date column

    Returns:
        Filtered DataFrame
    """
    if df is None or df.empty:
        return df

    n_months = TIMEFRAME_MONTHS.get(timeframe, 12)
    cutoff = datetime.now() - timedelta(days=n_months * 30)

    if date_col not in df.columns:
        return df.tail(n_months)

    try:
        dates = pd.to_datetime(df[date_col])
        return df[dates >= cutoff].copy()
    except Exception:
        return df.tail(n_months)


def filter_regional_data(
    data: List[Dict[str, Any]],
    region: str = "All Regions",
    region_key: str = "region",
) -> List[Dict[str, Any]]:
    """
    Filter list of regional dicts by selected region.

    Args:
        data: List of dicts, each with a region key
        region: Region name or "All Regions"
        region_key: Key used for region name in each dict

    Returns:
        Filtered list
    """
    if region == "All Regions" or not region:
        return data
    return [d for d in data if d.get(region_key) == region]


def filter_sparkline(
    sparkline: Optional[List[float]],
    timeframe: str = "12M",
) -> Optional[List[float]]:
    """Trim a sparkline to the selected timeframe."""
    if not sparkline:
        return sparkline
    n = TIMEFRAME_MONTHS.get(timeframe, 12)
    return sparkline[-min(n, len(sparkline)) :]


def apply_filters_to_executive_data(
    data: Dict[str, Any],
    timeframe: str = "12M",
    region: str = "All Regions",
) -> Dict[str, Any]:
    """
    Apply time and region filters to executive dashboard data.

    Args:
        data: Full data dict from load_executive_data()
        timeframe: Time period filter
        region: Region filter

    Returns:
        Filtered data dict ready for chart rendering
    """
    filtered = {
        "hero_kpis": data.get("hero_kpis", {}),
        "regions": data.get("regions", []),
        "region_coords": data.get("region_coords", {}),
    }

    line_chart = data.get("line_chart", {})
    filtered_line = filter_timeseries_by_months(
        line_chart.get("months", []),
        line_chart.get("values", []),
        timeframe,
    )
    filtered["line_chart"] = {
        **line_chart,
        "months": filtered_line["months"],
        "values": filtered_line["values"],
    }

    dual_axis = data.get("dual_axis", {})
    filtered_dual_months = filter_timeseries_by_months(
        dual_axis.get("months", []),
        dual_axis.get("ocr", []),
        timeframe,
    )
    filtered_dual_pressure = filter_timeseries_by_months(
        dual_axis.get("months", []),
        dual_axis.get("pressure", []),
        timeframe,
    )
    filtered["dual_axis"] = {
        **dual_axis,
        "months": filtered_dual_months["months"],
        "ocr": filtered_dual_months["values"],
        "pressure": filtered_dual_pressure["values"],
    }

    scatter_data = data.get("scatter_data", [])
    filtered["scatter_data"] = filter_regional_data(scatter_data, region)

    hero = filtered["hero_kpis"]
    pressure_sparkline = hero.get("pressure_index", {}).get("sparkline")
    if pressure_sparkline:
        hero["pressure_index"]["sparkline"] = filter_sparkline(
            pressure_sparkline, timeframe
        )

    price_mom_sparkline = hero.get("price_mom", {}).get("sparkline")
    if price_mom_sparkline:
        hero["price_mom"]["sparkline"] = filter_sparkline(
            price_mom_sparkline, timeframe
        )

    if region != "All Regions":
        pressure_regions = hero.get("pressure_index", {}).get("regions", {})
        if region in pressure_regions:
            hero["pressure_index"]["value"] = pressure_regions[region]

        aff_regions = hero.get("affordability", {}).get("regions", {})
        if region in aff_regions:
            hero["affordability"]["value"] = aff_regions[region]

        mom_regions = hero.get("price_mom", {}).get("regions", {})
        if region in mom_regions:
            hero["price_mom"]["value"] = mom_regions[region]

    return filtered
