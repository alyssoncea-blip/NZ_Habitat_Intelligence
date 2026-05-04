"""
Housing Dashboard - Power BI Style Refactored
Mercado Imobiliário: KPIs 07-12
Layout edge-to-edge com Hero KPIs, Gráficos e Heatmap
"""

import dash_bootstrap_components as dbc
from dash import html, dcc
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from ..components.cards import HousingKPICard
from ..components.layout import create_section_header
from ..data.housing_kpi_data import load_housing_data, SUBURBS_LIST, CITIES_LIST
from ..utils.logger import get_logger

logger = get_logger(__name__)


def create_housing_dashboard():
    """
    Create the Housing Dashboard in Power BI style.
    Layout:
    - Hero KPI Row (6 cards KPI 07-12) ~35-40%
    - Main Analytics (~35%) - Row 1: Boxplot + Line | Row 2: 3 charts
    - Supply & Demand (~25%) - Heatmap + Consent comparison
    """
    logger.info("Creating Power BI style housing dashboard")

    data = load_housing_data()
    hero_kpis = data["hero_kpis"]
    chart_data = data["chart_data"]

    return dbc.Container(
        [
            create_section_header(
                "Housing Market Dashboard",
                "Premium Edition • Market Mechanics & Supply-Demand Dynamics",
            ),
            _create_filter_bar(),
            html.Div(
                [
                    dbc.Row(
                        [
                            dbc.Col(
                                HousingKPICard.create_median_price_card(
                                    value=hero_kpis["median_price"]["value"],
                                    trend=hero_kpis["median_price"]["trend"],
                                    change=hero_kpis["median_price"]["change"],
                                    sparkline_data=hero_kpis["median_price"].get(
                                        "sparkline"
                                    ),
                                    subtitle=hero_kpis["median_price"]["subtitle"],
                                ),
                                width=12,
                                md=6,
                                lg=2,
                                className="mb-3",
                            ),
                            dbc.Col(
                                HousingKPICard.create_days_on_market_card(
                                    value=hero_kpis["days_on_market"]["value"],
                                    trend=hero_kpis["days_on_market"]["trend"],
                                    status=hero_kpis["days_on_market"]["status"],
                                    sparkline_data=hero_kpis["days_on_market"].get(
                                        "sparkline"
                                    ),
                                    subtitle=hero_kpis["days_on_market"]["subtitle"],
                                ),
                                width=12,
                                md=6,
                                lg=2,
                                className="mb-3",
                            ),
                            dbc.Col(
                                HousingKPICard.create_new_listings_card(
                                    value=hero_kpis["new_listings"]["value"],
                                    trend=hero_kpis["new_listings"]["trend"],
                                    change=hero_kpis["new_listings"]["change"],
                                    weekly_data=hero_kpis["new_listings"].get(
                                        "weekly_data"
                                    ),
                                    subtitle=hero_kpis["new_listings"]["subtitle"],
                                ),
                                width=12,
                                md=6,
                                lg=2,
                                className="mb-3",
                            ),
                            dbc.Col(
                                HousingKPICard.create_property_type_card(
                                    dominant_pct=hero_kpis["property_type"][
                                        "dominant_pct"
                                    ],
                                    breakdown=hero_kpis["property_type"]["breakdown"],
                                    subtitle=hero_kpis["property_type"]["subtitle"],
                                ),
                                width=12,
                                md=6,
                                lg=2,
                                className="mb-3",
                            ),
                            dbc.Col(
                                HousingKPICard.create_price_per_m2_card(
                                    value=hero_kpis["price_per_m2"]["value"],
                                    trend=hero_kpis["price_per_m2"]["trend"],
                                    change=hero_kpis["price_per_m2"]["change"],
                                    bedrooms=hero_kpis["price_per_m2"]["bedrooms"],
                                    subtitle=hero_kpis["price_per_m2"]["subtitle"],
                                ),
                                width=12,
                                md=6,
                                lg=2,
                                className="mb-3",
                            ),
                            dbc.Col(
                                HousingKPICard.create_supply_gap_card(
                                    value=hero_kpis["supply_gap"]["value"],
                                    trend=hero_kpis["supply_gap"]["trend"],
                                    status=hero_kpis["supply_gap"]["status"],
                                    severity=hero_kpis["supply_gap"]["severity"],
                                    subtitle=hero_kpis["supply_gap"]["subtitle"],
                                ),
                                width=12,
                                md=6,
                                lg=2,
                                className="mb-3",
                            ),
                        ],
                        className="g-3 mb-4",
                    )
                ],
                style={"minHeight": "30vh"},
            ),
            html.Div(
                [
                    html.H5("Market Analytics", className="section-label mb-3"),
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    html.Div(
                                        [
                                            html.H6(
                                                "Price Distribution by Suburb",
                                                className="mb-2",
                                                style={
                                                    "fontSize": "0.9rem",
                                                    "fontWeight": "600",
                                                },
                                            ),
                                            dcc.Graph(
                                                id="housing-boxplot",
                                                figure=_create_boxplot_figure(
                                                    chart_data
                                                ),
                                                config={"displayModeBar": False},
                                                style={"height": "280px"},
                                            ),
                                        ],
                                        className="chart-card p-3",
                                    )
                                ],
                                width=12,
                                md=7,
                                className="mb-3",
                            ),
                            dbc.Col(
                                [
                                    html.Div(
                                        [
                                            html.H6(
                                                "Listings Volume Trend",
                                                className="mb-2",
                                                style={
                                                    "fontSize": "0.9rem",
                                                    "fontWeight": "600",
                                                },
                                            ),
                                            dcc.Graph(
                                                id="housing-line",
                                                figure=_create_line_figure(
                                                    chart_data["line_chart"]
                                                ),
                                                config={"displayModeBar": False},
                                                style={"height": "280px"},
                                            ),
                                        ],
                                        className="chart-card p-3",
                                    )
                                ],
                                width=12,
                                md=5,
                                className="mb-3",
                            ),
                        ],
                        className="mb-3",
                    ),
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    html.Div(
                                        [
                                            html.H6(
                                                "Property Type Breakdown",
                                                className="mb-2",
                                                style={
                                                    "fontSize": "0.9rem",
                                                    "fontWeight": "600",
                                                },
                                            ),
                                            dcc.Graph(
                                                id="housing-stacked-bar",
                                                figure=_create_stacked_bar_figure(
                                                    chart_data["stacked_bar"]
                                                ),
                                                config={"displayModeBar": False},
                                                style={"height": "240px"},
                                            ),
                                        ],
                                        className="chart-card p-3",
                                    )
                                ],
                                width=12,
                                md=4,
                                className="mb-3",
                            ),
                            dbc.Col(
                                [
                                    html.Div(
                                        [
                                            html.H6(
                                                "Price per m² vs Bedrooms",
                                                className="mb-2",
                                                style={
                                                    "fontSize": "0.9rem",
                                                    "fontWeight": "600",
                                                },
                                            ),
                                            dcc.Graph(
                                                id="housing-scatter",
                                                figure=_create_scatter_figure(
                                                    chart_data["scatter"]
                                                ),
                                                config={"displayModeBar": False},
                                                style={"height": "240px"},
                                            ),
                                        ],
                                        className="chart-card p-3",
                                    )
                                ],
                                width=12,
                                md=4,
                                className="mb-3",
                            ),
                            dbc.Col(
                                [
                                    html.Div(
                                        [
                                            html.H6(
                                                "Market Speed (DOM Distribution)",
                                                className="mb-2",
                                                style={
                                                    "fontSize": "0.9rem",
                                                    "fontWeight": "600",
                                                },
                                            ),
                                            dcc.Graph(
                                                id="housing-dom-histogram",
                                                figure=_create_histogram_figure(
                                                    chart_data["dom_histogram"]
                                                ),
                                                config={"displayModeBar": False},
                                                style={"height": "240px"},
                                            ),
                                        ],
                                        className="chart-card p-3",
                                    )
                                ],
                                width=12,
                                md=4,
                                className="mb-3",
                            ),
                        ]
                    ),
                ],
                className="mb-4",
            ),
            html.Div(
                [
                    html.H5("Supply & Demand", className="section-label mb-3"),
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    html.Div(
                                        [
                                            html.H6(
                                                "Supply vs Demand Heatmap",
                                                className="mb-2",
                                                style={
                                                    "fontSize": "0.9rem",
                                                    "fontWeight": "600",
                                                },
                                            ),
                                            dcc.Graph(
                                                id="housing-heatmap",
                                                figure=_create_heatmap_figure(
                                                    chart_data
                                                ),
                                                config={"displayModeBar": False},
                                                style={"height": "280px"},
                                            ),
                                        ],
                                        className="chart-card p-3",
                                    )
                                ],
                                width=12,
                                md=8,
                                className="mb-3",
                            ),
                            dbc.Col(
                                [
                                    html.Div(
                                        [
                                            html.H6(
                                                "Consents vs Listings",
                                                className="mb-2",
                                                style={
                                                    "fontSize": "0.9rem",
                                                    "fontWeight": "600",
                                                },
                                            ),
                                            dcc.Graph(
                                                id="housing-consents-listings",
                                                figure=_create_consents_figure(
                                                    data["supply_demand"]
                                                ),
                                                config={"displayModeBar": False},
                                                style={"height": "280px"},
                                            ),
                                        ],
                                        className="chart-card p-3",
                                    )
                                ],
                                width=12,
                                md=4,
                                className="mb-3",
                            ),
                        ]
                    ),
                ]
            ),
        ],
        fluid=True,
        className="housing-dashboard py-4",
        style={
            "backgroundColor": "#f8f9fa",
            "minHeight": "100vh",
            "paddingLeft": "24px",
            "paddingRight": "24px",
        },
    )


def _create_filter_bar():
    return dbc.Row(
        [
            dbc.Col(
                [
                    html.Div(
                        [
                            html.Span(
                                "Filters",
                                className="me-3 text-muted",
                                style={"fontSize": "0.85rem"},
                            ),
                            dcc.Dropdown(
                                id="housing-region-selector",
                                options=[
                                    {"label": c, "value": c}
                                    for c in ["All"] + CITIES_LIST
                                ],
                                value="All",
                                placeholder="Select Region",
                                clearable=False,
                                style={"width": "160px", "display": "inline-block"},
                            ),
                            html.Span("|", className="mx-3 text-muted"),
                            dcc.Dropdown(
                                id="housing-suburb-selector",
                                options=[
                                    {"label": s, "value": s}
                                    for s in ["All"] + SUBURBS_LIST
                                ],
                                value="All",
                                placeholder="Select Suburb",
                                clearable=False,
                                style={"width": "160px", "display": "inline-block"},
                            ),
                            html.Span("|", className="mx-3 text-muted"),
                            dbc.ButtonGroup(
                                [
                                    dbc.Button(
                                        "3M",
                                        id="housing-btn-3m",
                                        color="outline-primary",
                                        size="sm",
                                        active=True,
                                    ),
                                    dbc.Button(
                                        "6M",
                                        id="housing-btn-6m",
                                        color="outline-primary",
                                        size="sm",
                                    ),
                                    dbc.Button(
                                        "12M",
                                        id="housing-btn-12m",
                                        color="outline-primary",
                                        size="sm",
                                    ),
                                ],
                                size="sm",
                            ),
                        ],
                        className="d-flex align-items-center justify-content-end py-2",
                    )
                ],
                width=12,
            )
        ],
        className="filter-bar bg-white border-bottom",
        style={
            "position": "sticky",
            "top": "56px",
            "zIndex": "1020",
            "padding": "8px 24px",
        },
    )


def _create_boxplot_figure(chart_data):
    """Render suburb prices as a horizontal bar chart since data is single values."""
    bp = chart_data.get("boxplot", {})
    suburbs = bp.get("suburbs", [])
    prices = bp.get("prices", [])

    if not suburbs or not prices:
        return go.Figure()

    colors = [
        "#2E86AB",
        "#A23B72",
        "#F18F01",
        "#28a745",
        "#6c757d",
        "#17a2b8",
        "#bc5090",
        "#ff6f00",
        "#58595b",
        "#003f5c",
    ]

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=prices,
            y=suburbs,
            orientation="h",
            marker_color=colors[: len(suburbs)],
            text=[f"${p:,.0f}" for p in prices],
            textposition="outside",
            textfont=dict(size=10),
            hovertemplate="%{y}<br>Median: $%{x:,.0f}<extra></extra>",
        )
    )

    fig.update_layout(
        margin=dict(l=120, r=20, t=20, b=40),
        paper_bgcolor="white",
        plot_bgcolor="white",
        showlegend=False,
        font=dict(size=10),
        xaxis=dict(
            title="Median Price (NZD)",
            gridcolor="#f0f0f0",
            tickprefix="$",
            tickformat=",.0f",
        ),
        yaxis=dict(autorange="reversed"),
        bargap=0.3,
    )
    return fig


def _create_line_figure(line_data):
    if not line_data or not line_data.get("values"):
        return go.Figure()

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=line_data["weeks"],
            y=line_data["values"],
            mode="lines+markers",
            line=dict(color="#2E86AB", width=2.5),
            marker=dict(size=7, color="#2E86AB"),
            fill="tozeroy",
            fillcolor="rgba(46, 134, 171, 0.12)",
            hovertemplate="%{y:.1f} listings<extra></extra>",
        )
    )

    fig.update_layout(
        margin=dict(l=40, r=20, t=20, b=40),
        paper_bgcolor="white",
        plot_bgcolor="white",
        showlegend=False,
        font=dict(size=10),
        yaxis=dict(title="New Listings", gridcolor="#f0f0f0"),
        xaxis=dict(showgrid=True),
    )
    return fig


def _create_stacked_bar_figure(stacked_bar_data):
    if not stacked_bar_data:
        return go.Figure()

    suburbs = [d["suburb"] for d in stacked_bar_data]
    fig = go.Figure()

    for col, color in zip(
        ["House", "Apartment", "Townhouse"], ["#2E86AB", "#A23B72", "#F18F01"]
    ):
        values = [d.get(col, 0) for d in stacked_bar_data]
        fig.add_trace(
            go.Bar(
                name=col,
                x=suburbs,
                y=values,
                marker_color=color,
                hovertemplate="%{y:.0f}%<extra></extra>",
            )
        )

    fig.update_layout(
        margin=dict(l=40, r=20, t=20, b=60),
        paper_bgcolor="white",
        plot_bgcolor="white",
        barmode="stack",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, font=dict(size=9)),
        font=dict(size=10),
        xaxis=dict(tickangle=-30, showgrid=False),
        yaxis=dict(title="% Share", gridcolor="#f0f0f0"),
    )
    return fig


def _create_scatter_figure(scatter_data):
    if not scatter_data:
        return go.Figure()

    fig = go.Figure()

    colors_map = {
        "Ponsonby": "#2E86AB",
        "Mt Eden": "#A23B72",
        "Newmarket": "#F18F01",
        "Kelburn": "#28a745",
        "Miramar": "#6c757d",
        "Riccarton": "#17a2b8",
        "New Brighton": "#bc5090",
        "Hillcrest": "#ff6f00",
        "North East Valley": "#58595b",
        "Mount Maunganui": "#003f5c",
    }

    for suburb in set(d["suburb"] for d in scatter_data):
        pts = [d for d in scatter_data if d["suburb"] == suburb]
        fig.add_trace(
            go.Scatter(
                x=[p["bedrooms"] for p in pts],
                y=[p["price_m2"] for p in pts],
                mode="markers",
                name=suburb,
                marker=dict(
                    size=10,
                    color=colors_map.get(suburb, "#6c757d"),
                    line=dict(width=1, color="white"),
                ),
                hovertemplate="%{fullData.name}<br>%{x}bd: $%{y:,.0f}/m²<extra></extra>",
            )
        )

    fig.update_layout(
        margin=dict(l=50, r=20, t=20, b=40),
        paper_bgcolor="white",
        plot_bgcolor="white",
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, font=dict(size=9)),
        font=dict(size=10),
        xaxis=dict(title="Bedrooms", dtick=1, gridcolor="#f0f0f0"),
        yaxis=dict(title="Price per m² (NZD)", gridcolor="#f0f0f0", tickprefix="$"),
    )
    return fig


def _create_histogram_figure(dom_histogram):
    if not dom_histogram:
        return go.Figure()

    buckets = [d["bucket"] for d in dom_histogram]
    counts = [d["count"] for d in dom_histogram]

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=buckets,
            y=counts,
            marker_color="#2E86AB",
            hovertemplate="%{y} suburbs<extra></extra>",
        )
    )

    fig.update_layout(
        margin=dict(l=40, r=20, t=20, b=40),
        paper_bgcolor="white",
        plot_bgcolor="white",
        showlegend=False,
        font=dict(size=10),
        xaxis=dict(title="Days on Market", gridcolor="#f0f0f0"),
        yaxis=dict(title="# Suburbs", gridcolor="#f0f0f0"),
    )
    return fig


def _create_heatmap_figure(chart_data):
    regions = chart_data.get("regions", [])
    months = chart_data.get("heatmap_months", [])
    heatmap = chart_data.get("heatmap", {})

    if not regions or not months:
        return go.Figure()

    z = []
    for region in regions:
        row = []
        for month in months:
            val = heatmap.get(f"{region}_{month}", {}).get("value", 50)
            row.append(val)
        z.append(row)

    fig = go.Figure(
        go.Heatmap(
            z=z,
            x=months,
            y=regions,
            colorscale="RdYlGn_r",
            hovertemplate="%{y} - %{x}<br>Deficit: %{z:.1f}<extra></extra>",
            colorbar=dict(title="Deficit Score", len=0.4),
        )
    )

    fig.update_layout(
        margin=dict(l=10, r=10, t=20, b=10),
        paper_bgcolor="white",
        font=dict(size=10),
        xaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.3)"),
        yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.3)"),
    )
    return fig


def _create_consents_figure(supply_demand):
    if not supply_demand or "data" not in supply_demand:
        return go.Figure()

    labels = supply_demand["data"]["labels"]
    consents = supply_demand["data"]["consents"]
    listings = supply_demand["data"]["listings"]

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_trace(
        go.Bar(
            x=labels,
            y=consents,
            name="Building Consents",
            marker_color="#2E86AB",
            opacity=0.7,
            hovertemplate="%{y:,} consents<extra></extra>",
        ),
        secondary_y=False,
    )

    fig.add_trace(
        go.Scatter(
            x=labels,
            y=listings,
            name="Listings Volume",
            line=dict(color="#A23B72", width=2.5),
            marker=dict(size=7, color="#A23B72"),
            hovertemplate="%{y:,} listings<extra></extra>",
        ),
        secondary_y=True,
    )

    fig.update_layout(
        margin=dict(l=40, r=40, t=20, b=40),
        paper_bgcolor="white",
        plot_bgcolor="white",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=9),
        ),
        showlegend=True,
        font=dict(size=10),
    )
    fig.update_yaxes(title_text="Consents", secondary_y=False, gridcolor="#f0f0f0")
    fig.update_yaxes(title_text="Listings", secondary_y=True, showgrid=False)
    fig.update_xaxes(gridcolor="#f0f0f0")

    return fig
