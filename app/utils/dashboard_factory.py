"""
Dashboard Factory - Shared utilities for creating premium dashboards.
Consolidates duplicated dashboard logic across tourism, macro, affordability, and forecast pages.
"""

from typing import Dict, List, Optional, Any

import dash_bootstrap_components as dbc
from dash import html

from ..components.cards import HeroKPICard, PremiumCard, create_dashboard_stats
from ..components.layout import create_section_header
from ..utils.logger import get_logger

logger = get_logger(__name__)


DEFAULT_PREFERRED_TERMS = {
    "affordability": ["affordability", "price", "income", "ratio", "rent", "burden", "cost"],
    "forecast": ["forecast", "risk", "volatility", "confidence", "scenario", "outlook", "uncertainty"],
    "tourism": ["tourism", "visitor", "accommodation", "seasonal", "growth"],
    "macro": ["gdp", "inflation", "unemployment", "interest", "rate", "economic"],
}


def create_hero_section(hero_kpi: Optional[Dict], title: str, description: str) -> html.Div:
    """Create hero section for dashboard."""
    if not hero_kpi:
        return HeroKPICard.create(
            title=title,
            value="N/A",
            unit="",
            description=f"No {description.lower()} hero KPI found in dataset",
            status="Unavailable",
            color="#2E86AB",
        )

    return HeroKPICard.create(
        title=hero_kpi.get("name", title),
        value=hero_kpi.get("value", "N/A"),
        unit=hero_kpi.get("unit", ""),
        description=hero_kpi.get("description", f"{description} indicator"),
        status=hero_kpi.get("status", "Monitoring"),
        color=hero_kpi.get("color", "#2E86AB"),
        confidence=hero_kpi.get("confidence"),
    )


def create_stats_section(
    kpis_df,
    preferred_terms: Optional[List[str]] = None,
    max_stats: int = 4
) -> html.Div:
    """
    Create stats section for dashboard using preferred search terms.

    Args:
        kpis_df: DataFrame of processed KPIs
        preferred_terms: List of terms to prioritize in stats
        max_stats: Maximum number of stats to display

    Returns:
        HTML Div with dashboard stats
    """
    if kpis_df.empty:
        return html.Div()

    if preferred_terms is None:
        preferred_terms = []

    stats_data = []

    for _, kpi in kpis_df.iterrows():
        name = str(kpi.get("name", ""))
        if len(stats_data) >= max_stats:
            break
        if any(term in name.lower() for term in preferred_terms):
            stats_data.append({
                "title": (name[:20] + "..." if len(name) > 20 else name),
                "value": kpi.get("value", "N/A"),
                "unit": kpi.get("unit", ""),
                "trend": kpi.get("trend", "neutral"),
            })

    if not stats_data:
        for _, kpi in kpis_df.head(max_stats).iterrows():
            name = str(kpi.get("name", "KPI"))
            stats_data.append({
                "title": (name[:20] + "..." if len(name) > 20 else name),
                "value": kpi.get("value", "N/A"),
                "unit": kpi.get("unit", ""),
                "trend": kpi.get("trend", "neutral"),
            })

    return create_dashboard_stats(stats_data)


def create_kpi_grid(kpis_df, empty_message: str = "No KPIs available") -> dbc.Row:
    """
    Create KPI grid for dashboard.

    Args:
        kpis_df: DataFrame of processed KPIs
        empty_message: Message to display when no KPIs available

    Returns:
        dbc.Row with KPI cards
    """
    if kpis_df.empty:
        return dbc.Alert(empty_message, color="warning")

    cards = []
    for _, kpi in kpis_df.iterrows():
        cards.append(
            dbc.Col(
                PremiumCard.create_kpi_card(kpi),
                width=12, md=6, lg=4,
                className="mb-3"
            )
        )

    return dbc.Row(cards)


def create_insights_section(
    kpis_df,
    max_insights: int = 5,
    prefix: str = "KPI"
) -> List[dbc.Card]:
    """
    Create insights section for dashboard.

    Args:
        kpis_df: DataFrame of processed KPIs
        max_insights: Maximum number of insights to display
        prefix: Prefix for insight titles

    Returns:
        List of insight cards
    """
    insights = []

    for _, kpi in kpis_df.head(max_insights).iterrows():
        name = kpi.get("name", prefix)
        value = kpi.get("display_value", kpi.get("value", "N/A"))
        status = kpi.get("status", "Monitoring")
        color = kpi.get("color", "#6c757d")

        insights.append(
            dbc.Card(
                dbc.CardBody([
                    html.H6(name, className="card-title"),
                    html.P(value, className="card-value mb-1"),
                    dbc.Badge(status, color=color.replace("#", "")),
                ]),
                className="mb-2",
            )
        )

    return insights


def find_hero_kpi(
    kpis_df,
    preferred_terms: Optional[List[str]] = None,
    default_title: str = "Conditions"
) -> Optional[Dict]:
    """
    Find hero KPI from processed KPIs based on preferred search terms.

    Args:
        kpis_df: DataFrame of processed KPIs
        preferred_terms: List of terms to search for in KPI names
        default_title: Default title if no hero KPI found

    Returns:
        Hero KPI dict or None
    """
    if kpis_df.empty:
        return None

    if preferred_terms is None:
        preferred_terms = []

    for _, kpi in kpis_df.iterrows():
        name = str(kpi.get("name", "")).lower()
        if any(term in name for term in preferred_terms):
            return kpi.to_dict() if hasattr(kpi, 'to_dict') else dict(kpi)

    return kpis_df.iloc[0].to_dict() if len(kpis_df) > 0 else None


class DashboardFactory:
    """
    Factory class for creating premium dashboards.
    Consolidates common dashboard creation patterns.
    """

    def __init__(
        self,
        dashboard_name: str,
        title: str,
        subtitle: str,
        hero_terms: Optional[List[str]] = None,
        stats_terms: Optional[List[str]] = None,
    ):
        """
        Initialize DashboardFactory.

        Args:
            dashboard_name: Name of dashboard (used for data loading)
            title: Dashboard title
            subtitle: Dashboard subtitle
            hero_terms: Terms to search for hero KPI
            stats_terms: Terms to prioritize in stats section
        """
        self.dashboard_name = dashboard_name
        self.title = title
        self.subtitle = subtitle
        self.hero_terms = hero_terms or DEFAULT_PREFERRED_TERMS.get(dashboard_name, [])
        self.stats_terms = stats_terms or DEFAULT_PREFERRED_TERMS.get(dashboard_name, [])

    def create_dashboard(
        self,
        kpis_df,
        include_kpi_grid: bool = True,
        include_insights: bool = True,
        insights_count: int = 5,
    ) -> dbc.Container:
        """
        Create complete dashboard container.

        Args:
            kpis_df: DataFrame of processed KPIs
            include_kpi_grid: Whether to include KPI grid
            include_insights: Whether to include insights section
            insights_count: Number of insights to show

        Returns:
            dbc.Container with full dashboard
        """
        hero_kpi = find_hero_kpi(kpis_df, self.hero_terms, self.title)

        children = [
            create_section_header(self.title, self.subtitle),
            html.Div(create_hero_section(hero_kpi, self.title, self.subtitle), id=f"{self.dashboard_name}-hero"),
            html.Div(
                create_stats_section(kpis_df, self.stats_terms),
                id=f"{self.dashboard_name}-stats"
            ),
        ]

        if include_kpi_grid:
            children.append(
                html.Div(
                    create_kpi_grid(kpis_df, f"No {self.dashboard_name} KPIs available"),
                    id=f"{self.dashboard_name}-kpi-grid"
                )
            )

        if include_insights:
            children.append(
                html.Div(
                    create_insights_section(kpis_df, insights_count, self.title.title()),
                    id=f"{self.dashboard_name}-insights"
                )
            )

        children.append(
            dcc.Store(
                id=f"{self.dashboard_name}-kpis-data",
                data=kpis_df.to_dict("records") if not kpis_df.empty else []
            )
        )

        return dbc.Container(
            fluid=True,
            className=f"{self.dashboard_name}-dashboard",
            children=children,
        )


from dash import dcc