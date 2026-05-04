"""Tourism Impact Dashboard page - Premium Edition."""

import dash_bootstrap_components as dbc
from dash import dcc, html, callback, Output, Input
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from app.components.cards import TourismKPICard, PremiumCard
from app.components.layout import create_section_header
from app.data.tourism_kpi_data import load_tourism_data
from app.utils.logger import get_logger

logger = get_logger(__name__)

ACCENT_COLORS = {
    "pressure": "#E74C3C",
    "airbnb": "#8E44AD",
    "lag": "#D35400",
    "seasonality": "#1A5276",
    "correlation": "#148F77",
}


def create_tourism_dashboard():
    """Create Tourism Impact dashboard."""
    logger.info("Creating tourism dashboard")
    data = load_tourism_data()

    return dbc.Container(
        fluid=True,
        className="tourism-dashboard",
        children=[
            create_section_header(
                "Tourism Impact Dashboard",
                "Premium Edition — KPIs 13–17: Tourism Pressure, Airbnb, Rent Lag, Seasonality & Correlation",
            ),
            _build_hero_row(data["hero_kpis"]),
            _build_analytics_section(data),
            _build_impact_section(data),
            _build_regional_breakdown(data),
        ],
    )


def _build_hero_row(hero_kpis: dict) -> html.Div:
    kpis = hero_kpis
    return html.Div([
        dbc.Row([
            dbc.Col(TourismKPICard.create_pressure_index_card(**kpis["pressure"]), width=12, lg=4),
            dbc.Col(TourismKPICard.create_airbnb_share_card(**kpis["airbnb_share"]), width=12, lg=4),
            dbc.Col(TourismKPICard.create_rent_lag_card(**kpis["rent_lag"]), width=12, lg=4),
        ], className="g-3 mb-3"),
        dbc.Row([
            dbc.Col(TourismKPICard.create_seasonality_card(**kpis["seasonality"]), width=12, lg=6),
            dbc.Col(TourismKPICard.create_dom_correlation_card(**kpis["correlation"]), width=12, lg=6),
        ], className="g-3"),
    ], className="mb-4")


def _build_analytics_section(data: dict) -> html.Div:
    chart_data = data["chart_data"]
    months = chart_data["dual_axis"]["months"]
    visitors = chart_data["dual_axis"]["visitors"]
    rent_index = chart_data["dual_axis"]["rent"]
    regions = data["regions"]

    dual_axis_fig = _make_dual_axis_chart(months, visitors, rent_index)
    seasonality_fig = _make_seasonality_chart(chart_data["seasonality_lines"])

    return html.Div([
        html.H5("📊 Tourism Analytics", className="section-title mb-3"),
        dbc.Row([
            dbc.Col(dbc.Card(dbc.CardBody([
                html.H6("Visitor Volume vs Rent Index", className="chart-title"),
                dcc.Graph(figure=dual_axis_fig, config={"displayModeBar": False}, style={"height": "260px"})
            ]), className="p-3"), className="col-12 col-lg-6"),
            dbc.Col(dbc.Card(dbc.CardBody([
                html.H6("Visitor Seasonality by Origin", className="chart-title"),
                dcc.Graph(figure=seasonality_fig, config={"displayModeBar": False}, style={"height": "260px"})
            ]), className="p-3"), className="col-12 col-lg-6"),
        ], className="g-3 mb-3"),
        _build_airbnb_bar_chart(chart_data["airbnb_bar"]),
    ], className="analytics-section mb-4")


def _build_airbnb_bar_chart(airbnb_bar_data: list) -> dbc.Card:
    fig = go.Figure(go.Bar(
        x=[d["airbnb_pct"] for d in airbnb_bar_data],
        y=[d["region"] for d in airbnb_bar_data],
        orientation="h",
        marker=dict(color=[ACCENT_COLORS["airbnb"] if v > 15 else "#a0aec0" for v in [d["airbnb_pct"] for d in airbnb_bar_data]]),
        text=[f"{d['airbnb_pct']:.1f}%" for d in airbnb_bar_data],
        textposition="outside",
        hovertemplate="<b>%{y}</b><br>%{x:.1f}%<extra></extra>",
    ))
    fig.update_layout(
        title=dict(text="Airbnb Share by Region (%)", font=dict(size=14), x=0.5),
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(l=80, r=30, t=40, b=40),
        height=280,
        xaxis=dict(title="", showgrid=True, gridcolor="rgba(0,0,0,0.05)"),
        yaxis=dict(title="", tickfont=dict(size=11), gridcolor="rgba(0,0,0,0.05)"),
        showlegend=False,
    )
    return dbc.Card(dbc.CardBody([
        dcc.Graph(figure=fig, config={"displayModeBar": False}, style={"height": "280px"})
    ], className="p-3"))


def _make_dual_axis_chart(months: list, visitors: list, rent_index: list) -> go.Figure:
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Bar(
        x=months, y=visitors, name="Visitors",
        marker_color="rgba(231,76,60,0.5)",
        marker_line=dict(color=ACCENT_COLORS["pressure"], width=1),
        hovertemplate="<b>Visitors</b><br>%{x}: %{y:,}<extra></extra>",
    ), secondary_y=False)
    fig.add_trace(go.Scatter(
        x=months, y=rent_index, name="Rent Index",
        mode="lines+markers",
        line=dict(color=ACCENT_COLORS["seasonality"], width=2.5),
        marker=dict(size=6),
        hovertemplate="<b>Rent Index</b><br>%{x}: %{y:.0f}<extra></extra>",
    ), secondary_y=True)
    fig.update_layout(
        plot_bgcolor="white", paper_bgcolor="white",
        margin=dict(l=50, r=50, t=20, b=30),
        legend=dict(orientation="h", y=1.12, x=0.5, xanchor="center"),
        xaxis=dict(showgrid=True, gridcolor="rgba(0,0,0,0.05)", tickfont=dict(size=10)),
        yaxis=dict(showgrid=True, gridcolor="rgba(0,0,0,0.05)", tickfont=dict(size=10)),
        hovermode="x unified",
    )
    fig.update_yaxes(title_text="Visitors", secondary_y=False, showgrid=True, gridcolor="rgba(0,0,0,0.05)")
    fig.update_yaxes(title_text="Rent Index", secondary_y=True, showgrid=False)
    return fig


def _make_seasonality_chart(seasonality: dict) -> go.Figure:
    origins_colors = {"Australia": "#28a745", "China": "#dc3545", "USA": "#2E86AB"}
    fig = go.Figure()
    for origin in ["Australia", "China", "USA"]:
        if origin in seasonality:
            fig.add_trace(go.Scatter(
                x=seasonality["months"], y=seasonality[origin],
                mode="lines+markers",
                name=origin,
                line=dict(color=origins_colors.get(origin, "#6c757d"), width=2),
                marker=dict(size=5),
                hovertemplate=f"<b>{{origin}}</b><br>%{{x}}: %{{y:.0f}}<extra></extra>",
            ))
    fig.update_layout(
        plot_bgcolor="white", paper_bgcolor="white",
        margin=dict(l=50, r=30, t=20, b=30),
        legend=dict(orientation="h", y=1.12, x=0.5, xanchor="center"),
        xaxis=dict(showgrid=True, gridcolor="rgba(0,0,0,0.05)", tickfont=dict(size=10)),
        yaxis=dict(title="Visitor Index", showgrid=True, gridcolor="rgba(0,0,0,0.05)", tickfont=dict(size=10)),
        hovermode="x unified",
    )
    return fig


def _build_impact_section(data: dict) -> html.Div:
    scatter_data = data["chart_data"]["scatter"]
    lag = data["chart_data"]["lag"]

    scatter_fig = _make_scatter_chart(scatter_data)
    lag_fig = _make_lag_indicator(lag)

    return html.Div([
        html.H5("🎯 Tourism Impact Analysis", className="section-title mb-3"),
        dbc.Row([
            dbc.Col(dbc.Card(dbc.CardBody([
                html.H6("Visitors vs Days on Market (by Region)", className="chart-title"),
                dcc.Graph(figure=scatter_fig, config={"displayModeBar": False}, style={"height": "260px"})
            ]), className="p-3"), className="col-12 col-lg-6"),
            dbc.Col(dbc.Card(dbc.CardBody([
                html.H6("Tourism → Rent Lag Indicator", className="chart-title"),
                lag_fig,
            ]), className="p-3"), className="col-12 col-lg-6"),
        ], className="g-3 mb-3"),
    ], className="impact-section mb-4")


def _make_scatter_chart(scatter_data: list) -> go.Figure:
    fig = go.Figure()
    color_map = {"high": "#E74C3C", "medium": "#ffc107", "low": "#28a745"}
    for d in scatter_data:
        pressure = d.get("pressure", 50)
        color = color_map["high"] if pressure > 70 else color_map["medium"] if pressure > 50 else color_map["low"]
        fig.add_trace(go.Scatter(
            x=[d["visitors"]], y=[d["dom"]],
            mode="markers+text",
            marker=dict(size=16, color=color, line=dict(color="white", width=1.5)),
            text=[d["region"]],
            textposition="top center",
            textfont=dict(size=10),
            hovertemplate=f"<b>{d['region']}</b><br>Visitors: {d['visitors']:,}<br>DOM: {d['dom']:.1f}<extra></extra>",
        ))
    fig.update_layout(
        plot_bgcolor="white", paper_bgcolor="white",
        margin=dict(l=50, r=30, t=30, b=50),
        xaxis=dict(title="Visitor Volume", showgrid=True, gridcolor="rgba(0,0,0,0.05)", tickfont=dict(size=10)),
        yaxis=dict(title="Days on Market", showgrid=True, gridcolor="rgba(0,0,0,0.05)", tickfont=dict(size=10)),
        hovermode="closest",
    )
    return fig


def _make_lag_indicator(lag: dict) -> html.Div:
    lag_months = lag.get("lag_months", 4)
    peak_month = lag.get("tourism_peak_month", "Jan")
    rent_month = lag.get("rent_increase_month", "May")

    timeline_steps = ["Tourism Peak", f"+{lag_months}m", "Rent Increase"]
    colors = [ACCENT_COLORS["pressure"], "#dee2e6", ACCENT_COLORS["lag"]]

    steps_html = []
    for i, step in enumerate(timeline_steps):
        color = colors[i]
        step_elems = [
            html.Div(style={
                "width": "36px", "height": "36px", "borderRadius": "50%",
                "background": color, "display": "flex", "alignItems": "center",
                "justifyContent": "center", "color": "white", "fontWeight": "700", "fontSize": "0.8rem"
            }, children=str(i) if i > 0 else "●"),
            html.Span(step, style={"fontSize": "0.8rem", "fontWeight": "600", "color": "#495057"}),
        ]
        if i < len(timeline_steps) - 1:
            step_elems.append(html.Div(style={
                "flex": "1", "height": "3px", "background": "#dee2e6", "margin": "0 8px"
            }))
        steps_html.append(html.Div(step_elems, className="d-flex align-items-center"))

    return html.Div([
        html.Div([
            html.Span(peak_month, style={"fontSize": "0.75rem", "color": ACCENT_COLORS["pressure"], "fontWeight": "600"}),
            html.Span(f" → +{lag_months} months → ", style={"fontSize": "0.75rem", "color": "#6c757d"}),
            html.Span(rent_month, style={"fontSize": "0.75rem", "color": ACCENT_COLORS["lag"], "fontWeight": "600"}),
        ], className="text-center mb-3"),
        html.Div(steps_html, className="d-flex align-items-center gap-2"),
        html.Div([
            html.Span("Average lag: ", style={"fontSize": "0.7rem", "color": "#8898aa"}),
            html.Span(f"{lag_months} months", style={"fontSize": "0.8rem", "fontWeight": "600", "color": ACCENT_COLORS["lag"]}),
            html.Span("  •  ", style={"fontSize": "0.7rem", "color": "#dee2e6"}),
            html.Span("Queens-4m fastest", style={"fontSize": "0.72rem", "color": "#28a745"}),
            html.Span("  •  ", style={"fontSize": "0.7rem", "color": "#dee2e6"}),
            html.Span("Dunedin-10m slowest", style={"fontSize": "0.72rem", "color": "#dc3545"}),
        ], className="text-center mt-2"),
    ], style={"padding": "10px 0"})


def _build_regional_breakdown(data: dict) -> html.Div:
    pressure = data["hero_kpis"]["pressure"]["by_region"]
    airbnb = data["hero_kpis"]["airbnb_share"]["by_region"]
    regions = data["regions"]

    heatmap_fig = _make_heatmap_figure(
        regions,
        data["chart_data"]["heatmap"]["z"],
        data["chart_data"]["heatmap"]["months"],
    )

    table_rows = []
    for region in sorted(regions, key=lambda r: pressure.get(r, 0), reverse=True):
        p_val = pressure.get(region, 0)
        a_val = airbnb.get(region, 0)
        color = "#E74C3C" if p_val > 70 else "#ffc107" if p_val > 50 else "#28a745"
        table_rows.append(html.Tr([
            html.Td(region, style={"fontWeight": "600", "fontSize": "0.85rem"}),
            html.Td(f"{p_val:.1f}", style={"color": color, "fontWeight": "700", "fontSize": "0.85rem"}),
            html.Td(f"{a_val:.1f}%", style={"color": ACCENT_COLORS["airbnb"], "fontWeight": "600", "fontSize": "0.85rem"}),
        ]))

    return html.Div([
        html.H5("🗺️ Regional Tourism Pressure", className="section-title mb-3"),
        dbc.Row([
            dbc.Col(dbc.Card(dbc.CardBody([
                html.H6("Pressure × Time Heatmap", className="chart-title"),
                dcc.Graph(figure=heatmap_fig, config={"displayModeBar": False}, style={"height": "300px"})
            ]), className="p-3"), className="col-12 col-lg-7"),
            dbc.Col(dbc.Card(dbc.CardBody([
                html.H6("Top Regions Summary", className="chart-title"),
                html.Table([
                    html.Thead(html.Tr([
                        html.Th("Region", style={"fontSize": "0.75rem"}),
                        html.Th("Pressure", style={"fontSize": "0.75rem"}),
                        html.Th("Airbnb", style={"fontSize": "0.75rem"}),
                    ])),
                    html.Tbody(table_rows[:8]),
                ], className="table table-sm table-hover mb-0")
            ]), className="p-3"), className="col-12 col-lg-5"),
        ], className="g-3"),
    ], className="regional-section mb-4")


def _make_heatmap_figure(regions: list, z_matrix: list, time_periods: list) -> go.Figure:
    fig = go.Figure(go.Heatmap(
        z=z_matrix,
        x=time_periods,
        y=regions,
        colorscale=[
            [0, "#28a745"], [0.5, "#ffc107"], [1, "#E74C3C"]
        ],
        showscale=True,
        colorbar=dict(title="Pressure", tickfont=dict(size=10)),
        hovertemplate="<b>%{y}</b> - %{x}<br>Pressure: %{z:.1f}<extra></extra>",
    ))
    fig.update_layout(
        plot_bgcolor="white", paper_bgcolor="white",
        margin=dict(l=100, r=30, t=20, b=40),
        height=300,
        xaxis=dict(tickfont=dict(size=10), showgrid=False),
        yaxis=dict(tickfont=dict(size=10), showgrid=False),
    )
    return fig