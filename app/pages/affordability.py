"""Affordability Dashboard - Premium Edition (KPI 23-27)."""

import dash_bootstrap_components as dbc
from dash import dcc, html
import plotly.graph_objects as go

from app.components.cards import AffordabilityKPICard
from app.components.layout import create_section_header
from app.data.affordability_kpi_data import load_affordability_data
from app.utils.logger import get_logger

logger = get_logger(__name__)

ACCENT = {
    "years": "#2E86AB",
    "rent_burden": "#E74C3C",
    "ranking": "#8E44AD",
    "gap": "#D35400",
    "migration": "#148F77",
}


def create_affordability_dashboard():
    """Create Housing Affordability dashboard."""
    logger.info("Creating affordability dashboard")
    data = load_affordability_data()

    return dbc.Container(
        fluid=True,
        className="affordability-dashboard",
        children=[
            create_section_header(
                "Housing Affordability Dashboard",
                "Premium Edition — KPIs 23-27: Years to Buy, Rent Burden, Ranking, Gap & Migration",
            ),
            _build_hero_row(data["hero_kpis"]),
            _build_ranking_section(data["chart_data"]),
            _build_middle_charts(data["chart_data"]),
            _build_heatmap_section(data["chart_data"]),
            dcc.Store(id="affordability-kpis-data", data=data),
            dcc.Store(
                id="affordability-filter-state",
                data={"timeframe": "12M", "region": "All"},
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
                        AffordabilityKPICard.create_years_to_buy_card(
                            **kpis["years_to_buy"]
                        ),
                        width=12,
                        lg=4,
                    ),
                    dbc.Col(
                        AffordabilityKPICard.create_rent_burden_card(
                            **kpis["rent_burden"]
                        ),
                        width=12,
                        lg=4,
                    ),
                    dbc.Col(
                        AffordabilityKPICard.create_ranking_card(**kpis["ranking"]),
                        width=12,
                        lg=4,
                    ),
                ],
                className="g-3 mb-3",
            ),
            dbc.Row(
                [
                    dbc.Col(
                        AffordabilityKPICard.create_gap_card(
                            **kpis["demographics_gap"]
                        ),
                        width=12,
                        lg=6,
                    ),
                    dbc.Col(
                        AffordabilityKPICard.create_migration_card(
                            **kpis["net_migration"]
                        ),
                        width=12,
                        lg=6,
                    ),
                ],
                className="g-3",
            ),
        ],
        className="mb-4",
    )


def _build_ranking_section(chart_data: dict) -> html.Div:
    ranking_fig = _make_ranking_chart(chart_data["ranking_bar"])
    rent_burden_fig = _make_rent_burden_chart(chart_data["rent_burden_bar"])

    return html.Div(
        [
            html.H5(
                "Affordability Comparison",
                style={
                    "fontSize": "0.85rem",
                    "fontWeight": "800",
                    "textTransform": "uppercase",
                    "letterSpacing": "0.5px",
                    "color": "#12263A",
                    "borderLeft": "4px solid " + ACCENT["years"],
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
                                        "Affordability Ranking by Region (1=Most Affordable)",
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
                                        figure=ranking_fig,
                                        config={"displayModeBar": False},
                                        style={"height": "320px"},
                                    ),
                                ]
                            ),
                            className="p-3",
                        ),
                        className="col-12 col-lg-7",
                    ),
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(
                                [
                                    html.H6(
                                        "Rent Burden Distribution Across Regions",
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
                                        figure=rent_burden_fig,
                                        config={"displayModeBar": False},
                                        style={"height": "320px"},
                                    ),
                                ]
                            ),
                            className="p-3",
                        ),
                        className="col-12 col-lg-5",
                    ),
                ],
                className="g-3 mb-4",
            ),
        ]
    )


def _make_ranking_chart(data: list) -> go.Figure:
    colors = [
        "#28a745" if r["rank"] <= 4 else "#ffc107" if r["rank"] <= 10 else "#e74c3c"
        for r in data
    ]
    fig = go.Figure(
        go.Bar(
            x=[r["rank"] for r in data],
            y=[r["region"] for r in data],
            orientation="h",
            marker=dict(color=colors),
            text=[f"#{r['rank']}" for r in data],
            textposition="inside",
            hovertemplate="<b>%{y}</b><br>Rank: %{x} | Years: %{customdata}<extra></extra>",
        )
    )
    fig.update_layout(
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(l=120, r=30, t=20, b=40),
        height=320,
        xaxis=dict(
            title="Rank (1=Best)",
            dtick=1,
            showgrid=True,
            gridcolor="rgba(0,0,0,0.05)",
            tickfont=dict(size=10),
        ),
        yaxis=dict(title="", tickfont=dict(size=11), gridcolor="rgba(0,0,0,0.05)"),
        showlegend=False,
    )
    return fig


def _make_rent_burden_chart(data: list) -> go.Figure:
    colors = [
        "#dc3545" if d["burden"] > 35 else "#ffc107" if d["burden"] > 28 else "#28a745"
        for d in data
    ]
    fig = go.Figure(
        go.Bar(
            x=[d["burden"] for d in data],
            y=[d["region"] for d in data],
            orientation="h",
            marker=dict(color=colors),
            text=[f"{d['burden']:.0f}%" for d in data],
            textposition="outside",
            hovertemplate="<b>%{y}</b><br>Rent Burden: %{x:.0f}%<extra></extra>",
        )
    )
    fig.update_layout(
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(l=100, r=50, t=20, b=40),
        height=320,
        xaxis=dict(
            title="Rent Burden (%)",
            showgrid=True,
            gridcolor="rgba(0,0,0,0.05)",
            tickfont=dict(size=10),
        ),
        yaxis=dict(title="", tickfont=dict(size=10), gridcolor="rgba(0,0,0,0.05)"),
        showlegend=False,
    )
    return fig


def _build_middle_charts(chart_data: dict) -> html.Div:
    scatter_fig = _make_income_price_scatter(chart_data["scatter"])
    demo_fig = _make_demo_ts(chart_data["demo_ts"])
    migration_fig = _make_migration_chart(chart_data["migration_bar"])

    return html.Div(
        [
            html.H5(
                "Drivers of Affordability",
                style={
                    "fontSize": "0.85rem",
                    "fontWeight": "800",
                    "textTransform": "uppercase",
                    "letterSpacing": "0.5px",
                    "color": "#12263A",
                    "borderLeft": "4px solid " + ACCENT["gap"],
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
                                        "Income vs House Price by Region",
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
                                        figure=scatter_fig,
                                        config={"displayModeBar": False},
                                        style={"height": "260px"},
                                    ),
                                ]
                            ),
                            className="p-3",
                        ),
                        className="col-12 col-lg-4",
                    ),
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(
                                [
                                    html.H6(
                                        "Population vs Housing Supply Growth",
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
                                        figure=demo_fig,
                                        config={"displayModeBar": False},
                                        style={"height": "260px"},
                                    ),
                                ]
                            ),
                            className="p-3",
                        ),
                        className="col-12 col-lg-4",
                    ),
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(
                                [
                                    html.H6(
                                        "Net Internal Migration by Region",
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
                                        figure=migration_fig,
                                        config={"displayModeBar": False},
                                        style={"height": "260px"},
                                    ),
                                ]
                            ),
                            className="p-3",
                        ),
                        className="col-12 col-lg-4",
                    ),
                ],
                className="g-3 mb-4",
            ),
        ]
    )


def _make_income_price_scatter(data: list) -> go.Figure:
    fig = go.Figure()
    for d in data:
        fig.add_trace(
            go.Scatter(
                x=[d["income"]],
                y=[d["price"]],
                mode="markers+text",
                marker=dict(
                    size=14, color=ACCENT["years"], line=dict(color="white", width=1.5)
                ),
                text=[d["region"]],
                textposition="top right",
                textfont=dict(size=9),
                hovertemplate=f"<b>{d['region']}</b><br>Income: ${d['income']:,}<br>Price: ${d['price']:,}<extra></extra>",
            )
        )
    max_income = max(d["income"] for d in data)
    max_price = max(d["price"] for d in data)
    fig.add_trace(
        go.Scatter(
            x=[0, max_income],
            y=[0, max_price],
            mode="lines",
            line=dict(color="#dee2e6", width=2, dash="dash"),
            showlegend=False,
        )
    )
    fig.update_layout(
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(l=50, r=20, t=20, b=50),
        xaxis=dict(
            title="Median Income (NZD)",
            showgrid=True,
            gridcolor="rgba(0,0,0,0.05)",
            tickfont=dict(size=10),
        ),
        yaxis=dict(
            title="House Price (NZD)",
            showgrid=True,
            gridcolor="rgba(0,0,0,0.05)",
            tickfont=dict(size=10),
        ),
    )
    return fig


def _make_demo_ts(data: dict) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=data["months"],
            y=data["population"],
            mode="lines",
            name="Population Growth",
            line=dict(color=ACCENT["gap"], width=2.5),
            fill="tozeroy",
            fillcolor="rgba(211,84,0,0.2)",
            hovertemplate="<b>%{x}</b><br>Pop Growth: %{y:.1f}%<extra></extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=data["months"],
            y=data["housing_supply"],
            mode="lines",
            name="Housing Supply",
            line=dict(color=ACCENT["years"], width=2.5),
            fill="tozeroy",
            fillcolor="rgba(46,134,171,0.2)",
            hovertemplate="<b>%{x}</b><br>Housing: %{y:.1f}%<extra></extra>",
        )
    )
    fig.update_layout(
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(l=50, r=20, t=20, b=40),
        legend=dict(orientation="h", y=1.12, x=0.5, xanchor="center"),
        xaxis=dict(showgrid=True, gridcolor="rgba(0,0,0,0.05)", tickfont=dict(size=10)),
        yaxis=dict(
            title="% Growth",
            showgrid=True,
            gridcolor="rgba(0,0,0,0.05)",
            tickfont=dict(size=10),
        ),
        hovermode="x unified",
    )
    return fig


def _make_migration_chart(data: list) -> go.Figure:
    colors = [
        ACCENT["migration"] if v > 0 else "#dc3545" for v in [d["value"] for d in data]
    ]
    fig = go.Figure(
        go.Bar(
            x=[d["value"] for d in data],
            y=[d["region"] for d in data],
            orientation="h",
            marker=dict(color=colors),
            text=[
                f"+{d['value']:,}" if d["value"] > 0 else f"{d['value']:,}"
                for d in data
            ],
            textposition="outside",
            hovertemplate="<b>%{y}</b><br>Net: %{text}<extra></extra>",
        )
    )
    fig.update_layout(
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(l=100, r=60, t=20, b=40),
        height=260,
        xaxis=dict(
            title="Net Migration (people/yr)",
            showgrid=True,
            gridcolor="rgba(0,0,0,0.05)",
            tickfont=dict(size=10),
        ),
        yaxis=dict(title="", tickfont=dict(size=10), gridcolor="rgba(0,0,0,0.05)"),
        showlegend=False,
    )
    return fig


def _build_heatmap_section(chart_data: dict) -> html.Div:
    heatmap_fig = _make_affordability_heatmap(
        chart_data["regions"], chart_data["heatmap_z"], chart_data["heatmap_months"]
    )
    risk_data = chart_data["ranking_bar"]

    return html.Div(
        [
            html.H5(
                "Affordability Pressure Heatmap",
                style={
                    "fontSize": "0.85rem",
                    "fontWeight": "800",
                    "textTransform": "uppercase",
                    "letterSpacing": "0.5px",
                    "color": "#12263A",
                    "borderLeft": "4px solid " + ACCENT["rent_burden"],
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
                                        "Affordability Score by Region × Time",
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
                                        style={"height": "320px"},
                                    ),
                                ]
                            ),
                            className="p-3",
                        ),
                        className="col-12 col-lg-8",
                    ),
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(
                                [
                                    html.H6(
                                        "Affordability Risk Indicator",
                                        style={
                                            "fontSize": "0.75rem",
                                            "fontWeight": "700",
                                            "textTransform": "uppercase",
                                            "letterSpacing": "0.5px",
                                            "color": "#495057",
                                            "marginBottom": "10px",
                                        },
                                    ),
                                    _make_risk_indicator(risk_data),
                                ]
                            ),
                            className="p-3",
                        ),
                        className="col-12 col-lg-4",
                    ),
                ],
                className="g-3 mb-4",
            ),
        ]
    )


def _make_affordability_heatmap(
    regions: list, z_matrix: list, time_periods: list
) -> go.Figure:
    fig = go.Figure(
        go.Heatmap(
            z=z_matrix,
            x=time_periods,
            y=regions,
            colorscale=[[0, "#28a745"], [0.5, "#ffc107"], [1, "#dc3545"]],
            showscale=True,
            colorbar=dict(title="Affordability Score", tickfont=dict(size=10)),
            hovertemplate="<b>%{y}</b> - %{x}<br>Score: %{z:.0f}<extra></extra>",
        )
    )
    fig.update_layout(
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(l=120, r=30, t=20, b=40),
        height=320,
        xaxis=dict(tickfont=dict(size=10), showgrid=False),
        yaxis=dict(tickfont=dict(size=10), showgrid=False),
    )
    return fig


def _make_risk_indicator(ranking_data: list) -> html.Div:
    high_risk = [r for r in ranking_data if r["rank"] >= 12]
    moderate_risk = [r for r in ranking_data if 7 <= r["rank"] < 12]
    low_risk = [r for r in ranking_data if r["rank"] < 7]

    def risk_group(items: list, color: str, label: str) -> html.Div:
        regions_list = ", ".join([r["region"] for r in items[:4]])
        if len(items) > 4:
            regions_list += f" +{len(items) - 4} more"
        return html.Div(
            [
                html.Div(
                    label,
                    style={
                        "fontSize": "0.7rem",
                        "fontWeight": "700",
                        "color": color,
                        "textTransform": "uppercase",
                        "marginBottom": "4px",
                    },
                ),
                html.Div(
                    regions_list,
                    style={
                        "fontSize": "0.72rem",
                        "color": "#495057",
                        "lineHeight": "1.4",
                    },
                ),
            ],
            className="mb-3",
        )

    return html.Div(
        [
            risk_group(high_risk, "#dc3545", "High Risk"),
            risk_group(moderate_risk, "#ffc107", "Moderate"),
            risk_group(low_risk, "#28a745", "Low Risk"),
        ]
    )
