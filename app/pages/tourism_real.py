"""
Tourism Dashboard Premium - Implementation Real
Análise do impacto do tourism no mercado housing
"""

import dash_bootstrap_components as dbc
from dash import html, dcc
import pandas as pd
from ..components.cards import PremiumCard, HeroKPICard, create_dashboard_stats
from ..components.layout import create_section_header
from ..utils.data_loader import load_kpis_for_dashboard
from ..utils.kpi_processor import process_kpis_for_visualization
from ..utils.quality_indicators import show_data_source_info
from ..utils.logger import get_logger

logger = get_logger(__name__)


def _ensure_df(kpis_data):
    """Convert dict/list input to DataFrame if needed."""
    if kpis_data is None:
        return pd.DataFrame()
    if isinstance(kpis_data, pd.DataFrame):
        return kpis_data
    if isinstance(kpis_data, dict):
        kpi_list = kpis_data.get("kpis", [])
        return pd.DataFrame(kpi_list) if kpi_list else pd.DataFrame()
    if isinstance(kpis_data, list):
        return pd.DataFrame(kpis_data) if kpis_data else pd.DataFrame()
    return pd.DataFrame()


def create_tourism_dashboard():
    """
    Create premium tourism dashboard with real data

    Returns:
        Componente Dash com layout do tourism dashboard
    """
    logger.info("Creating tourism dashboard premium")

    # Load data
    kpis_df = _ensure_df(load_kpis_for_dashboard("tourism"))

    if kpis_df.empty:
        logger.error("Could not load tourism KPIs")
        return create_error_state("Tourism data is not available")

    logger.info(f"KPIs de tourism carregados: {len(kpis_df)} registros")

    # Process KPIs for visualization
    processed_kpis = process_kpis_for_visualization(kpis_df)

    # Encontra KPI hero
    hero_kpi = find_tourism_hero_kpi(processed_kpis)

    # Create dashboard layout
    return dbc.Container(
        fluid=True,
        className="tourism-dashboard",
        children=[
            # Header
            create_section_header(
                "Tourism Impact Dashboard",
                "Premium Edition • Tourism-Housing Market Analysis",
            ),
            # Quality info
            show_data_source_info("tourism"),
            # Hero section
            html.Div(id="tourism-hero", children=create_tourism_hero_section(hero_kpi)),
            # Quick statistics
            html.Div(id="tourism-stats", children=create_tourism_stats(processed_kpis)),
            # KPI grid
            html.Div(
                id="tourism-kpi-grid", children=create_tourism_kpi_grid(processed_kpis)
            ),
            # Impact analysis
            html.Div(id="impact-analysis", children=create_impact_analysis_section()),
            # Insights
            html.Div(
                id="tourism-insights", children=create_tourism_insights(processed_kpis)
            ),
            # Callbacks
            dcc.Store(
                id="tourism-kpis-data",
                data=processed_kpis.get("kpis", [])
                if isinstance(processed_kpis, dict)
                else processed_kpis.to_dict("records"),
            ),
            dcc.Store(
                id="tourism-filter-state", data={"timeframe": "12M", "region": "All"}
            ),
        ],
    )


def create_tourism_hero_section(hero_kpi):
    """Create hero section for tourism dashboard"""
    if not hero_kpi:
        return HeroKPICard.create(
            title="Tourism Impact Analysis",
            value="Active",
            unit="",
            description="Monitoring tourism's impact on housing market",
            status="Analyzing",
            color="#2E86AB",
        )

    return HeroKPICard.create(
        title=hero_kpi.get("name", "Tourism Impact"),
        value=hero_kpi.get("value", "N/A"),
        unit=hero_kpi.get("unit", ""),
        description=hero_kpi.get("description", "Tourism market impact indicator"),
        status=hero_kpi.get("status", "Active"),
        color=hero_kpi.get("color", "#2E86AB"),
    )


def create_tourism_stats(kpis_df):
    """Create quick tourism statistics"""
    kpis_df = _ensure_df(kpis_df)
    if kpis_df.empty:
        return html.Div()

    stats_data = []

    for _, kpi in kpis_df.iterrows():
        kpi_name = kpi["name"]
        kpi_value = kpi.get("value", 0)
        kpi_unit = kpi.get("unit", "")

        # Seleciona KPIs importantes
        if len(stats_data) < 4:
            stats_data.append(
                {
                    "title": kpi_name[:18] + "..." if len(kpi_name) > 18 else kpi_name,
                    "value": round(float(kpi_value), 1)
                    if isinstance(kpi_value, (int, float))
                    else kpi_value,
                    "unit": kpi_unit,
                    "trend": kpi.get("trend", "neutral"),
                }
            )

    return create_dashboard_stats(stats_data)


def create_tourism_kpi_grid(kpis_df):
    """Create tourism KPI grid."""
    kpis_df = _ensure_df(kpis_df)
    if kpis_df.empty:
        return html.Div("No tourism KPIs available", className="alert alert-warning")

    # Categoriza KPIs
    categorized = categorize_tourism_kpis(kpis_df)

    rows = []

    for category, kpis in categorized.items():
        if not kpis:
            continue

        # Category header
        rows.append(
            dbc.Row(
                [dbc.Col([html.H4(category, className="category-title")], width=12)],
                className="category-row",
            )
        )

        # Cards da category
        category_cards = []
        for kpi in kpis:
            card = PremiumCard.create_kpi_card(kpi)
            category_cards.append(
                dbc.Col(card, width=6, lg=4, className="kpi-card-col")
            )

        rows.append(dbc.Row(category_cards, className="kpi-grid-row"))

    return rows


def create_impact_analysis_section():
    """Create impact analysis section"""
    return dbc.Card(
        [
            dbc.CardHeader([html.H5("Impact Analysis", className="analysis-title")]),
            dbc.CardBody(
                [
                    html.P(
                        "Tourism impact analysis on housing market indicators.",
                        className="text-muted",
                    ),
                    html.Small(
                        "Future enhancement: Detailed correlation analysis between tourism metrics and housing market performance.",
                        className="text-muted d-block mt-2",
                    ),
                ]
            ),
        ],
        className="analysis-card",
    )


def create_tourism_insights(kpis_df):
    """Create tourism insights."""
    kpis_df = _ensure_df(kpis_df)
    insights = []

    if not kpis_df.empty:
        insights.append("Tourism impact indicators loaded for analysis.")
        insights.append("Monitor seasonal patterns and short-term rental penetration.")

    return dbc.Card(
        [
            dbc.CardHeader([html.H5("Tourism Insights", className="insights-title")]),
            dbc.CardBody(
                [
                    html.Ul(
                        [html.Li(insight) for insight in insights[:3]],
                        className="insights-list",
                    ),
                    html.P(
                        "Seasonal analysis recommended for tourism-dependent regions.",
                        className="insights-note",
                    ),
                ]
            ),
        ],
        className="insights-card",
    )


def find_tourism_hero_kpi(kpis_df):
    """Encontra KPI hero para tourism dashboard"""
    kpis_df = _ensure_df(kpis_df)
    if kpis_df.empty:
        return None

    # Prioridade: Tourism Pressure Index
    pressure_kpis = kpis_df[kpis_df["name"].str.contains("Pressure", case=False)]
    if not pressure_kpis.empty:
        return pressure_kpis.iloc[0].to_dict()

    # Prioridade: Tourism indicators
    tourism_kpis = kpis_df[kpis_df["name"].str.contains("Tourism", case=False)]
    if not tourism_kpis.empty:
        return tourism_kpis.iloc[0].to_dict()

    # Fallback
    return kpis_df.iloc[0].to_dict() if not kpis_df.empty else None


def categorize_tourism_kpis(kpis_df):
    """Categoriza KPIs de tourism"""
    kpis_df = _ensure_df(kpis_df)
    if kpis_df.empty:
        return {}
    categories = {
        "Pressure & Impact": [],
        "Market Penetration": [],
        "Seasonality": [],
        "Other Indicators": [],
    }

    for _, kpi in kpis_df.iterrows():
        kpi_name = kpi["name"].lower()

        if any(term in kpi_name for term in ["pressure", "impact", "correlation"]):
            categories["Pressure & Impact"].append(kpi)
        elif any(
            term in kpi_name for term in ["penetration", "share", "rental", "airbnb"]
        ):
            categories["Market Penetration"].append(kpi)
        elif any(term in kpi_name for term in ["seasonality", "seasonal", "visitor"]):
            categories["Seasonality"].append(kpi)
        else:
            categories["Other Indicators"].append(kpi)

    # Remove empty categories
    return {k: v for k, v in categories.items() if v}


def create_error_state(message):
    """Create error state."""
    return dbc.Container(
        [
            dbc.Alert(
                [
                    html.H4("Tourism Dashboard Error", className="alert-heading"),
                    html.P(message),
                    html.Hr(),
                    html.P("Tourism impact analysis requires tourism-specific data."),
                ],
                color="warning",
            ),
            dbc.Button(
                "Go to Executive Dashboard", href="/", color="primary", className="mt-3"
            ),
        ]
    )
