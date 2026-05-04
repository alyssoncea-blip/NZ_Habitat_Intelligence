"""Macroeconomic Dashboard - Premium Edition (KPI 18-22)."""

import dash_bootstrap_components as dbc
from dash import dcc, html
import plotly.graph_objects as go

from app.components.cards import MacroKPICard
from app.components.layout import create_section_header
from app.data.macro_kpi_data import load_macro_data
from app.utils.logger import get_logger

logger = get_logger(__name__)

ACCENT = {
    "ocr": "#1A5276",
    "mortgage": "#2E86AB",
    "cost": "#148F77",
    "construction": "#D35400",
    "correlation": "#8E44AD",
}


def create_macro_dashboard():
    """Create Macroeconomic dashboard."""
    logger.info("Creating macro dashboard")
    data = load_macro_data()

    return dbc.Container(
        fluid=True,
        className="macro-dashboard",
        children=[
            create_section_header(
                "Macroeconomic Dashboard",
                "Premium Edition — KPIs 18-22: OCR, Mortgage Rates, Construction Employment & Correlation",
            ),
            _build_hero_row(data["hero_kpis"]),
            _build_ocr_timeline(data["chart_data"]),
            _build_mortgage_section(data),
            _build_middle_charts(data["chart_data"]),
            _build_correlation_section(data["chart_data"]),
            dcc.Store(id="macro-kpis-data", data=data),
            dcc.Store(id="macro-filter-state", data={"timeframe": "12M", "region": "All"}),
        ],
    )


def _build_hero_row(hero_kpis: dict) -> html.Div:
    kpis = hero_kpis
    return html.Div([
        dbc.Row([
            dbc.Col(MacroKPICard.create_ocr_card(**kpis["ocr"]), width=12, lg=4),
            dbc.Col(MacroKPICard.create_mortgage_rates_card(**kpis["mortgage_rates"]), width=12, lg=4),
            dbc.Col(MacroKPICard.create_mortgage_cost_card(**kpis["mortgage_cost"]), width=12, lg=4),
        ], className="g-2 mb-2"),
        dbc.Row([
            dbc.Col(MacroKPICard.create_construction_card(**kpis["construction"]), width=12, lg=6),
            dbc.Col(MacroKPICard.create_ocr_listings_corr_card(**kpis["ocr_listings_corr"]), width=12, lg=6),
        ], className="g-2"),
    ], className="mb-3")


def _build_ocr_timeline(chart_data: dict) -> html.Div:
    ocr = chart_data["ocr_timeline"]
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=ocr["months"], y=ocr["values"],
        mode="lines",
        line=dict(color=ACCENT["ocr"], width=2.5),
        fill="tozeroy",
        fillcolor="rgba(26,82,118,0.2)",
        hovertemplate="<b>%{x}</b><br>OCR: %{y:.2f}%<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=[ocr["months"][-1]], y=[ocr["current"]],
        mode="markers+text",
        marker=dict(size=14, color=ACCENT["ocr"], line=dict(color="white", width=2)),
        text=[f"{ocr['current']:.2f}%"],
        textposition="top right",
        textfont=dict(size=12, color=ACCENT["ocr"]),
        showlegend=False,
    ))
    fig.update_layout(
        plot_bgcolor="white", paper_bgcolor="white",
        margin=dict(l=50, r=80, t=20, b=40),
        height=220,
        xaxis=dict(showgrid=True, gridcolor="rgba(0,0,0,0.05)", tickfont=dict(size=10), dtick=6),
        yaxis=dict(title="OCR %", showgrid=True, gridcolor="rgba(0,0,0,0.05)", tickfont=dict(size=10)),
        hovermode="x unified",
    )
    return dbc.Card(dbc.CardBody([
        html.H6("OCR Historical Timeline", style={
            "fontSize": "0.75rem", "fontWeight": "700", "textTransform": "uppercase",
            "letterSpacing": "0.5px", "color": "#495057", "marginBottom": "8px",
        }),
        dcc.Graph(figure=fig, config={"displayModeBar": False}, style={"height": "220px"}),
        html.Div([
            html.Span("Next RBNZ decision: ", style={"fontSize": "0.68rem", "color": "#8898aa"}),
            html.Span(ocr["decision_date"], style={"fontSize": "0.72rem", "fontWeight": "700", "color": ACCENT["ocr"]}),
        ], className="text-end mt-1"),
    ], className="p-3"), className="mb-3")


def _build_mortgage_section(data: dict) -> html.Div:
    chart = data["chart_data"]
    suburbs = chart["mortgage_by_suburb"]["suburbs"]
    costs = chart["mortgage_by_suburb"]["costs"]

    yield_curve_fig = _make_yield_curve_chart(chart["mortgage_ts"])
    suburb_fig = _make_suburb_cost_chart(suburbs, costs)

    return html.Div([
        dbc.Row([
            dbc.Col(dbc.Card(dbc.CardBody([
                html.H6("Mortgage Yield Curve (Current vs 3M Ago)", style={
                    "fontSize": "0.75rem", "fontWeight": "700", "textTransform": "uppercase",
                    "letterSpacing": "0.5px", "color": "#495057", "marginBottom": "8px",
                }),
                dcc.Graph(figure=yield_curve_fig, config={"displayModeBar": False}, style={"height": "220px"}),
            ]), className="p-3"), className="col-12 col-lg-6"),
            dbc.Col(dbc.Card(dbc.CardBody([
                html.H6("Monthly Mortgage Cost by Suburb ($750K, 2Y)", style={
                    "fontSize": "0.75rem", "fontWeight": "700", "textTransform": "uppercase",
                    "letterSpacing": "0.5px", "color": "#495057", "marginBottom": "8px",
                }),
                dcc.Graph(figure=suburb_fig, config={"displayModeBar": False}, style={"height": "220px"}),
            ]), className="p-3"), className="col-12 col-lg-6"),
        ], className="g-2 mb-3"),
    ])


def _make_yield_curve_chart(ts: dict) -> go.Figure:
    terms = ["1Y", "2Y", "5Y"]
    current = [ts["1Y"][-1], ts["2Y"][-1], ts["5Y"][-1]]
    prev = [ts["1Y"][-4], ts["2Y"][-4], ts["5Y"][-4]]
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=terms, y=current, mode="lines+markers+text",
        name="Current",
        line=dict(color=ACCENT["mortgage"], width=3),
        marker=dict(size=10),
        text=[f"{v:.2f}%" for v in current],
        textposition="top center",
        hovertemplate="<b>Current %{x}</b><br>%{y:.2f}%<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=terms, y=prev, mode="lines+markers",
        name="3 Months Ago",
        line=dict(color="#adb5bd", width=2, dash="dot"),
        marker=dict(size=8),
        hovertemplate="<b>3M Ago %{x}</b><br>%{y:.2f}%<extra></extra>",
    ))
    fig.update_layout(
        plot_bgcolor="white", paper_bgcolor="white",
        margin=dict(l=50, r=30, t=20, b=40),
        legend=dict(orientation="h", y=1.12, x=0.5, xanchor="center"),
        xaxis=dict(title="Term", showgrid=True, gridcolor="rgba(0,0,0,0.05)", tickfont=dict(size=11)),
        yaxis=dict(title="Rate %", showgrid=True, gridcolor="rgba(0,0,0,0.05)", tickfont=dict(size=10)),
    )
    return fig


def _make_suburb_cost_chart(suburbs: list, costs: list) -> go.Figure:
    sorted_data = sorted(zip(suburbs, costs), key=lambda x: x[1], reverse=True)
    s, c = zip(*sorted_data)
    colors = [ACCENT["cost"] if v > 4500 else "#adb5bd" for v in c]
    fig = go.Figure(go.Bar(
        x=list(c), y=list(s),
        orientation="h",
        marker=dict(color=list(c), colorscale=[[0, "#dee2e6"], [1, ACCENT["cost"]]]),
        text=[f"${v:,}" for v in c],
        textposition="outside",
        hovertemplate="<b>%{y}</b><br>$%{x:,}<extra></extra>",
    ))
    fig.update_layout(
        plot_bgcolor="white", paper_bgcolor="white",
        margin=dict(l=80, r=60, t=20, b=40),
        height=220,
        xaxis=dict(title="Monthly Cost (NZD)", showgrid=True, gridcolor="rgba(0,0,0,0.05)", tickfont=dict(size=9)),
        yaxis=dict(title="", tickfont=dict(size=10), gridcolor="rgba(0,0,0,0.05)"),
        showlegend=False,
    )
    return fig


def _build_middle_charts(chart_data: dict) -> html.Div:
    cost_trend_fig = _make_cost_trend_chart(chart_data["mortgage_cost_trend"])
    constr_trend_fig = _make_construction_trend_chart(chart_data["construction_trend"])
    scatter_fig = _make_ocr_listings_scatter(chart_data["ocr_listings_scatter"])

    return html.Div([
        dbc.Row([
            dbc.Col(dbc.Card(dbc.CardBody([
                html.H6("Mortgage Cost Trend (12 Months)", style={
                    "fontSize": "0.75rem", "fontWeight": "700", "textTransform": "uppercase",
                    "letterSpacing": "0.5px", "color": "#495057", "marginBottom": "8px",
                }),
                dcc.Graph(figure=cost_trend_fig, config={"displayModeBar": False}, style={"height": "200px"}),
            ]), className="p-3"), className="col-12 col-lg-4"),
            dbc.Col(dbc.Card(dbc.CardBody([
                html.H6("Construction Employment Trend", style={
                    "fontSize": "0.75rem", "fontWeight": "700", "textTransform": "uppercase",
                    "letterSpacing": "0.5px", "color": "#495057", "marginBottom": "8px",
                }),
                dcc.Graph(figure=constr_trend_fig, config={"displayModeBar": False}, style={"height": "200px"}),
            ]), className="p-3"), className="col-12 col-lg-4"),
            dbc.Col(dbc.Card(dbc.CardBody([
                html.H6("OCR (Lagged) vs Listings Volume", style={
                    "fontSize": "0.75rem", "fontWeight": "700", "textTransform": "uppercase",
                    "letterSpacing": "0.5px", "color": "#495057", "marginBottom": "8px",
                }),
                dcc.Graph(figure=scatter_fig, config={"displayModeBar": False}, style={"height": "200px"}),
            ]), className="p-3"), className="col-12 col-lg-4"),
        ], className="g-2 mb-3"),
    ])


def _make_cost_trend_chart(data: dict) -> go.Figure:
    fig = go.Figure(go.Scatter(
        x=data["months"], y=data["values"],
        mode="lines", fill="tozeroy",
        fillcolor="rgba(20,143,119,0.2)",
        line=dict(color=ACCENT["cost"], width=2),
        hovertemplate="<b>%{x}</b><br>$%{y:,}<extra></extra>",
    ))
    fig.update_layout(
        plot_bgcolor="white", paper_bgcolor="white",
        margin=dict(l=40, r=20, t=20, b=40),
        xaxis=dict(showgrid=True, gridcolor="rgba(0,0,0,0.05)", tickfont=dict(size=9)),
        yaxis=dict(showgrid=True, gridcolor="rgba(0,0,0,0.05)", tickfont=dict(size=9)),
        hovermode="x unified",
    )
    return fig


def _make_construction_trend_chart(data: dict) -> go.Figure:
    fig = go.Figure(go.Scatter(
        x=data["months"], y=data["values"],
        mode="lines", fill="tozeroy",
        fillcolor="rgba(211,84,0,0.2)",
        line=dict(color=ACCENT["construction"], width=2),
        hovertemplate="<b>%{x}</b><br>%{y:.1f}%<extra></extra>",
    ))
    fig.update_layout(
        plot_bgcolor="white", paper_bgcolor="white",
        margin=dict(l=40, r=20, t=20, b=40),
        xaxis=dict(showgrid=True, gridcolor="rgba(0,0,0,0.05)", tickfont=dict(size=9)),
        yaxis=dict(showgrid=True, gridcolor="rgba(0,0,0,0.05)", tickfont=dict(size=9)),
        hovermode="x unified",
    )
    return fig


def _make_ocr_listings_scatter(scatter_data: list) -> go.Figure:
    fig = go.Figure()
    for d in scatter_data:
        fig.add_trace(go.Scatter(
            x=[d["ocr"]], y=[d["listings"]],
            mode="markers+text",
            marker=dict(size=12, color=ACCENT["ocr"], line=dict(color="white", width=1.5)),
            text=[d["label"]],
            textposition="top center",
            textfont=dict(size=9),
            hovertemplate=f"<b>{d['label']}</b><br>OCR: {d['ocr']:.2f}%<br>Listings: {d['listings']:,}<extra></extra>",
        ))
    z = np.polyfit([d["ocr"] for d in scatter_data], [d["listings"] for d in scatter_data], 1)
    p = np.poly1d(z)
    x_range = np.linspace(min(d["ocr"] for d in scatter_data), max(d["ocr"] for d in scatter_data), 50)
    fig.add_trace(go.Scatter(
        x=x_range, y=p(x_range),
        mode="lines", line=dict(color="#dc3545", width=2, dash="dash"),
        showlegend=False,
    ))
    fig.update_layout(
        plot_bgcolor="white", paper_bgcolor="white",
        margin=dict(l=50, r=20, t=20, b=50),
        xaxis=dict(title="Lagged OCR %", showgrid=True, gridcolor="rgba(0,0,0,0.05)", tickfont=dict(size=9)),
        yaxis=dict(title="Listings", showgrid=True, gridcolor="rgba(0,0,0,0.05)", tickfont=dict(size=9)),
    )
    return fig


def _build_correlation_section(chart_data: dict) -> html.Div:
    matrix_fig = _make_correlation_matrix(chart_data["correlation_matrix"], chart_data["matrix_variables"])
    lag = chart_data["lag_indicator"]

    return html.Div([
        html.H5("Macro Correlation & Signals", style={
            "fontSize": "0.85rem", "fontWeight": "800", "textTransform": "uppercase",
            "letterSpacing": "0.5px", "color": "#12263A", "borderLeft": "4px solid " + ACCENT["correlation"],
            "paddingLeft": "10px", "marginBottom": "10px",
        }),
        dbc.Row([
            dbc.Col(dbc.Card(dbc.CardBody([
                html.H6("Correlation Matrix (6 Variables)", style={
                    "fontSize": "0.75rem", "fontWeight": "700", "textTransform": "uppercase",
                    "letterSpacing": "0.5px", "color": "#495057", "marginBottom": "8px",
                }),
                dcc.Graph(figure=matrix_fig, config={"displayModeBar": False}, style={"height": "280px"}),
            ]), className="p-3"), className="col-12 col-lg-7"),
            dbc.Col(dbc.Card(dbc.CardBody([
                html.H6("Lag Impact Indicator", style={
                    "fontSize": "0.75rem", "fontWeight": "700", "textTransform": "uppercase",
                    "letterSpacing": "0.5px", "color": "#495057", "marginBottom": "10px",
                }),
                _make_lag_indicator(lag),
                html.Hr(),
                html.Div([
                    html.Span("Key signal: ", style={"fontSize": "0.68rem", "color": "#8898aa"}),
                    html.Span("OCR cut → listings increase after 3-6 months",
                              style={"fontSize": "0.75rem", "fontWeight": "600", "color": ACCENT["correlation"]}),
                ], className="mt-3"),
            ]), className="p-3"), className="col-12 col-lg-5"),
        ], className="g-2"),
    ], className="mb-3")


def _make_correlation_matrix(matrix: dict, variables: list) -> go.Figure:
    z_values = [[matrix[v][k] for k in variables] for v in variables]
    text_values = [[f"{matrix[v][k]:.2f}" for k in variables] for v in variables]

    def corr_color(v: float) -> str:
        if v == 1.00:
            return "#495057"
        if v >= 0.7:
            return "#28a745"
        if v >= 0.4:
            return "#a8d5ba"
        if v >= 0.1:
            return "#f8f9fa"
        if v >= -0.1:
            return "#f8f9fa"
        if v >= -0.4:
            return "#f5b7b1"
        return "#e74c3c"

    colors = [[corr_color(v) for v in row] for row in z_values]

    fig = go.Figure(go.Heatmap(
        z=z_values,
        x=variables,
        y=variables,
        text=text_values,
        texttemplate="%{text}",
        colorscale=[[0, "#28a745"], [0.5, "#f8f9fa"], [1, "#dc3545"]],
        showscale=True,
        colorbar=dict(title="Correlation", tickfont=dict(size=10)),
        hovertemplate="<b>%{x}</b> × <b>%{y}</b><br>%{z:.2f}<extra></extra>",
    ))
    fig.update_layout(
        plot_bgcolor="white", paper_bgcolor="white",
        margin=dict(l=100, r=30, t=20, b=40),
        height=280,
        xaxis=dict(tickfont=dict(size=10), showgrid=False),
        yaxis=dict(tickfont=dict(size=10), showgrid=False, autorange="reversed"),
    )
    return fig


def _make_lag_indicator(lag_data: dict) -> html.Div:
    steps = lag_data["steps"]
    colors = lag_data["colors"]

    step_elems = []
    for i, (step, color) in enumerate(zip(steps, colors)):
        step_elems.append(html.Div([
            html.Div(step, style={
                "minWidth": "70px", "textAlign": "center",
                "fontSize": "0.72rem", "fontWeight": "600",
                "color": color, "background": color + "15",
                "padding": "4px 8px", "borderRadius": "4px",
            }),
        ], className="d-flex flex-column align-items-center"))
        if i < len(steps) - 1:
            step_elems.append(html.Div([
                html.Span("→", style={"fontSize": "0.9rem", "color": "#dee2e6"}),
                html.Span("+3m", style={"fontSize": "0.6rem", "color": "#adb5bd"}),
            ], className="d-flex flex-column align-items-center"))

    return html.Div(step_elems, className="d-flex flex-row align-items-center flex-wrap gap-2")


import numpy as np