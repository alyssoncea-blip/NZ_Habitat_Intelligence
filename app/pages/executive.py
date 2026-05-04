"""
Executive Dashboard - Power BI Style Refactored
Layout edge-to-edge com Hero KPIs, Choropleth Map e Insights Charts
"""

import dash_bootstrap_components as dbc
from dash import html, dcc

from ..components.cards import ExecutiveKPICard
from ..components.layout import create_section_header, create_filter_bar
from ..components.choropleth_map import create_map_component
from ..data.executive_kpi_data import load_executive_data
from ..utils.logger import get_logger

logger = get_logger(__name__)


def create_executive_dashboard():
    """
    Create the Executive Dashboard in Power BI style.

    Layout:
    - Hero KPI Row (6 cards em uma linha) ~40% altura
    - Choropleth Map (full-width) ~35% altura
    - Insights Charts (3 charts) ~25% altura

    Returns:
        Dash component com layout completo
    """
    logger.info("Creating Power BI style executive dashboard")

    data = load_executive_data()
    hero_kpis = data["hero_kpis"]
    regions_data = hero_kpis["map_preview"]["regions"]

    return dbc.Container([

        create_section_header(
            "NZ Housing Pulse",
            "Executive Overview - Real-time Market Intelligence"
        ),

        create_filter_bar(
            region_options=["All Regions"] + data["regions"],
            time_options=["3M", "6M", "12M", "1Y", "5Y"]
        ),

        html.Div([
            dbc.Row([
                dbc.Col(
                    ExecutiveKPICard.create_pressure_index_card(
                        value=hero_kpis["pressure_index"]["value"],
                        trend=hero_kpis["pressure_index"]["trend"],
                        change=hero_kpis["pressure_index"]["change"],
                        sparkline_data=hero_kpis["pressure_index"].get("sparkline")
                    ),
                    width=12, md=6, lg=2, className="mb-3"
                ),
                dbc.Col(
                    ExecutiveKPICard.create_affordability_card(
                        value=hero_kpis["affordability"]["value"],
                        trend=hero_kpis["affordability"]["trend"],
                        change=hero_kpis["affordability"]["change"]
                    ),
                    width=12, md=6, lg=2, className="mb-3"
                ),
                dbc.Col(
                    ExecutiveKPICard.create_price_mom_card(
                        value=hero_kpis["price_mom"]["value"],
                        trend=hero_kpis["price_mom"]["trend"],
                        sparkline_data=hero_kpis["price_mom"].get("sparkline")
                    ),
                    width=12, md=6, lg=2, className="mb-3"
                ),
                dbc.Col(
                    ExecutiveKPICard.create_ocr_card(
                        current=hero_kpis["ocr"]["current"],
                        twelve_months_ago=hero_kpis["ocr"]["twelve_months_ago"],
                        change_bps=hero_kpis["ocr"]["change_bps"],
                        next_decision=hero_kpis["ocr"].get("next_decision", "2026-05-28")
                    ),
                    width=12, md=6, lg=2, className="mb-3"
                ),
                dbc.Col(
                    ExecutiveKPICard.create_top3_regions_card(
                        top3_data=hero_kpis["top3"]["top3"]
                    ),
                    width=12, md=6, lg=2, className="mb-3"
                ),
                dbc.Col(
                    ExecutiveKPICard.create_map_preview_card(),
                    width=12, md=6, lg=2, className="mb-3"
                ),
            ], className="g-3 mb-4")
        ], style={"minHeight": "35vh"}),

        html.Div([
            dbc.Row([
                dbc.Col([
                    html.Div([
                        html.H5("Regional Pressure Index",
                                className="mb-3",
                                style={"fontSize": "1rem", "fontWeight": "600"}),
                        html.P("Regional housing market pressure index",
                               className="text-muted mb-3",
                               style={"fontSize": "0.8rem"}),
                        create_map_component(
                            regions_data=regions_data,
                            map_id="executive-choropleth",
                            height=350
                        )
                    ], className="bg-white p-4 rounded",
                       style={"boxShadow": "0 2px 8px rgba(0,0,0,0.08)"})
                ], width=12)
            ])
        ], style={"minHeight": "45vh"}, className="mb-4"),

        html.Div([
            dbc.Row([
                dbc.Col([
                    html.Div([
                        html.H6("Pressure vs Affordability",
                                className="mb-3",
                                style={"fontSize": "0.9rem", "fontWeight": "600"}),
                        dcc.Graph(
                            id="scatter-pressure-affordability",
                            figure=_create_scatter_figure(data["scatter_data"]),
                            config={"displayModeBar": False},
                            style={"height": "250px"}
                        )
                    ], className="bg-white p-3 rounded h-100",
                       style={"boxShadow": "0 2px 8px rgba(0,0,0,0.08)"})
                ], width=12, md=4, className="mb-3"),

                dbc.Col([
                    html.Div([
                        html.H6("Price Change MoM",
                                className="mb-3",
                                style={"fontSize": "0.9rem", "fontWeight": "600"}),
                        dcc.Graph(
                            id="line-price-mom",
                            figure=_create_line_figure(data["line_chart"]),
                            config={"displayModeBar": False},
                            style={"height": "250px"}
                        )
                    ], className="bg-white p-3 rounded h-100",
                       style={"boxShadow": "0 2px 8px rgba(0,0,0,0.08)"})
                ], width=12, md=4, className="mb-3"),

                dbc.Col([
                    html.Div([
                        html.H6("OCR vs Pressure",
                                className="mb-3",
                                style={"fontSize": "0.9rem", "fontWeight": "600"}),
                        dcc.Graph(
                            id="dual-axis-ocr-pressure",
                            figure=_create_dual_axis_figure(data["dual_axis"]),
                            config={"displayModeBar": False},
                            style={"height": "250px"}
                        )
                    ], className="bg-white p-3 rounded h-100",
                       style={"boxShadow": "0 2px 8px rgba(0,0,0,0.08)"})
                ], width=12, md=4, className="mb-3"),
            ], className="g-3")
        ], style={"minHeight": "35vh"}),

    ], fluid=True, className="executive-dashboard py-4",
       style={
           "backgroundColor": "#f8f9fa",
           "minHeight": "100vh",
           "paddingLeft": "24px",
           "paddingRight": "24px"
       })


def _create_scatter_figure(scatter_data):
    """Create the Pressure vs Affordability scatter plot."""
    import plotly.graph_objects as go

    if not scatter_data:
        return go.Figure()

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=[d["affordability"] for d in scatter_data],
        y=[d["pressure"] for d in scatter_data],
        mode='markers',
        marker=dict(
            size=10,
            color=[d["pressure"] for d in scatter_data],
            colorscale='RdYlGn_r',
            showscale=False,
            line=dict(width=1, color='white')
        ),
        text=[d["region"] for d in scatter_data],
        hovertemplate='<b>%{text}</b><br>Affordability: %{x:.1f}x<br>Pressure: %{y:.1f}<extra></extra>',
    ))

    fig.update_layout(
        margin=dict(l=40, r=20, t=20, b=40),
        xaxis_title="Affordability (Price/Income)",
        yaxis_title="Pressure Index",
        paper_bgcolor="white",
        plot_bgcolor="white",
        showlegend=False,
        font=dict(size=10),
        xaxis=dict(gridcolor="#f0f0f0", showgrid=True),
        yaxis=dict(gridcolor="#f0f0f0", showgrid=True),
    )

    return fig


def _create_line_figure(line_data):
    """Create the Price Change MoM line chart."""
    import plotly.graph_objects as go

    if not line_data or not line_data.get("values"):
        return go.Figure()

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=line_data["months"],
        y=line_data["values"],
        mode='lines+markers',
        line=dict(color='#2E86AB', width=2),
        marker=dict(size=6, color='#2E86AB'),
        fill='tozeroy',
        fillcolor='rgba(46, 134, 171, 0.1)',
    ))

    fig.update_layout(
        margin=dict(l=40, r=20, t=20, b=40),
        xaxis_title=None,
        yaxis_title=f"Change ({line_data['unit']})",
        paper_bgcolor="white",
        plot_bgcolor="white",
        showlegend=False,
        font=dict(size=10),
        xaxis=dict(gridcolor="#f0f0f0", showgrid=True),
        yaxis=dict(gridcolor="#f0f0f0", showgrid=True),
    )

    return fig


def _create_dual_axis_figure(dual_data):
    """Create the dual axis OCR vs Pressure chart."""
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    if not dual_data or not dual_data.get("months"):
        return go.Figure()

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_trace(
        go.Scatter(
            x=dual_data["months"],
            y=dual_data["ocr"],
            name="OCR",
            line=dict(color='#dc3545', width=2),
            marker=dict(size=6)
        ),
        secondary_y=False,
    )

    fig.add_trace(
        go.Scatter(
            x=dual_data["months"],
            y=dual_data["pressure"],
            name="Pressure",
            line=dict(color='#2E86AB', width=2),
            marker=dict(size=6)
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
            font=dict(size=9)
        ),
        font=dict(size=10),
        showlegend=True,
    )

    fig.update_xaxes(gridcolor="#f0f0f0", showgrid=True)
    fig.update_yaxes(gridcolor="#f0f0f0", showgrid=True, secondary_y=False)
    fig.update_yaxes(gridcolor="#f0f0f0", showgrid=True, secondary_y=True)

    return fig


def create_quick_stats(kpis_df):
    """Legacy: mantido para compatibilidade."""
    return html.Div()


def create_kpi_grid(categorized_kpis):
    """Legacy: mantido para compatibilidade."""
    return html.Div()


def group_kpis_by_category(kpis_df):
    """Legacy: mantido para compatibilidade."""
    return {}


def create_executive_insights(kpis_df):
    """Legacy: mantido para compatibilidade."""
    return html.Div()


__all__ = [
    'create_executive_dashboard',
    'create_quick_stats',
    'create_kpi_grid',
    'group_kpis_by_category',
    'create_executive_insights',
]
