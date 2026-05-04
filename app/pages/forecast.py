"""Forecast Dashboard - Premium Edition (KPI 28-34)."""

import dash_bootstrap_components as dbc
from dash import dcc, html
import plotly.graph_objects as go

from app.components.cards import ForecastKPICard
from app.components.layout import create_section_header
from app.data.forecast_kpi_data import load_forecast_data
from app.utils.logger import get_logger

logger = get_logger(__name__)

ACCENT = {
    "forecast": "#2E86AB",
    "confidence": "#148F77",
    "ocr": "#1A5276",
    "tourism": "#D35400",
    "risk": "#E74C3C",
    "model": "#8E44AD",
}


def create_forecast_dashboard():
    """Create Forecast & Risk dashboard."""
    logger.info("Creating forecast dashboard")
    data = load_forecast_data()

    return dbc.Container(
        fluid=True,
        className="forecast-dashboard",
        children=[
            create_section_header(
                "Forecast & Risk Dashboard",
                "Premium Edition — KPIs 28-34: Price Forecast, Confidence, OCR/Tourism Impact, Risk Regions & Model Confidence",
            ),
            _build_hero_row(data["hero_kpis"]),
            _build_forecast_chart(data["chart_data"]),
            _build_decomposition_section(data["chart_data"]),
            _build_scenario_comparison(data["chart_data"]),
            _build_risk_section(data["chart_data"]),
            dcc.Store(id="forecast-kpis-data", data=data),
            dcc.Store(
                id="forecast-filter-state",
                data={"timeframe": "12M", "scenario": "Base"},
            ),
        ],
    )


def _build_hero_row(hero_kpis: dict) -> html.Div:
    kpis = hero_kpis
    return html.Div(
        [
            dbc.Row(
                [
                    dbc.Col(
                        ForecastKPICard.create_price_forecast_card(
                            **kpis["price_forecast"]
                        ),
                        width=12,
                        lg=4,
                    ),
                    dbc.Col(
                        ForecastKPICard.create_confidence_range_card(
                            **kpis["confidence_range"]
                        ),
                        width=12,
                        lg=4,
                    ),
                    dbc.Col(
                        ForecastKPICard.create_ocr_impact_card(**kpis["ocr_impact"]),
                        width=12,
                        lg=4,
                    ),
                ],
                className="g-3 mb-3",
            ),
            dbc.Row(
                [
                    dbc.Col(
                        ForecastKPICard.create_tourism_impact_card(
                            **kpis["tourism_impact"]
                        ),
                        width=12,
                        lg=4,
                    ),
                    dbc.Col(
                        ForecastKPICard.create_risk_regions_card(
                            **kpis["high_risk_regions"]
                        ),
                        width=12,
                        lg=4,
                    ),
                    dbc.Col(
                        ForecastKPICard.create_model_confidence_card(
                            **kpis["model_confidence"]
                        ),
                        width=12,
                        lg=4,
                    ),
                ],
                className="g-3",
            ),
        ],
        className="mb-4",
    )


def _build_forecast_chart(chart_data: dict) -> html.Div:
    fs = chart_data["forecast_series"]
    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=list(range(len(fs["historical"]))),
            y=fs["historical"],
            mode="lines",
            name="Historical",
            line=dict(color=ACCENT["forecast"], width=2.5),
            hovertemplate="Month %{x}<br>Price: $%{y:,.0f}<extra></extra>",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=list(
                range(
                    len(fs["historical"]), len(fs["historical"]) + len(fs["forecast"])
                )
            ),
            y=fs["forecast"],
            mode="lines",
            name="Forecast",
            line=dict(color=ACCENT["forecast"], width=2.5, dash="dash"),
            hovertemplate="Month %{x}<br>Forecast: $%{y:,.0f}<extra></extra>",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=list(
                range(
                    len(fs["historical"]), len(fs["historical"]) + len(fs["forecast"])
                )
            ),
            y=fs["conf_95_high"],
            mode="lines",
            name="95% CI",
            line=dict(width=0),
            showlegend=False,
            hoverinfo="skip",
            fillcolor="rgba(46,134,171,0.1)",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=list(
                range(
                    len(fs["historical"]), len(fs["historical"]) + len(fs["forecast"])
                )
            ),
            y=fs["conf_95_low"],
            mode="lines",
            name="95% CI",
            line=dict(width=0),
            showlegend=False,
            hoverinfo="skip",
            fill="tonextx",
            fillcolor="rgba(46,134,171,0.1)",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=list(
                range(
                    len(fs["historical"]), len(fs["historical"]) + len(fs["forecast"])
                )
            ),
            y=fs["conf_80_high"],
            mode="lines",
            name="80% CI",
            line=dict(width=0),
            showlegend=False,
            hoverinfo="skip",
            fillcolor="rgba(46,134,171,0.2)",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=list(
                range(
                    len(fs["historical"]), len(fs["historical"]) + len(fs["forecast"])
                )
            ),
            y=fs["conf_80_low"],
            mode="lines",
            name="80% CI",
            line=dict(width=0),
            showlegend=False,
            hoverinfo="skip",
            fill="tonextx",
            fillcolor="rgba(46,134,171,0.2)",
        )
    )

    split_point = len(fs["historical"])
    fig.add_vline(
        x=split_point - 0.5, line_dash="dot", line_color="#adb5bd", line_width=1.5
    )

    fig.update_layout(
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(l=50, r=30, t=20, b=50),
        height=300,
        legend=dict(orientation="h", y=1.12, x=0.5, xanchor="center"),
        xaxis=dict(showgrid=True, gridcolor="rgba(0,0,0,0.05)", tickfont=dict(size=10)),
        yaxis=dict(
            title="Median Price (NZD)",
            showgrid=True,
            gridcolor="rgba(0,0,0,0.05)",
            tickfont=dict(size=10),
            tickprefix="$",
        ),
        hovermode="x unified",
    )

    return dbc.Card(
        dbc.CardBody(
            [
                html.H6(
                    "12-Month Price Forecast with Confidence Bands",
                    style={
                        "fontSize": "0.75rem",
                        "fontWeight": "700",
                        "textTransform": "uppercase",
                        "letterSpacing": "0.5px",
                        "color": "#495057",
                        "marginBottom": "8px",
                    },
                ),
                dcc.Graph(
                    figure=fig,
                    config={"displayModeBar": False},
                    style={"height": "300px"},
                ),
                html.Div(
                    [
                        html.Span(
                            "Blue = Historical  |  Dashed = Forecast  |  Shaded = Confidence Intervals",
                            style={"fontSize": "0.68rem", "color": "#8898aa"},
                        ),
                    ],
                    className="text-center mt-1",
                ),
            ],
            className="p-3",
        ),
        className="mb-4",
    )


def _build_decomposition_section(chart_data: dict) -> html.Div:
    trend_fig = _make_trend_chart(chart_data["trend_data"])

    return html.Div(
        [
            html.H5(
                "Trend + Seasonality Decomposition",
                style={
                    "fontSize": "0.85rem",
                    "fontWeight": "800",
                    "textTransform": "uppercase",
                    "letterSpacing": "0.5px",
                    "color": "#12263A",
                    "borderLeft": "4px solid " + ACCENT["forecast"],
                    "paddingLeft": "10px",
                    "marginBottom": "12px",
                },
            ),
            dbc.Card(
                dbc.CardBody(
                    [
                        dcc.Graph(
                            figure=trend_fig,
                            config={"displayModeBar": False},
                            style={"height": "260px"},
                        ),
                    ],
                    className="p-3",
                )
            ),
        ],
        className="mb-4",
    )


def _make_trend_chart(data: dict) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=data["months"],
            y=data["trend"],
            mode="lines",
            name="Trend",
            line=dict(color=ACCENT["forecast"], width=2.5),
            hovertemplate="<b>%{x}</b><br>Trend: %{y:.0f}<extra></extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=data["months"],
            y=data["seasonal"],
            mode="lines",
            name="Seasonality",
            line=dict(color=ACCENT["tourism"], width=2),
            hovertemplate="<b>%{x}</b><br>Seasonal: %{y:.0f}<extra></extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=data["months"],
            y=data["residual"],
            mode="lines",
            name="Residual",
            line=dict(color="#adb5bd", width=1.5, dash="dot"),
            hovertemplate="<b>%{x}</b><br>Residual: %{y:.1f}<extra></extra>",
        )
    )
    fig.update_layout(
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(l=50, r=30, t=20, b=40),
        legend=dict(orientation="h", y=1.12, x=0.5, xanchor="center"),
        xaxis=dict(showgrid=True, gridcolor="rgba(0,0,0,0.05)", tickfont=dict(size=10)),
        yaxis=dict(
            title="Index",
            showgrid=True,
            gridcolor="rgba(0,0,0,0.05)",
            tickfont=dict(size=10),
        ),
        hovermode="x unified",
    )
    return fig


def _build_scenario_comparison(chart_data: dict) -> html.Div:
    scenarios = chart_data["scenario_data"]

    dom_fig = _make_dom_forecast_chart(chart_data["dom_forecast"], chart_data["months"])

    return html.Div(
        [
            html.H5(
                "Scenario Comparison Panel",
                style={
                    "fontSize": "0.85rem",
                    "fontWeight": "800",
                    "textTransform": "uppercase",
                    "letterSpacing": "0.5px",
                    "color": "#12263A",
                    "borderLeft": "4px solid " + ACCENT["ocr"],
                    "paddingLeft": "10px",
                    "marginBottom": "12px",
                },
            ),
            dbc.Row(
                [
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(
                                [
                                    html.H6(
                                        "OCR Scenario Impact on Price",
                                        style={
                                            "fontSize": "0.75rem",
                                            "fontWeight": "700",
                                            "textTransform": "uppercase",
                                            "letterSpacing": "0.5px",
                                            "color": "#495057",
                                            "marginBottom": "8px",
                                        },
                                    ),
                                    _build_scenario_table(scenarios),
                                ]
                            ),
                            className="p-3",
                        ),
                        className="col-12 col-lg-6",
                    ),
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(
                                [
                                    html.H6(
                                        "DOM Forecast (12 Months)",
                                        style={
                                            "fontSize": "0.75rem",
                                            "fontWeight": "700",
                                            "textTransform": "uppercase",
                                            "letterSpacing": "0.5px",
                                            "color": "#495057",
                                            "marginBottom": "8px",
                                        },
                                    ),
                                    dcc.Graph(
                                        figure=dom_fig,
                                        config={"displayModeBar": False},
                                        style={"height": "200px"},
                                    ),
                                ]
                            ),
                            className="p-3",
                        ),
                        className="col-12 col-lg-6",
                    ),
                ],
                className="g-3 mb-4",
            ),
        ]
    )


def _build_scenario_table(scenarios: dict) -> html.Div:
    labels = {
        "base": ("Base Case", "#495057"),
        "optimistic": ("Optimistic", "#28a745"),
        "stress": ("Stress", "#dc3545"),
    }
    rows = []
    for key in ["base", "optimistic", "stress"]:
        s = scenarios[key]
        label, color = labels[key]
        rows.append(
            html.Div(
                [
                    html.Span(
                        label,
                        style={
                            "fontSize": "0.72rem",
                            "fontWeight": "700",
                            "width": "80px",
                            "color": color,
                        },
                    ),
                    html.Span(
                        f"${s['price']:,.0f}",
                        style={
                            "fontSize": "0.78rem",
                            "width": "90px",
                            "textAlign": "right",
                        },
                    ),
                    html.Span(
                        f"DOM {s['dom']}d",
                        style={
                            "fontSize": "0.72rem",
                            "color": "#8898aa",
                            "marginLeft": "8px",
                        },
                    ),
                    html.Span(
                        f"L: {s['listings']:,}",
                        style={
                            "fontSize": "0.72rem",
                            "color": "#8898aa",
                            "marginLeft": "8px",
                        },
                    ),
                ],
                className="d-flex mb-1",
            )
        )

    return html.Div(rows)


def _make_scenario_chart(scenarios: dict) -> go.Figure:
    labels = ["Base", "Optimistic", "Stress"]
    prices = [scenarios[k]["price"] for k in ["base", "optimistic", "stress"]]
    colors = ["#495057", "#28a745", "#dc3545"]

    fig = go.Figure(
        go.Bar(
            x=labels,
            y=prices,
            marker_color=colors,
            text=[f"${p:,}" for p in prices],
            textposition="outside",
            hovertemplate="<b>%{x}</b><br>$%{y:,}<extra></extra>",
        )
    )
    fig.update_layout(
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(l=40, r=30, t=20, b=40),
        height=200,
        xaxis=dict(showgrid=False),
        yaxis=dict(
            title="Price (NZD)",
            showgrid=True,
            gridcolor="rgba(0,0,0,0.05)",
            tickfont=dict(size=9),
        ),
        showlegend=False,
    )
    return fig


def _make_dom_forecast_chart(dom_data: list, months: list) -> go.Figure:
    fig = go.Figure(
        go.Scatter(
            x=months,
            y=dom_data,
            mode="lines+markers",
            line=dict(color=ACCENT["tourism"], width=2.5),
            marker=dict(size=6),
            fill="tozeroy",
            fillcolor="rgba(211,84,0,0.15)",
            hovertemplate="<b>%{x}</b><br>DOM: %{y} days<extra></extra>",
        )
    )
    fig.update_layout(
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(l=40, r=20, t=20, b=40),
        xaxis=dict(showgrid=True, gridcolor="rgba(0,0,0,0.05)", tickfont=dict(size=10)),
        yaxis=dict(
            title="Days on Market",
            showgrid=True,
            gridcolor="rgba(0,0,0,0.05)",
            tickfont=dict(size=10),
        ),
        hovermode="x unified",
    )
    return fig


def _build_risk_section(chart_data: dict) -> html.Div:
    heatmap_fig = _make_risk_heatmap(
        chart_data["regions"], chart_data["heatmap_z"], chart_data["heatmap_months"]
    )

    return html.Div(
        [
            html.H5(
                "Risk Heatmap & Divergence Alerts",
                style={
                    "fontSize": "0.85rem",
                    "fontWeight": "800",
                    "textTransform": "uppercase",
                    "letterSpacing": "0.5px",
                    "color": "#12263A",
                    "borderLeft": "4px solid " + ACCENT["risk"],
                    "paddingLeft": "10px",
                    "marginBottom": "12px",
                },
            ),
            dbc.Card(
                dbc.CardBody(
                    [
                        html.H6(
                            "Forecast Risk by Region × Time (Blue=Stable, Orange=Moderate, Red=High)",
                            style={
                                "fontSize": "0.75rem",
                                "fontWeight": "700",
                                "textTransform": "uppercase",
                                "letterSpacing": "0.5px",
                                "color": "#495057",
                                "marginBottom": "8px",
                            },
                        ),
                        dcc.Graph(
                            figure=heatmap_fig,
                            config={"displayModeBar": False},
                            style={"height": "280px"},
                        ),
                    ],
                    className="p-3",
                )
            ),
            _build_divergence_table(chart_data["risk_table"]),
        ],
        className="mb-4",
    )


def _make_risk_heatmap(regions: list, z_matrix: list, time_periods: list) -> go.Figure:
    fig = go.Figure(
        go.Heatmap(
            z=z_matrix,
            x=time_periods,
            y=regions,
            colorscale=[[0, "#2E86AB"], [0.5, "#ffc107"], [1, "#E74C3C"]],
            showscale=True,
            colorbar=dict(title="Risk Score", tickfont=dict(size=10)),
            hovertemplate="<b>%{y}</b> - %{x}<br>Risk: %{z:.0f}<extra></extra>",
        )
    )
    fig.update_layout(
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(l=110, r=30, t=20, b=40),
        height=280,
        xaxis=dict(tickfont=dict(size=10), showgrid=False),
        yaxis=dict(tickfont=dict(size=10), showgrid=False),
    )
    return fig


def _build_divergence_table(risk_data: list) -> dbc.Card:
    rows = []
    for item in risk_data:
        risk_color = "#dc3545" if item["risk"] == "High" else "#ffc107"
        conf_color = (
            "#28a745"
            if item["confidence"] >= 75
            else "#ffc107" if item["confidence"] >= 65 else "#dc3545"
        )
        rows.append(
            html.Tr(
                [
                    html.Td(
                        item["region"],
                        style={"fontWeight": "600", "fontSize": "0.82rem"},
                    ),
                    html.Td(
                        item["risk"],
                        style={
                            "color": risk_color,
                            "fontWeight": "700",
                            "fontSize": "0.82rem",
                        },
                    ),
                    html.Td(
                        f"{item['confidence']}%",
                        style={
                            "color": conf_color,
                            "fontWeight": "600",
                            "fontSize": "0.82rem",
                        },
                    ),
                ]
            )
        )

    return dbc.Card(
        dbc.CardBody(
            [
                html.H6(
                    "Divergence Alert Panel",
                    style={
                        "fontSize": "0.75rem",
                        "fontWeight": "700",
                        "textTransform": "uppercase",
                        "letterSpacing": "0.5px",
                        "color": "#495057",
                        "marginBottom": "8px",
                    },
                ),
                html.Table(
                    [
                        html.Thead(
                            html.Tr(
                                [
                                    html.Th("Region", style={"fontSize": "0.72rem"}),
                                    html.Th(
                                        "Risk Level", style={"fontSize": "0.72rem"}
                                    ),
                                    html.Th(
                                        "Confidence", style={"fontSize": "0.72rem"}
                                    ),
                                ]
                            )
                        ),
                        html.Tbody(rows),
                    ],
                    className="table table-sm table-hover mb-0",
                ),
            ],
            className="p-3",
        ),
        className="mb-4",
    )
