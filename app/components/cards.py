"""
Premium Card Components for Executive Dashboard
Reusable card components with executive design
"""
import dash_bootstrap_components as dbc
from dash import html
import numpy as np

from ..utils.style_config import COLORS, get_kpi_color
from ..utils.kpi_labels import to_executive_label

class PremiumCard:
    """Base class for premium dashboard cards"""
    
    @staticmethod
    def create_kpi_card(kpi_data):
        """Creates a premium KPI card with executive design"""
        name = kpi_data.get('name', '')
        display_name = to_executive_label(name)
        value = kpi_data.get('value', 0)
        unit = kpi_data.get('unit', '')
        description = kpi_data.get('description', '')
        category = kpi_data.get('category', 'general')
        source = kpi_data.get('source', 'Unknown')
        display_value = format_value_for_card(value)
        
        # Determines status and color based on value
        status, color = get_kpi_color(name, value, category)
        
        return dbc.Card(
            [
                dbc.CardHeader([
                    html.H5(display_name, className="kpi-card-title", title=f"Technical KPI: {name}"),
                    html.Small(f"Source: {source}", className="kpi-source")
                ]),
                dbc.CardBody([
                    html.Div([
                        html.Span(display_value, className="kpi-value"),
                        html.Span(unit, className="kpi-unit")
                    ], className="kpi-display"),
                    
                    html.Div(status, className="kpi-status", style={"color": color}),
                    
                    html.P(description, className="kpi-description"),
                    
                    # Progress bar for context
                    html.Div([
                        html.Div(
                            className="kpi-progress",
                            style={
                                "width": f"{calculate_percentage(value, name)}%",
                                "backgroundColor": color,
                                "height": "6px",
                                "borderRadius": "3px"
                            }
                        )
                    ], className="kpi-progress-container")
                ])
            ],
            className="kpi-card premium-card",
            style={"borderLeft": f"4px solid {color}"}
        )
    
    @staticmethod
    def create_info_card(title, content, icon='ℹ️', color='#17a2b8'):
        """Creates an informative card with icon"""
        return dbc.Card(
            [
                dbc.CardHeader([
                    html.Span(icon, style={"marginRight": "8px", "fontSize": "1.2em"}),
                    html.H6(title, style={"display": "inline"})
                ]),
                dbc.CardBody([
                    html.P(content, className="card-text")
                ])
            ],
            className="info-card",
            style={"borderLeft": f"4px solid {color}"}
        )

class HeroKPICard:
    """Special card for hero KPIs (main indicators)"""
    
    @staticmethod
    def create(title, value, unit, description, status, color, confidence=None):
        """Creates a hero card for main KPI"""
        display_value = format_value_for_card(value)
        children = [
            html.H4(title, className="hero-card-title"),
            html.Div([
                html.Span(display_value, className="hero-value"),
                html.Span(unit, className="hero-unit")
            ], className="hero-display"),
            html.Div(status, className="hero-status", style={"color": color})
        ]
        
        if confidence:
            children.append(
                html.Div(f"Confidence: {confidence}%", className="hero-confidence")
            )
        
        if description:
            children.append(
                html.P(description, className="hero-description")
            )
        
        return dbc.Card(
            dbc.CardBody(children),
            className="hero-kpi-card",
            style={
                "borderLeft": f"5px solid {color}",
                "background": f"linear-gradient(135deg, {color}15 0%, {color}05 100%)"
            }
        )

def create_dashboard_stats(stats_data):
    """Creates a row of dashboard statistics"""
    stats_cards = []
    
    for stat in stats_data:
        title = stat.get('title', '')
        value = stat.get('value', 0)
        unit = stat.get('unit', '')
        trend = stat.get('trend', None)
        
        trend_icon = "→"
        trend_class = "neutral"
        if trend == "up":
            trend_icon = "↑"
            trend_class = "positive"
        elif trend == "down":
            trend_icon = "↓"
            trend_class = "negative"
        
        stat_card = dbc.Col(
            dbc.Card([
                dbc.CardBody([
                    html.Small(title, className="stat-title"),
                    html.Div([
                        html.Span(value, className="stat-value"),
                        html.Span(unit, className="stat-unit"),
                        html.Span(trend_icon, className=f"stat-trend {trend_class}")
                    ], className="stat-display")
                ])
            ], className="stat-card"),
            width=2
        )
        stats_cards.append(stat_card)
    
    return dbc.Row(stats_cards, className="dashboard-stats", justify="between")

def calculate_percentage(value, kpi_name):
    """Calculates percentage base for progress bar based on KPI"""
    # Simplified logic - real implementation depends on KPI ranges
    try:
        numeric_value = float(value)
    except (TypeError, ValueError):
        return 0

    if "%" in str(kpi_name).lower() or "rate" in str(kpi_name).lower():
        return min(numeric_value, 100)
    if "score" in str(kpi_name).lower() or "index" in str(kpi_name).lower():
        return min(max(numeric_value, 0), 100)
    if "deficit" in str(kpi_name).lower() or "gap" in str(kpi_name).lower():
        return min(numeric_value * 10, 100)
    return min(max(numeric_value, 0), 100)


def format_value_for_card(value):
    """Format card value safely for display."""
    try:
        if value is None:
            return "N/A"
        if isinstance(value, float) and value != value:
            return "N/A"
        if isinstance(value, float):
            return f"{value:.2f}".rstrip("0").rstrip(".")
        return str(value)
    except Exception:
        return "N/A"


# ============================================================================
# EXECUTIVE DASHBOARD CARDS - Power BI Style
# ============================================================================

class ExecutiveKPICard:
    """
    Componente de cards especializado para o Executive Dashboard.
    6 variantes conforme especificação do design.
    """

    @staticmethod
    def create_pressure_index_card(value: float, trend: str = "up", change: float = 3.2,
                                   sparkline_data: list = None, unit: str = "pts"):
        """
        Card 1: Composite Housing Pressure Index
        - Número grande centralizado
        - Sparkline Plotly
        - Seta de tendência
        """
        trend_icon = "↑" if trend == "up" else "↓" if trend == "down" else "→"
        trend_color = "#28a745" if trend == "up" else "#dc3545" if trend == "down" else "#6c757d"

        return dbc.Card([
            dbc.CardBody([
                html.H6("Composite Housing Pressure Index",
                        className="kpi-card-title text-muted mb-2",
                        style={"fontSize": "0.75rem", "textTransform": "uppercase", "letterSpacing": "0.05em"}),
                html.Div([
                    html.Span(f"{value:.1f}",
                              className="hero-kpi-value",
                              style={"fontSize": "2.8rem", "fontWeight": "700", "lineHeight": "1"}),
                    html.Span(trend_icon,
                              style={"fontSize": "1.5rem", "color": trend_color, "marginLeft": "8px"})
                ], className="d-flex align-items-center justify-content-center mb-2"),
                html.Div([
                    html.Span(f"{change:+.1f}%", style={"color": trend_color, "fontWeight": "600"}),
                    html.Span(" vs last month", className="text-muted", style={"fontSize": "0.75rem"})
                ], className="text-center mb-3"),
                # Sparkline container (placeholder for mini chart)
                html.Div(
                    id="pressure-sparkline",
                    className="sparkline-container",
                    style={"height": "40px", "background": "#f8f9fa", "borderRadius": "4px"}
                ) if sparkline_data else None
            ], className="p-4")
        ],
            className="executive-kpi-card h-100",
            style={
                "borderRadius": "12px",
                "boxShadow": "0 2px 8px rgba(0,0,0,0.08)",
                "border": "none",
                "background": "white"
            }
        )

    @staticmethod
    def create_affordability_card(value: float, trend: str = "up", change: float = 0.4):
        """
        Card 2: Affordability Score (Price/Income)
        - Ratio grande com gradiente de cor (verde→vermelho)
        - Delta vs último período
        """
        # Determina cor baseada no valor (menor = melhor)
        if value < 5:
            color = "#28a745"  # verde
            status = "Good"
        elif value < 8:
            color = "#ffc107"  # amarelo
            status = "Moderate"
        else:
            color = "#dc3545"  # vermelho
            status = "High"

        trend_icon = "↑" if trend == "up" else "↓"
        trend_color = "#dc3545" if trend == "up" else "#28a745"  # for affordability, rising is bad

        return dbc.Card([
            dbc.CardBody([
                html.H6("Affordability Score (Price/Income)",
                        className="kpi-card-title text-muted mb-2",
                        style={"fontSize": "0.75rem", "textTransform": "uppercase", "letterSpacing": "0.05em"}),
                html.Div([
                    html.Span(f"{value:.2f}",
                              style={"fontSize": "2.8rem", "fontWeight": "700", "lineHeight": "1",
                                     "background": f"linear-gradient(135deg, {color} 0%, {color}dd 100%)",
                                     "WebkitBackgroundClip": "text",
                                     "WebkitTextFillColor": "transparent"})
                ], className="text-center mb-2"),
                html.Div([
                    html.Span(status,
                              style={"color": color, "fontWeight": "600", "fontSize": "0.85rem"})
                ], className="text-center mb-2"),
                html.Div([
                    html.Span(trend_icon, style={"color": trend_color, "fontWeight": "600"}),
                    html.Span(f" {change:+.1f}", style={"color": trend_color, "fontWeight": "600"}),
                    html.Span(" vs last period", className="text-muted", style={"fontSize": "0.75rem"})
                ], className="text-center")
            ], className="p-4")
        ],
            className="executive-kpi-card h-100",
            style={
                "borderRadius": "12px",
                "boxShadow": "0 2px 8px rgba(0,0,0,0.08)",
                "border": "none",
                "background": "white"
            }
        )

    @staticmethod
    def create_price_mom_card(value: float, trend: str = "up", sparkline_data: list = None):
        """
        Card 3: Asking Price MoM % Change
        - Porcentagem grande
        - Cor baseada na magnitude
        - Mini bar trend
        """
        # Cor baseada na magnitude
        if value > 1.0:
            color = "#28a745"
        elif value > 0:
            color = "#ffc107"
        else:
            color = "#dc3545"

        trend_icon = "↑" if trend == "up" else "↓"

        return dbc.Card([
            dbc.CardBody([
                html.H6("Asking Price MoM Change",
                        className="kpi-card-title text-muted mb-2",
                        style={"fontSize": "0.75rem", "textTransform": "uppercase", "letterSpacing": "0.05em"}),
                html.Div([
                    html.Span(f"{value:.2f}%",
                              style={"fontSize": "2.5rem", "fontWeight": "700", "lineHeight": "1",
                                     "color": color}),
                    html.Span(trend_icon,
                              style={"fontSize": "1.5rem", "color": color, "marginLeft": "8px"})
                ], className="d-flex align-items-center justify-content-center mb-3"),
                # Mini bar trend
                html.Div([
                    html.Div(style={
                        "height": "6px",
                        "width": f"{min(abs(value) * 20, 100)}%",
                        "background": color,
                        "borderRadius": "3px",
                        "margin": "0 auto"
                    })
                ], style={"background": "#e9ecef", "borderRadius": "3px", "padding": "2px"})
            ], className="p-4")
        ],
            className="executive-kpi-card h-100",
            style={
                "borderRadius": "12px",
                "boxShadow": "0 2px 8px rgba(0,0,0,0.08)",
                "border": "none",
                "background": "white"
            }
        )

    @staticmethod
    def create_ocr_card(current: float, twelve_months_ago: float, change_bps: float,
                        next_decision: str = "2026-05-28"):
        """
        Card 4: OCR Current vs 12 Months Ago
        - Layout dividido
        - Left: OCR atual, Right: OCR 12 meses atrás
        - Arrow/delta entre eles
        """
        return dbc.Card([
            dbc.CardBody([
                html.H6("OCR Current vs 12 Months Ago",
                        className="kpi-card-title text-muted mb-3",
                        style={"fontSize": "0.75rem", "textTransform": "uppercase", "letterSpacing": "0.05em"}),
                html.Div([
                    # Left side - Current
                    html.Div([
                        html.Div(f"{current:.2f}",
                                   style={"fontSize": "2rem", "fontWeight": "700", "lineHeight": "1"}),
                        html.Div("OCR", style={"fontSize": "0.75rem", "color": "#6c757d"})
                    ], className="text-center"),

                    # Arrow
                    html.Div([
                        html.Span("→", style={"fontSize": "1.5rem", "color": "#2E86AB"})
                    ], className="px-3"),

                    # Right side - 12 months ago
                    html.Div([
                        html.Div(f"{twelve_months_ago:.2f}",
                                   style={"fontSize": "2rem", "fontWeight": "700",
                                          "lineHeight": "1", "color": "#6c757d"}),
                        html.Div("12 months ago", style={"fontSize": "0.75rem", "color": "#6c757d"})
                    ], className="text-center")
                ], className="d-flex align-items-center justify-content-center mb-3"),

                # Change
                html.Div([
                    html.Span(f"+{change_bps:.0f} bps", style={"color": "#dc3545", "fontWeight": "600"}),
                ], className="text-center mb-2"),

                # Next decision
                html.Div([
                    html.Span("Next: ", className="text-muted", style={"fontSize": "0.7rem"}),
                    html.Span(next_decision, style={"fontSize": "0.7rem", "fontWeight": "600"})
                ], className="text-center")
            ], className="p-4")
        ],
            className="executive-kpi-card h-100",
            style={
                "borderRadius": "12px",
                "boxShadow": "0 2px 8px rgba(0,0,0,0.08)",
                "border": "none",
                "background": "white"
            }
        )

    @staticmethod
    def create_top3_regions_card(top3_data: list):
        """
        Card 5: Top 3 Regions Under Pressure
        - Mini-ranking vertical
        - Cada linha: região, score, ícone
        """
        if not top3_data or len(top3_data) < 3:
            # Fallback data
            top3_data = [
                {"region": "Auckland", "score": 82.4},
                {"region": "Queenstown", "score": 87.5},
                {"region": "Tauranga", "score": 74.8}
            ]

        def get_color_for_score(score):
            if score >= 80:
                return "#dc3545"  # red
            elif score >= 60:
                return "#ffc107"  # yellow
            return "#28a745"  # green

        rows = []
        for i, item in enumerate(top3_data[:3], 1):
            score = item.get("score", 0)
            region = item.get("region", "Unknown")
            color = get_color_for_score(score)

            rows.append(html.Div([
                html.Span(f"{i}", style={
                    "width": "20px",
                    "height": "20px",
                    "borderRadius": "50%",
                    "background": "#f8f9fa",
                    "display": "inline-flex",
                    "alignItems": "center",
                    "justifyContent": "center",
                    "fontSize": "0.75rem",
                    "fontWeight": "600",
                    "marginRight": "8px"
                }),
                html.Span(region, style={"flex": "1", "fontSize": "0.9rem"}),
                html.Span(f"{score:.1f}", style={
                    "fontWeight": "700",
                    "color": color,
                    "fontSize": "0.95rem"
                }),
                html.Span("⚠️" if score >= 80 else "⚡" if score >= 60 else "✓",
                          style={"marginLeft": "8px", "fontSize": "0.9rem"})
            ], className="d-flex align-items-center py-2",
                style={"borderBottom": "1px solid #f0f0f0" if i < 3 else "none"}))

        return dbc.Card([
            dbc.CardBody([
                html.H6("Top 3 Regions Under Pressure",
                        className="kpi-card-title text-muted mb-3",
                        style={"fontSize": "0.75rem", "textTransform": "uppercase", "letterSpacing": "0.05em"}),
                html.Div(rows)
            ], className="p-4")
        ],
            className="executive-kpi-card h-100",
            style={
                "borderRadius": "12px",
                "boxShadow": "0 2px 8px rgba(0,0,0,0.08)",
                "border": "none",
                "background": "white"
            }
        )

    @staticmethod
    def create_map_preview_card():
        """
        Card 6: Map Preview Card
        - Mini choropleth Plotly incorporado
        - Label "Click to expand"
        """
        return dbc.Card([
            dbc.CardBody([
                html.H6("Regional Map Preview",
                        className="kpi-card-title text-muted mb-2",
                        style={"fontSize": "0.75rem", "textTransform": "uppercase", "letterSpacing": "0.05em"}),
                html.Div([
                    # Placeholder para mini mapa
                    html.Div(
                        id="map-preview-container",
                        style={
                            "height": "100px",
                            "background": "linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%)",
                            "borderRadius": "8px",
                            "display": "flex",
                            "alignItems": "center",
                            "justifyContent": "center",
                            "position": "relative"
                        },
                        children=[
                            html.Div("🇳🇿", style={"fontSize": "2rem"}),
                            html.Div(style={
                                "position": "absolute",
                                "top": "50%",
                                "left": "50%",
                                "transform": "translate(-50%, -50%)",
                                "width": "40px",
                                "height": "60px",
                                "background": "rgba(46, 134, 171, 0.3)",
                                "borderRadius": "4px"
                            })
                        ]
                    ),
                    html.Div("Click to expand",
                             className="text-center mt-2",
                             style={"fontSize": "0.75rem", "color": "#2E86AB", "cursor": "pointer"})
                ])
            ], className="p-4")
        ],
            className="executive-kpi-card h-100",
            style={
                "borderRadius": "12px",
                "boxShadow": "0 2px 8px rgba(0,0,0,0.08)",
                "border": "none",
                "background": "white",
                "cursor": "pointer"
            }
        )


# ============================================================================
# HOUSING DASHBOARD CARDS - KPI 07-12
# ============================================================================

class HousingKPICard:
    """
    Cards especializados para o Housing Dashboard (KPIs 07-12).
    Seguem o design spec: large cards, sparklines, gauges, mini charts.
    """

    @staticmethod
    def _card_style():
        return {
            "borderRadius": "12px",
            "boxShadow": "0 2px 8px rgba(0,0,0,0.08)",
            "border": "none",
            "background": "white",
        }

    @staticmethod
    def _title_style():
        return {
            "fontSize": "0.72rem",
            "textTransform": "uppercase",
            "letterSpacing": "0.06em",
            "color": "#6c757d",
            "marginBottom": "8px",
        }

    @staticmethod
    def create_median_price_card(
        value: float, unit: str = "NZD", trend: str = "up",
        change: float = 2.3, sparkline_data: list = None, subtitle: str = "Median Listing Price"
    ):
        """
        KPI 07: Median House Price (by Suburb)
        - Large currency value (centered)
        - Subtitle: "Median Listing Price"
        - Small sparkline (price trend)
        """
        trend_icon = "↑" if trend == "up" else "↓"
        trend_color = "#28a745" if trend == "up" else "#dc3545"

        def format_currency(v):
            if v >= 1_000_000:
                return f"${v/1_000_000:.2f}M"
            return f"${v:,.0f}"

        return dbc.Card([
            dbc.CardBody([
                html.H6("KPI 07 — Median House Price", style=HousingKPICard._title_style()),
                html.P(subtitle, className="text-muted mb-2", style={"fontSize": "0.8rem"}),
                html.Div([
                    html.Span(format_currency(value),
                              style={"fontSize": "2.2rem", "fontWeight": "700", "lineHeight": "1"}),
                    html.Span(trend_icon, style={"fontSize": "1.4rem", "color": trend_color, "marginLeft": "6px"}),
                ], className="d-flex align-items-center justify-content-center mb-2"),
                html.Div([
                    html.Span(f"{change:+.1f}% MoM",
                              style={"color": trend_color, "fontWeight": "600", "fontSize": "0.85rem"}),
                ], className="text-center mb-3"),
                # Sparkline placeholder
                html.Div(
                    id="kpi-07-sparkline",
                    className="sparkline-container",
                    style={"height": "36px", "background": "#f8f9fa", "borderRadius": "4px"}
                ) if sparkline_data else None
            ], className="p-4")
        ], className="housing-kpi-card h-100", style=HousingKPICard._card_style())

    @staticmethod
    def create_days_on_market_card(
        value: float, unit: str = "days", trend: str = "down",
        status: str = "Normal", sparkline_data: list = None, subtitle: str = "Days Until Sale"
    ):
        """
        KPI 08: Average Days on Market (DOM)
        - Large numeric value (days)
        - Status indicator: Low=green (fast), High=red (slow)
        - Small trend line
        """
        # Status color: Fast = green, Normal = yellow, Slow = red
        if value < 30:
            status_color = "#28a745"
            status_text = "Fast Market"
        elif value < 45:
            status_color = "#ffc107"
            status_text = "Normal"
        else:
            status_color = "#dc3545"
            status_text = "Slow Market"

        trend_icon = "↑" if trend == "up" else "↓"
        trend_color = "#28a745" if trend == "down" else "#dc3545"  # down = improving

        return dbc.Card([
            dbc.CardBody([
                html.H6("KPI 08 — Average Days on Market", style=HousingKPICard._title_style()),
                html.P(subtitle, className="text-muted mb-2", style={"fontSize": "0.8rem"}),
                html.Div([
                    html.Span(f"{value:.0f}",
                              style={"fontSize": "2.8rem", "fontWeight": "700", "lineHeight": "1"}),
                    html.Span(trend_icon,
                              style={"fontSize": "1.4rem", "color": trend_color, "marginLeft": "6px"}),
                ], className="d-flex align-items-center justify-content-center mb-2"),
                html.Div([
                    html.Span(status_text,
                              style={"color": status_color, "fontWeight": "600", "fontSize": "0.85rem"}),
                ], className="text-center mb-2"),
                # Status indicator bar
                html.Div([
                    html.Div(style={
                        "width": f"{min(value / 60 * 100, 100)}%",
                        "height": "6px",
                        "background": status_color,
                        "borderRadius": "3px",
                    })
                ], style={"background": "#e9ecef", "borderRadius": "3px", "padding": "2px"}),
            ], className="p-4")
        ], className="housing-kpi-card h-100", style=HousingKPICard._card_style())

    @staticmethod
    def create_new_listings_card(
        value: float, unit: str = "listings/week", trend: str = "up",
        change: float = 5.2, weekly_data: list = None, subtitle: str = "Weekly Market Supply"
    ):
        """
        KPI 09: New Listings per Week
        - Large number
        - Subtitle: "Weekly Market Supply"
        - Mini bar chart (recent weeks)
        - Optional YoY or WoW delta
        """
        trend_icon = "↑" if trend == "up" else "↓"
        trend_color = "#28a745" if trend == "up" else "#dc3545"

        return dbc.Card([
            dbc.CardBody([
                html.H6("KPI 09 — New Listings per Week", style=HousingKPICard._title_style()),
                html.P(subtitle, className="text-muted mb-2", style={"fontSize": "0.8rem"}),
                html.Div([
                    html.Span(f"{value:.1f}",
                              style={"fontSize": "2.8rem", "fontWeight": "700", "lineHeight": "1"}),
                    html.Span(f"/week", style={"fontSize": "1rem", "color": "#6c757d", "marginLeft": "4px"}),
                ], className="d-flex align-items-center justify-content-center mb-2"),
                html.Div([
                    html.Span(trend_icon, style={"color": trend_color, "fontWeight": "600"}),
                    html.Span(f" {change:+.1f}% WoW",
                              style={"color": trend_color, "fontWeight": "600", "fontSize": "0.85rem"}),
                ], className="text-center mb-2"),
                # Mini bar chart placeholder
                html.Div(
                    id="kpi-09-bar-chart",
                    className="sparkline-container",
                    style={"height": "36px", "background": "#f8f9fa", "borderRadius": "4px"}
                ) if weekly_data else None
            ], className="p-4")
        ], className="housing-kpi-card h-100", style=HousingKPICard._card_style())

    @staticmethod
    def create_property_type_card(
        dominant_pct: float, breakdown: dict = None, unit: str = "%",
        subtitle: str = "Houses as % of Listings"
    ):
        """
        KPI 10: Property Type Distribution
        - Dominant % (e.g., Houses %)
        - Mini stacked horizontal bar inside card
        - Breakdown: Houses / Apartments / Rooms
        - Clean legend
        """
        if breakdown is None:
            breakdown = {"House": dominant_pct, "Apartment": 20, "Townhouse": 12}

        colors = {"House": "#2E86AB", "Apartment": "#A23B72", "Townhouse": "#F18F01"}
        labels = {"House": "Houses", "Apartment": "Apartments", "Townhouse": "Townhouses"}

        bars = []
        for prop_type, pct in breakdown.items():
            color = colors.get(prop_type, "#6c757d")
            bars.append(html.Div([
                html.Span(labels.get(prop_type, prop_type),
                          style={"fontSize": "0.75rem", "width": "80px"}),
                html.Div(style={
                    "flex": "1",
                    "height": "12px",
                    "background": color,
                    "borderRadius": "2px",
                    "width": f"{pct}%",
                    "marginRight": "4px"
                }),
                html.Span(f"{pct:.0f}%",
                          style={"fontSize": "0.75rem", "fontWeight": "600", "marginLeft": "4px"})
            ], className="d-flex align-items-center mb-1"))

        return dbc.Card([
            dbc.CardBody([
                html.H6("KPI 10 — Property Type Distribution", style=HousingKPICard._title_style()),
                html.P(subtitle, className="text-muted mb-3", style={"fontSize": "0.8rem"}),
                # Dominant value
                html.Div([
                    html.Span(f"{dominant_pct:.0f}%",
                              style={"fontSize": "2.5rem", "fontWeight": "700", "lineHeight": "1"}),
                    html.Span(" Houses", style={"fontSize": "1rem", "color": "#6c757d"}),
                ], className="text-center mb-3"),
                # Stacked bars
                html.Div(bars)
            ], className="p-4")
        ], className="housing-kpi-card h-100", style=HousingKPICard._card_style())

    @staticmethod
    def create_price_per_m2_card(
        value: float, unit: str = "NZD/m²", trend: str = "up",
        change: float = 1.8, bedrooms: dict = None, subtitle: str = "Price per m² (by bedrooms)"
    ):
        """
        KPI 11: Average Price per m²
        - Large value
        - Subtitle: "Price per m² (by bedrooms)"
        - Small segmented indicator (1–2–3–4 bedrooms)
        - Subtle comparison markers
        """
        if bedrooms is None:
            bedrooms = {"1bed": 9000, "2bed": 8000, "3bed": 7500, "4bed": 7000}

        trend_icon = "↑" if trend == "up" else "↓"
        trend_color = "#28a745" if trend == "up" else "#dc3545"

        def format_m2(v):
            return f"${v:,.0f}"

        segments = [
            html.Div([
                html.Span("1bd", style={"fontSize": "0.65rem", "color": "#6c757d", "width": "30px"}),
                html.Div(style={
                    "flex": "1",
                    "height": "16px",
                    "background": "#2E86AB",
                    "borderRadius": "2px",
                    "width": f"{min(bedrooms.get('1bed', 8000) / 12000 * 100, 100)}%",
                }),
                html.Span(format_m2(bedrooms.get('1bed', 8000)),
                          style={"fontSize": "0.72rem", "fontWeight": "600", "marginLeft": "4px"})
            ], className="d-flex align-items-center mb-1"),
            html.Div([
                html.Span("2bd", style={"fontSize": "0.65rem", "color": "#6c757d", "width": "30px"}),
                html.Div(style={
                    "flex": "1",
                    "height": "16px",
                    "background": "#2E86AB",
                    "borderRadius": "2px",
                    "width": f"{min(bedrooms.get('2bed', 8000) / 12000 * 100, 100)}%",
                }),
                html.Span(format_m2(bedrooms.get('2bed', 8000)),
                          style={"fontSize": "0.72rem", "fontWeight": "600", "marginLeft": "4px"})
            ], className="d-flex align-items-center mb-1"),
            html.Div([
                html.Span("3bd", style={"fontSize": "0.65rem", "color": "#6c757d", "width": "30px"}),
                html.Div(style={
                    "flex": "1",
                    "height": "16px",
                    "background": "#2E86AB",
                    "borderRadius": "2px",
                    "width": f"{min(bedrooms.get('3bed', 8000) / 12000 * 100, 100)}%",
                }),
                html.Span(format_m2(bedrooms.get('3bed', 8000)),
                          style={"fontSize": "0.72rem", "fontWeight": "600", "marginLeft": "4px"})
            ], className="d-flex align-items-center mb-1"),
            html.Div([
                html.Span("4bd", style={"fontSize": "0.65rem", "color": "#6c757d", "width": "30px"}),
                html.Div(style={
                    "flex": "1",
                    "height": "16px",
                    "background": "#2E86AB",
                    "borderRadius": "2px",
                    "width": f"{min(bedrooms.get('4bed', 8000) / 12000 * 100, 100)}%",
                }),
                html.Span(format_m2(bedrooms.get('4bed', 8000)),
                          style={"fontSize": "0.72rem", "fontWeight": "600", "marginLeft": "4px"})
            ], className="d-flex align-items-center mb-1"),
        ]

        return dbc.Card([
            dbc.CardBody([
                html.H6("KPI 11 — Average Price per m²", style=HousingKPICard._title_style()),
                html.P(subtitle, className="text-muted mb-2", style={"fontSize": "0.8rem"}),
                html.Div([
                    html.Span(f"${value:,.0f}",
                              style={"fontSize": "2rem", "fontWeight": "700", "lineHeight": "1"}),
                    html.Span(trend_icon, style={"fontSize": "1.3rem", "color": trend_color, "marginLeft": "6px"}),
                ], className="d-flex align-items-center justify-content-center mb-3"),
                html.Div(segments, style={"padding": "0 4px"})
            ], className="p-4")
        ], className="housing-kpi-card h-100", style=HousingKPICard._card_style())

    @staticmethod
    def create_supply_gap_card(
        value: float, unit: str = "pts", trend: str = "up",
        status: str = "Deficit", severity: float = 0.75,
        subtitle: str = "Supply vs Demand Imbalance"
    ):
        """
        KPI 12: Housing Supply Gap (Deficit Score)
        - Composite score (0–100)
        - Label: "Supply vs Demand Imbalance"
        - Visual: progress bar or gauge style
        - Highlight shortage severity
        """
        trend_icon = "↑" if trend == "up" else "↓"
        trend_color = "#dc3545" if trend == "up" else "#28a745"

        if severity >= 0.75:
            gauge_color = "#dc3545"
            status_text = "Severe Shortage"
        elif severity >= 0.50:
            gauge_color = "#ffc107"
            status_text = "Moderate Deficit"
        else:
            gauge_color = "#28a745"
            status_text = "Balanced"

        return dbc.Card([
            dbc.CardBody([
                html.H6("KPI 12 — Housing Supply Gap", style=HousingKPICard._title_style()),
                html.P(subtitle, className="text-muted mb-2", style={"fontSize": "0.8rem"}),
                html.Div([
                    html.Span(f"{value:.0f}",
                              style={"fontSize": "2.8rem", "fontWeight": "700", "lineHeight": "1", "color": gauge_color}),
                    html.Span(trend_icon, style={"fontSize": "1.4rem", "color": trend_color, "marginLeft": "6px"}),
                ], className="d-flex align-items-center justify-content-center mb-2"),
                html.Div([
                    html.Span(status_text,
                              style={"color": gauge_color, "fontWeight": "600", "fontSize": "0.85rem"}),
                ], className="text-center mb-3"),
                # Gauge / progress bar
                html.Div([
                    html.Div(style={
                        "width": f"{severity * 100}%",
                        "height": "10px",
                        "background": gauge_color,
                        "borderRadius": "5px",
                    })
                ], style={"background": "#e9ecef", "borderRadius": "5px", "padding": "3px"}),
                html.Div([
                    html.Span("Balanced", style={"fontSize": "0.65rem", "color": "#6c757d"}),
                    html.Span("Severe", style={"fontSize": "0.65rem", "color": "#6c757d", "marginLeft": "auto"})
                ], className="d-flex justify-content-between mt-1")
            ], className="p-4")
        ], className="housing-kpi-card h-100", style=HousingKPICard._card_style())


class TourismKPICard:
    """KPIs 13–17: Tourism Impact on Housing Market."""

    _accent_colors = {
        "pressure": "#E74C3C",
        "airbnb": "#8E44AD",
        "lag": "#D35400",
        "seasonality": "#1A5276",
        "correlation": "#148F77",
    }

    @staticmethod
    def _card_style() -> dict:
        return {
            "borderRadius": "12px",
            "border": "1px solid rgba(255,255,255,0.1)",
            "boxShadow": "0 2px 8px rgba(0,0,0,0.08)",
            "background": "#fff",
        }

    @staticmethod
    def _title_style() -> dict:
        return {
            "fontSize": "0.72rem",
            "fontWeight": "600",
            "color": "#8898aa",
            "letterSpacing": "0.5px",
            "textTransform": "uppercase",
            "marginBottom": "4px",
        }

    @staticmethod
    def _build_sparkline_bar(width: int = 60, height: int = 28, color: str = "#2E86AB") -> html.Div:
        return html.Div(
            style={
                "display": "flex",
                "alignItems": "end",
                "gap": "2px",
                "height": f"{height}px",
                "marginTop": "6px",
            }
        )

    @staticmethod
    def _sparkline_bars(data: list, width: int = 80, height: int = 28,
                        color: str = "#2E86AB") -> html.Div:
        if not data:
            return html.Div()
        bars = []
        max_v = max(data)
        min_v = min(data)
        rng = max_v - min_v if max_v != min_v else 1
        for v in data:
            bar_h = max(2, int((v - min_v) / rng * (height - 4)))
            bars.append(html.Div(style={
                "flex": "1",
                "height": f"{bar_h}px",
                "background": color,
                "borderRadius": "2px 2px 0 0",
                "margin": "0 1px",
            }))
        return html.Div(bars, style={
            "display": "flex", "alignItems": "flex-end",
            "gap": "2px", "height": f"{height}px",
        })

    # ── KPI 13: Tourism Pressure Index ────────────────────────────────────
    @staticmethod
    def create_pressure_index_card(value: float, unit: str = "pts",
                                     trend: str = "up", change: float = 4.2,
                                     sparkline: list = None, by_region: dict = None):
        accent = TourismKPICard._accent_colors["pressure"]
        trend_icon = "↑" if trend == "up" else "↓"
        trend_color = "#28a745" if trend == "up" else "#dc3545"

        top_region = max(by_region.items(), key=lambda x: x[1]) if by_region else None

        return dbc.Card([
            dbc.CardBody([
                html.H6("KPI 13 — Tourism Pressure Index", style=TourismKPICard._title_style()),
                html.P("Tourism Pressure on Housing", className="text-muted mb-2", style={"fontSize": "0.78rem"}),
                html.Div([
                    html.Span(f"{value:.1f}",
                              style={"fontSize": "2.6rem", "fontWeight": "700", "lineHeight": "1", "color": accent}),
                    html.Span(trend_icon, style={"fontSize": "1.4rem", "color": trend_color, "marginLeft": "6px"}),
                ], className="d-flex align-items-center justify-content-center mb-2"),
                html.Div([
                    html.Span(f"{change:+.1f}%",
                              style={"color": trend_color, "fontWeight": "600", "fontSize": "0.85rem"}),
                    html.Span(" vs last month", style={"color": "#8898aa", "fontSize": "0.75rem", "marginLeft": "2px"}),
                ], className="text-center mb-3"),
                TourismKPICard._sparkline_bars(sparkline, 90, 32, color=accent) if sparkline else None,
                html.Hr(style={"margin": "10px 0 8px"}),
                html.Div([
                    html.Span("Highest: ", style={"fontSize": "0.7rem", "color": "#8898aa"}),
                    html.Span(top_region[0], style={"fontSize": "0.75rem", "fontWeight": "600", "color": accent}),
                    html.Span(f" {top_region[1]:.1f}", style={"fontSize": "0.75rem", "fontWeight": "700", "color": accent}),
                ], className="text-center") if top_region else None,
            ], className="p-3")
        ], className="housing-kpi-card h-100", style=TourismKPICard._card_style())

    # ── KPI 14: Airbnb Share ────────────────────────────────────────────────
    @staticmethod
    def create_airbnb_share_card(value: float, unit: str = "%",
                                  trend: str = "up", change: float = 1.8,
                                  breakdown: dict = None, sparkline: list = None,
                                  by_region: dict = None):
        accent = TourismKPICard._accent_colors["airbnb"]
        trend_icon = "↑" if trend == "up" else "↓"
        trend_color = "#28a745" if trend == "up" else "#dc3545"
        if breakdown is None:
            breakdown = {"Airbnb": value, "Traditional": round(100 - value, 1)}

        top_region = max(by_region.items(), key=lambda x: x[1]) if by_region else None

        stacked_pct = breakdown.get("Airbnb", value)
        trad_pct = breakdown.get("Traditional", round(100 - value, 1))

        return dbc.Card([
            dbc.CardBody([
                html.H6("KPI 14 — Airbnb Share of Rentals", style=TourismKPICard._title_style()),
                html.P("% of Housing Supply Listed on Airbnb", className="text-muted mb-2", style={"fontSize": "0.78rem"}),
                html.Div([
                    html.Span(f"{value:.1f}",
                              style={"fontSize": "2.6rem", "fontWeight": "700", "lineHeight": "1", "color": accent}),
                    html.Span(f"%", style={"fontSize": "1.1rem", "color": accent, "marginLeft": "2px"}),
                ], className="d-flex align-items-center justify-content-center mb-2"),
                html.Div([
                    html.Span(trend_icon, style={"color": trend_color, "fontWeight": "600"}),
                    html.Span(f" {change:+.1f}% pp YoY",
                              style={"color": trend_color, "fontWeight": "600", "fontSize": "0.85rem"}),
                ], className="text-center mb-3"),
                # Stacked bar Airbnb vs Traditional
                html.Div([
                    html.Div(style={
                        "flex": f"{stacked_pct}",
                        "height": "8px",
                        "background": accent,
                        "borderRadius": "4px 0 0 4px",
                    }),
                    html.Div(style={
                        "flex": f"{trad_pct}",
                        "height": "8px",
                        "background": "#dee2e6",
                        "borderRadius": "0 4px 4px 0",
                    }),
                ], className="d-flex mb-1", style={"borderRadius": "4px", "overflow": "hidden"}),
                html.Div([
                    html.Span("● Airbnb", style={"fontSize": "0.68rem", "color": accent, "fontWeight": "600"}),
                    html.Span(f" {stacked_pct:.1f}%", style={"fontSize": "0.68rem", "color": "#495057", "marginLeft": "2px"}),
                    html.Span("  ● Traditional", style={"fontSize": "0.68rem", "color": "#8898aa", "marginLeft": "10px"}),
                    html.Span(f" {trad_pct:.1f}%", style={"fontSize": "0.68rem", "color": "#495057", "marginLeft": "2px"}),
                ], className="text-center"),
                TourismKPICard._sparkline_bars(sparkline, 90, 28, color=accent) if sparkline else None,
                html.Div([
                    html.Span("Highest: ", style={"fontSize": "0.7rem", "color": "#8898aa"}),
                    html.Span(top_region[0], style={"fontSize": "0.75rem", "fontWeight": "600", "color": accent}),
                    html.Span(f" {top_region[1]:.1f}%", style={"fontSize": "0.75rem", "fontWeight": "700", "color": accent}),
                ], className="text-center mt-2") if top_region else None,
            ], className="p-3")
        ], className="housing-kpi-card h-100", style=TourismKPICard._card_style())

    # ── KPI 15: Tourism → Rent Lag ──────────────────────────────────────────
    @staticmethod
    def create_rent_lag_card(value: float, unit: str = "months",
                              trend: str = "up", sparkline: list = None,
                              by_region: dict = None):
        accent = TourismKPICard._accent_colors["lag"]
        trend_icon = "↑" if trend == "up" else "↓"
        trend_color = "#dc3545" if trend == "up" else "#28a745"

        fast_regions = [r for r, v in (by_region or {}).items() if v <= 4]
        slow_regions = [r for r, v in (by_region or {}).items() if v > 6]

        return dbc.Card([
            dbc.CardBody([
                html.H6("KPI 15 — Tourism → Rent Price Lag", style=TourismKPICard._title_style()),
                html.P("Lag Effect (Visitors → Rent Increase)", className="text-muted mb-2", style={"fontSize": "0.78rem"}),
                html.Div([
                    html.Span(f"{value:.0f}",
                              style={"fontSize": "2.6rem", "fontWeight": "700", "lineHeight": "1", "color": accent}),
                    html.Span(" months", style={"fontSize": "1rem", "color": "#6c757d", "marginLeft": "4px"}),
                    html.Span(trend_icon, style={"fontSize": "1.4rem", "color": trend_color, "marginLeft": "6px"}),
                ], className="d-flex align-items-center justify-content-center mb-2"),
                TourismKPICard._sparkline_bars(sparkline, 90, 28, color=accent) if sparkline else None,
                html.Hr(style={"margin": "10px 0 8px"}),
                # Mini timeline: Tourism peak → Rent increase
                html.Div([
                    html.Span("Tourism Peak", style={"fontSize": "0.65rem", "color": "#8898aa"}),
                    html.Span(" → ", style={"fontSize": "0.65rem", "color": "#dee2e6"}),
                    html.Span(f"+{value:.0f}m", style={"fontSize": "0.7rem", "fontWeight": "600", "color": accent}),
                    html.Span(" → Rent ↑", style={"fontSize": "0.65rem", "color": "#8898aa", "marginLeft": "4px"}),
                ], className="text-center d-flex justify-content-center align-items-center gap-1"),
                html.Div([
                    html.Span(f"Fast: {', '.join(fast_regions[:3]) if fast_regions else 'N/A'}",
                              style={"fontSize": "0.68rem", "color": "#28a745", "marginRight": "8px"}) if fast_regions else None,
                    html.Span(f"Slow: {', '.join(slow_regions[:2]) if slow_regions else 'N/A'}",
                              style={"fontSize": "0.68rem", "color": "#dc3545"}) if slow_regions else None,
                ], className="text-center mt-2"),
            ], className="p-3")
        ], className="housing-kpi-card h-100", style=TourismKPICard._card_style())

    # ── KPI 16: Visitor Seasonality Strength ────────────────────────────────
    @staticmethod
    def create_seasonality_card(value: float, unit: str = "pts",
                                 trend: str = "down", by_origin: dict = None,
                                 sparklines: dict = None):
        accent = TourismKPICard._accent_colors["seasonality"]
        trend_icon = "↓" if trend == "down" else "↑"
        trend_color = "#28a745" if trend == "down" else "#dc3545"

        origins = by_origin or {}
        origin_colors = {"Australia": "#28a745", "China": "#dc3545", "USA": "#2E86AB"}
        origin_keys = list(origins.keys())[:3]

        return dbc.Card([
            dbc.CardBody([
                html.H6("KPI 16 — Visitor Seasonality Strength", style=TourismKPICard._title_style()),
                html.P("Peak vs Low Season Intensity", className="text-muted mb-1", style={"fontSize": "0.78rem"}),
                html.Div([
                    html.Span(f"{value:.1f}",
                              style={"fontSize": "2.2rem", "fontWeight": "700", "lineHeight": "1", "color": accent}),
                    html.Span(" pts", style={"fontSize": "0.9rem", "color": "#6c757d"}),
                    html.Span(trend_icon, style={"fontSize": "1.2rem", "color": trend_color, "marginLeft": "6px"}),
                ], className="d-flex align-items-center justify-content-center mb-2"),
                html.Div([
                    html.Span("Current average", style={"fontSize": "0.7rem", "color": "#8898aa"}),
                ], className="text-center mb-2"),
                html.Div([
                    html.Div([
                        html.Span(o, style={"fontSize": "0.65rem", "fontWeight": "600",
                                            "color": origin_colors.get(o, "#6c757d"), "width": "52px"}),
                        TourismKPICard._sparkline_bars(sparklines.get(o, []), 60, 20,
                                                       color=origin_colors.get(o, "#6c757d")) if sparklines else None,
                        html.Span(f"{origins[o]:.0f}",
                                  style={"fontSize": "0.72rem", "fontWeight": "700", "color": origin_colors.get(o, "#6c757d")}),
                    ], className="d-flex align-items-center gap-1 mb-1")
                    for o in origin_keys
                ]),
            ], className="p-3")
        ], className="housing-kpi-card h-100", style=TourismKPICard._card_style())

    # ── KPI 17: Tourism × DOM Correlation ──────────────────────────────────
    @staticmethod
    def create_dom_correlation_card(value: float, unit: str = "r",
                                      trend: str = "neutral", strength: str = "Strong",
                                      by_region: dict = None):
        accent = TourismKPICard._accent_colors["correlation"]

        strength_colors = {"Strong": "#28a745", "Moderate": "#ffc107", "Weak": "#6c757d"}
        strength_color = strength_colors.get(strength, "#6c757d")

        trend_icon = {"up": "↗", "down": "↘", "neutral": "→"}.get(trend, "→")
        trend_color = "#28a745" if trend == "up" else "#dc3545" if trend == "down" else "#6c757d"

        return dbc.Card([
            dbc.CardBody([
                html.H6("KPI 17 — Tourism × DOM Correlation", style=TourismKPICard._title_style()),
                html.P("Visitors vs Days on Market", className="text-muted mb-2", style={"fontSize": "0.78rem"}),
                html.Div([
                    html.Span(f"{value:.2f}",
                              style={"fontSize": "2.6rem", "fontWeight": "700", "lineHeight": "1", "color": accent}),
                    html.Span(trend_icon, style={"fontSize": "1.4rem", "color": trend_color, "marginLeft": "6px"}),
                ], className="d-flex align-items-center justify-content-center mb-2"),
                html.Div([
                    html.Span(strength,
                              style={"color": strength_color, "fontWeight": "700", "fontSize": "0.9rem"}),
                    html.Span(" correlation", style={"color": "#8898aa", "fontSize": "0.8rem", "marginLeft": "4px"}),
                ], className="text-center mb-3"),
                html.Hr(style={"margin": "6px 0"}),
                html.Div([
                    html.Span("Top regions:", style={"fontSize": "0.7rem", "color": "#8898aa"}),
                    html.Span(", ".join(list(by_region.keys())[:3]) if by_region else "",
                              style={"fontSize": "0.72rem", "fontWeight": "600", "color": accent}),
                ], className="text-center"),
            ], className="p-3")
        ], className="housing-kpi-card h-100", style=TourismKPICard._card_style())


class MacroKPICard:
    """KPIs 18-22: Macroeconomic (OCR, Mortgage Rates, Construction, Correlation)."""

    _accent_colors = {
        "ocr": "#1A5276",
        "mortgage": "#2E86AB",
        "cost": "#148F77",
        "construction": "#D35400",
        "correlation": "#8E44AD",
    }

    @staticmethod
    def _card_style() -> dict:
        return {
            "borderRadius": "8px",
            "border": "1px solid rgba(0,0,0,0.08)",
            "boxShadow": "0 1px 4px rgba(0,0,0,0.06)",
            "background": "#fff",
        }

    @staticmethod
    def _title_style() -> dict:
        return {
            "fontSize": "0.68rem",
            "fontWeight": "700",
            "color": "#495057",
            "letterSpacing": "0.5px",
            "textTransform": "uppercase",
            "marginBottom": "4px",
        }

    @staticmethod
    def _sparkline_bars(data: list, width: int = 80, height: int = 28,
                        color: str = "#2E86AB") -> html.Div:
        if not data:
            return html.Div()
        bars = []
        max_v, min_v = max(data), min(data)
        rng = max_v - min_v if max_v != min_v else 1
        for v in data:
            bar_h = max(2, int((v - min_v) / rng * (height - 4)))
            bars.append(html.Div(style={
                "flex": "1", "height": f"{bar_h}px",
                "background": color, "borderRadius": "2px 2px 0 0", "margin": "0 1px",
            }))
        return html.Div(bars, style={"display": "flex", "alignItems": "flex-end", "gap": "1px", "height": f"{height}px"})

    # ── KPI 18: OCR Current ────────────────────────────────────────────────
    @staticmethod
    def create_ocr_card(value: float, unit: str = "%", trend: str = "down",
                         change: float = -0.25, next_decision: str = "",
                         sparkline: list = None, history: list = None):
        accent = MacroKPICard._accent_colors["ocr"]
        trend_icon = "↓" if trend == "down" else "↑"
        trend_color = "#28a745" if trend == "down" else "#dc3545"

        return dbc.Card([
            dbc.CardBody([
                html.H6("KPI 18 — OCR Current", style=MacroKPICard._title_style()),
                html.P("Official Cash Rate (RBNZ)", className="text-muted mb-1", style={"fontSize": "0.75rem"}),
                html.Div([
                    html.Span(f"{value:.2f}",
                              style={"fontSize": "2.8rem", "fontWeight": "700", "lineHeight": "1", "color": accent}),
                    html.Span("%", style={"fontSize": "1.2rem", "color": accent, "marginLeft": "2px"}),
                    html.Span(trend_icon, style={"fontSize": "1.4rem", "color": trend_color, "marginLeft": "6px"}),
                ], className="d-flex align-items-center justify-content-center mb-1"),
                html.Div([
                    html.Span(f"{change:+.2f}%", style={"color": trend_color, "fontWeight": "600", "fontSize": "0.82rem"}),
                    html.Span(" vs last decision", style={"color": "#8898aa", "fontSize": "0.72rem", "marginLeft": "2px"}),
                ], className="text-center mb-2"),
                MacroKPICard._sparkline_bars(sparkline, 100, 30, color=accent) if sparkline else None,
                html.Hr(style={"margin": "8px 0 6px"}),
                html.Div([
                    html.Span("Next decision: ", style={"fontSize": "0.65rem", "color": "#8898aa"}),
                    html.Span(next_decision, style={"fontSize": "0.72rem", "fontWeight": "700", "color": accent}),
                ], className="text-center"),
            ], className="p-3")
        ], className="housing-kpi-card h-100", style=MacroKPICard._card_style())

    # ── KPI 19: Mortgage Rates (1Y / 2Y / 5Y) ─────────────────────────────
    @staticmethod
    def create_mortgage_rates_card(rates: dict = None, rates_prev: dict = None,
                                    subtitle: str = "by Term (1Y / 2Y / 5Y)"):
        accent = MacroKPICard._accent_colors["mortgage"]
        if rates is None:
            rates = {"1Y": 6.45, "2Y": 6.20, "5Y": 6.85}

        terms = ["1Y", "2Y", "5Y"]
        term_colors = {"1Y": "#E74C3C", "2Y": "#2E86AB", "5Y": "#148F77"}

        def rate_row(term: str) -> html.Div:
            rv = rates.get(term, 0)
            rp = rates_prev.get(term, 0) if rates_prev else 0
            chg = rv - rp
            chg_color = "#28a745" if chg < 0 else "#dc3545" if chg > 0 else "#8898aa"
            return html.Div([
                html.Span(term, style={"fontSize": "0.7rem", "fontWeight": "700", "width": "24px",
                                       "color": term_colors.get(term, "#6c757d")}),
                html.Span(f"{rv:.2f}%", style={"fontSize": "1.1rem", "fontWeight": "700", "color": accent}),
                html.Span(f"{chg:+.2f}%", style={"fontSize": "0.68rem", "color": chg_color, "marginLeft": "4px"}),
            ], className="d-flex align-items-center mb-1")

        return dbc.Card([
            dbc.CardBody([
                html.H6("KPI 19 — Mortgage Rates", style=MacroKPICard._title_style()),
                html.P(subtitle, className="text-muted mb-2", style={"fontSize": "0.75rem"}),
                html.Div([rate_row(t) for t in terms], style={"padding": "4px 0"}),
                html.Hr(style={"margin": "8px 0 6px"}),
                html.Div([
                    html.Span("Current vs 3M ago", style={"fontSize": "0.65rem", "color": "#8898aa"}),
                ], className="text-center"),
                html.Div([
                    html.Div(style={
                        "flex": "1", "height": "6px",
                        "background": f"linear-gradient(90deg, {term_colors['1Y']}, {term_colors['2Y']}, {term_colors['5Y']})",
                        "borderRadius": "3px",
                    }),
                ], className="mt-2"),
            ], className="p-3")
        ], className="housing-kpi-card h-100", style=MacroKPICard._card_style())

    # ── KPI 20: Monthly Mortgage Cost ─────────────────────────────────────
    @staticmethod
    def create_mortgage_cost_card(value: float, unit: str = "NZD/month",
                                    trend: str = "down", change: float = -320,
                                    by_suburb: dict = None, subtitle: str = ""):
        accent = MacroKPICard._accent_colors["cost"]
        trend_color = "#28a745" if trend == "down" else "#dc3545"

        sorted_suburbs = sorted((by_suburb or {}).items(), key=lambda x: x[1], reverse=True)[:5]
        top_suburb = sorted_suburbs[0] if sorted_suburbs else None

        return dbc.Card([
            dbc.CardBody([
                html.H6("KPI 20 — Monthly Mortgage Cost", style=MacroKPICard._title_style()),
                html.P(f"$750K loan @ 6.20% (2Y)", className="text-muted mb-1", style={"fontSize": "0.75rem"}),
                html.Div([
                    html.Span(f"${value:,.0f}",
                              style={"fontSize": "2.4rem", "fontWeight": "700", "lineHeight": "1", "color": accent}),
                    html.Span("/mo", style={"fontSize": "0.9rem", "color": "#6c757d", "marginLeft": "2px"}),
                ], className="d-flex align-items-center justify-content-center mb-1"),
                html.Div([
                    html.Span("↓", style={"color": trend_color, "fontWeight": "600"}),
                    html.Span(f" ${abs(change):,} vs prev", style={"color": trend_color, "fontSize": "0.8rem"}),
                ], className="text-center mb-2"),
                html.Hr(style={"margin": "6px 0"}),
                html.Div([
                    html.Span("Most expensive: ", style={"fontSize": "0.65rem", "color": "#8898aa"}),
                    html.Span(top_suburb[0] if top_suburb else "N/A",
                              style={"fontSize": "0.72rem", "fontWeight": "600", "color": accent}),
                    html.Span(f" ${top_suburb[1]:,}" if top_suburb else "",
                              style={"fontSize": "0.72rem", "fontWeight": "700", "color": accent}),
                ], className="text-center"),
            ], className="p-3")
        ], className="housing-kpi-card h-100", style=MacroKPICard._card_style())

    # ── KPI 21: Construction Employment ──────────────────────────────────
    @staticmethod
    def create_construction_card(value: float, unit: str = "%",
                                   trend: str = "down", change: float = -0.3,
                                   status: str = "Declining",
                                   sparkline: list = None, history: list = None):
        accent = MacroKPICard._accent_colors["construction"]
        trend_color = "#dc3545" if trend == "down" else "#28a745"
        status_color = "#dc3545" if status == "Declining" else "#28a745"

        return dbc.Card([
            dbc.CardBody([
                html.H6("KPI 21 — Construction Employment", style=MacroKPICard._title_style()),
                html.P("% of Total Workforce", className="text-muted mb-1", style={"fontSize": "0.75rem"}),
                html.Div([
                    html.Span(f"{value:.1f}",
                              style={"fontSize": "2.8rem", "fontWeight": "700", "lineHeight": "1", "color": accent}),
                    html.Span("%", style={"fontSize": "1.2rem", "color": accent, "marginLeft": "2px"}),
                ], className="d-flex align-items-center justify-content-center mb-1"),
                html.Div([
                    html.Span(f"{change:+.1f}%", style={"color": trend_color, "fontWeight": "600", "fontSize": "0.82rem"}),
                    html.Span(f" MoM", style={"color": "#8898aa", "fontSize": "0.72rem"}),
                    html.Span(" ● ", style={"color": "#dee2e6", "fontSize": "0.8rem"}),
                    html.Span(status, style={"color": status_color, "fontWeight": "700", "fontSize": "0.78rem"}),
                ], className="text-center mb-2"),
                MacroKPICard._sparkline_bars(sparkline, 100, 28, color=accent) if sparkline else None,
            ], className="p-3")
        ], className="housing-kpi-card h-100", style=MacroKPICard._card_style())

    # ── KPI 22: OCR vs Listings Correlation ────────────────────────────────
    @staticmethod
    def create_ocr_listings_corr_card(value: float, unit: str = "r",
                                        strength: str = "Strong",
                                        type: str = "Negative",
                                        lag_periods: list = None,
                                        listings_data: list = None,
                                        lagged_ocr: list = None):
        accent = MacroKPICard._accent_colors["correlation"]

        strength_colors = {"Strong": "#28a745", "Moderate": "#ffc107", "Weak": "#6c757d"}
        type_colors = {"Negative": "#dc3545", "Positive": "#28a745", "Neutral": "#8898aa"}
        sc = strength_colors.get(strength, "#6c757d")
        tc = type_colors.get(type, "#6c757d")

        mini_bars = []
        if listings_data:
            max_v = max(listings_data)
            for v in listings_data[-8:]:
                bh = max(3, int(v / max_v * 28))
                mini_bars.append(html.Div(style={
                    "flex": "1", "height": f"{bh}px",
                    "background": accent, "borderRadius": "1px 1px 0 0",
                }))

        return dbc.Card([
            dbc.CardBody([
                html.H6("KPI 22 — OCR vs Listings Correlation", style=MacroKPICard._title_style()),
                html.P("Lagged Relationship", className="text-muted mb-1", style={"fontSize": "0.75rem"}),
                html.Div([
                    html.Span(f"{value:.2f}",
                              style={"fontSize": "2.8rem", "fontWeight": "700", "lineHeight": "1", "color": accent}),
                    html.Span(" r", style={"fontSize": "1.2rem", "color": accent}),
                ], className="d-flex align-items-center justify-content-center mb-1"),
                html.Div([
                    html.Span(strength, style={"color": sc, "fontWeight": "700", "fontSize": "0.85rem"}),
                    html.Span(f" / {type}", style={"color": tc, "fontWeight": "600", "fontSize": "0.82rem"}),
                ], className="text-center mb-2"),
                html.Hr(style={"margin": "6px 0 4px"}),
                html.Div([
                    html.Span("Inverse relationship", style={"fontSize": "0.65rem", "color": "#8898aa"}),
                ], className="text-center mb-1"),
                html.Div(mini_bars, style={"display": "flex", "alignItems": "flex-end", "gap": "2px", "height": "28px"}),
                html.Div([
                    html.Span("OCR up → Listings down", style={"fontSize": "0.65rem", "color": "#dc3545", "fontWeight": "600"}),
                ], className="text-center mt-1"),
            ], className="p-3")
        ], className="housing-kpi-card h-100", style=MacroKPICard._card_style())


class AffordabilityKPICard:
    """KPIs 23-27: Housing Affordability (Years to Buy, Rent Burden, Ranking, Gap, Migration)."""

    _accent_colors = {
        "years": "#2E86AB",
        "rent_burden": "#E74C3C",
        "ranking": "#8E44AD",
        "gap": "#D35400",
        "migration": "#148F77",
    }

    @staticmethod
    def _card_style() -> dict:
        return {
            "borderRadius": "16px",
            "border": "1px solid rgba(0,0,0,0.06)",
            "boxShadow": "0 4px 12px rgba(0,0,0,0.07)",
            "background": "#fff",
        }

    @staticmethod
    def _title_style() -> dict:
        return {
            "fontSize": "0.72rem",
            "fontWeight": "600",
            "color": "#8898aa",
            "letterSpacing": "0.5px",
            "textTransform": "uppercase",
            "marginBottom": "4px",
        }

    @staticmethod
    def _sparkline_bars(data: list, width: int = 80, height: int = 28,
                        color: str = "#2E86AB") -> html.Div:
        if not data:
            return html.Div()
        bars = []
        max_v, min_v = max(data), min(data)
        rng = max_v - min_v if max_v != min_v else 1
        for v in data:
            bar_h = max(2, int((v - min_v) / rng * (height - 4)))
            bars.append(html.Div(style={
                "flex": "1", "height": f"{bar_h}px",
                "background": color, "borderRadius": "2px 2px 0 0", "margin": "0 1px",
            }))
        return html.Div(bars, style={"display": "flex", "alignItems": "flex-end", "gap": "1px", "height": f"{height}px"})

    # ── KPI 23: Years to Buy a House ─────────────────────────────────────
    @staticmethod
    def create_years_to_buy_card(value: float, unit: str = "years",
                                 trend: str = "up", change: float = 0.8,
                                 status: str = "Expensive",
                                 color_scale: str = "#e74c3c",
                                 sparkline: list = None, by_region: dict = None):
        accent = AffordabilityKPICard._accent_colors["years"]
        trend_icon = "↑" if trend == "up" else "↓"
        trend_color = "#dc3545" if trend == "up" else "#28a745"

        status_colors = {"Expensive": "#dc3545", "Moderate": "#ffc107", "Affordable": "#28a745"}
        sc = status_colors.get(status, "#6c757d")

        return dbc.Card([
            dbc.CardBody([
                html.H6("KPI 23 — Years to Buy a House", style=AffordabilityKPICard._title_style()),
                html.P("Median Income Required", className="text-muted mb-1", style={"fontSize": "0.78rem"}),
                html.Div([
                    html.Span(f"{value:.1f}",
                              style={"fontSize": "3rem", "fontWeight": "700", "lineHeight": "1", "color": color_scale}),
                    html.Span(" yrs", style={"fontSize": "1rem", "color": "#6c757d", "marginLeft": "2px"}),
                    html.Span(trend_icon, style={"fontSize": "1.4rem", "color": trend_color, "marginLeft": "6px"}),
                ], className="d-flex align-items-center justify-content-center mb-1"),
                html.Div([
                    html.Span(f"{change:+.1f} yrs", style={"color": trend_color, "fontWeight": "600", "fontSize": "0.82rem"}),
                    html.Span(" vs last year", style={"color": "#8898aa", "fontSize": "0.72rem", "marginLeft": "2px"}),
                ], className="text-center mb-2"),
                AffordabilityKPICard._sparkline_bars(sparkline, 100, 28, color=color_scale) if sparkline else None,
                html.Hr(style={"margin": "8px 0 6px"}),
                html.Div([
                    html.Span("Status: ", style={"fontSize": "0.7rem", "color": "#8898aa"}),
                    html.Span(status, style={"color": sc, "fontWeight": "700", "fontSize": "0.82rem"}),
                ], className="text-center"),
            ], className="p-3")
        ], className="housing-kpi-card h-100", style=AffordabilityKPICard._card_style())

    # ── KPI 24: Rent Burden ─────────────────────────────────────────────
    @staticmethod
    def create_rent_burden_card(value: float, unit: str = "%",
                                 trend: str = "up", change: float = 2.5,
                                 status: str = "Warning",
                                 threshold: int = 30,
                                 sparkline: list = None, by_region: dict = None):
        accent = AffordabilityKPICard._accent_colors["rent_burden"]
        trend_color = "#dc3545" if trend == "up" else "#28a745"

        status_colors = {"Critical": "#dc3545", "Warning": "#ffc107", "Healthy": "#28a745"}
        sc = status_colors.get(status, "#6c757d")

        pct_filled = min(value / 50 * 100, 100)
        threshold_pos = threshold / 50 * 100

        return dbc.Card([
            dbc.CardBody([
                html.H6("KPI 24 — Rent Burden", style=AffordabilityKPICard._title_style()),
                html.P("Income Spent on Rent (%)", className="text-muted mb-1", style={"fontSize": "0.78rem"}),
                html.Div([
                    html.Span(f"{value:.1f}",
                              style={"fontSize": "3rem", "fontWeight": "700", "lineHeight": "1", "color": sc}),
                    html.Span("%", style={"fontSize": "1.2rem", "color": sc, "marginLeft": "2px"}),
                ], className="d-flex align-items-center justify-content-center mb-1"),
                html.Div([
                    html.Span(f"{change:+.1f}%", style={"color": trend_color, "fontWeight": "600", "fontSize": "0.82rem"}),
                    html.Span(" vs last year", style={"color": "#8898aa", "fontSize": "0.72rem", "marginLeft": "2px"}),
                ], className="text-center mb-2"),
                html.Div([
                    html.Div(style={"flex": str(pct_filled), "height": "10px", "background": sc, "borderRadius": "5px 0 0 5px"}),
                    html.Div(style={"flex": str(100 - pct_filled), "height": "10px", "background": "#dee2e6", "borderRadius": "0 5px 5px 0"}),
                ], className="d-flex", style={"borderRadius": "5px", "overflow": "hidden"}),
                html.Div([
                    html.Span(f"Threshold: {threshold}%", style={"fontSize": "0.65rem", "color": "#8898aa"}),
                    html.Span(" ● ", style={"color": "#dee2e6", "fontSize": "0.65rem"}),
                    html.Span(status, style={"fontSize": "0.72rem", "fontWeight": "700", "color": sc}),
                ], className="text-center mt-1"),
            ], className="p-3")
        ], className="housing-kpi-card h-100", style=AffordabilityKPICard._card_style())

    # ── KPI 25: Affordability Ranking ───────────────────────────────────
    @staticmethod
    def create_ranking_card(value: float, unit: str = "/ 16",
                             trend: str = "down", region_count: int = 16,
                             best_region: str = "", worst_region: str = "",
                             sparkline: list = None, by_region: dict = None):
        accent = AffordabilityKPICard._accent_colors["ranking"]
        trend_icon = "↑" if trend == "up" else "↓"
        trend_color = "#28a745" if trend == "down" else "#dc3545"

        return dbc.Card([
            dbc.CardBody([
                html.H6("KPI 25 — Affordability Ranking", style=AffordabilityKPICard._title_style()),
                html.P("National Position (1=Best, 16=Worst)", className="text-muted mb-1", style={"fontSize": "0.78rem"}),
                html.Div([
                    html.Span(f"#{int(value)}",
                              style={"fontSize": "3rem", "fontWeight": "700", "lineHeight": "1", "color": accent}),
                    html.Span(f" / {region_count}", style={"fontSize": "1rem", "color": "#6c757d", "marginLeft": "2px"}),
                    html.Span(trend_icon, style={"fontSize": "1.4rem", "color": trend_color, "marginLeft": "6px"}),
                ], className="d-flex align-items-center justify-content-center mb-1"),
                html.Div([
                    html.Span("of 16 regions", style={"color": "#8898aa", "fontSize": "0.78rem"}),
                ], className="text-center mb-2"),
                AffordabilityKPICard._sparkline_bars(sparkline, 90, 24, color=accent) if sparkline else None,
                html.Hr(style={"margin": "8px 0 6px"}),
                html.Div([
                    html.Span("Best: ", style={"fontSize": "0.65rem", "color": "#28a745"}),
                    html.Span(best_region, style={"fontSize": "0.72rem", "fontWeight": "700", "color": "#28a745"}),
                    html.Span("  |  Worst: ", style={"fontSize": "0.65rem", "color": "#dc3545", "marginLeft": "6px"}),
                    html.Span(worst_region, style={"fontSize": "0.72rem", "fontWeight": "700", "color": "#dc3545"}),
                ], className="text-center"),
            ], className="p-3")
        ], className="housing-kpi-card h-100", style=AffordabilityKPICard._card_style())

    # ── KPI 26: Demographics vs Housing Gap ─────────────────────────────
    @staticmethod
    def create_gap_card(value: float, unit: str = "%",
                         trend: str = "up", status: str = "Growing Gap",
                         sparkline: list = None,
                         by_region_growth: dict = None,
                         by_region_supply: dict = None):
        accent = AffordabilityKPICard._accent_colors["gap"]
        trend_color = "#dc3545" if trend == "up" else "#28a745"
        trend_icon = "↑" if trend == "up" else "↓"

        gap_colors = {"Growing Gap": "#dc3545", "Stable": "#ffc107", "Improving": "#28a745"}
        gc = gap_colors.get(status, "#6c757d")

        return dbc.Card([
            dbc.CardBody([
                html.H6("KPI 26 — Demographics vs Housing Gap", style=AffordabilityKPICard._title_style()),
                html.P("Population Growth - Housing Supply (%)", className="text-muted mb-1", style={"fontSize": "0.78rem"}),
                html.Div([
                    html.Span(f"{value:+.2f}",
                              style={"fontSize": "2.8rem", "fontWeight": "700", "lineHeight": "1", "color": accent}),
                    html.Span("%", style={"fontSize": "1.2rem", "color": accent, "marginLeft": "2px"}),
                    html.Span(trend_icon, style={"fontSize": "1.4rem", "color": trend_color, "marginLeft": "6px"}),
                ], className="d-flex align-items-center justify-content-center mb-1"),
                html.Div([
                    html.Span(status, style={"color": gc, "fontWeight": "700", "fontSize": "0.85rem"}),
                ], className="text-center mb-2"),
                html.Hr(style={"margin": "6px 0"}),
                html.Div([
                    html.Div([
                        html.Span("Pop growth avg: ", style={"fontSize": "0.65rem", "color": "#8898aa"}),
                        html.Span(f"{np.mean(list(by_region_growth.values())):.1f}%",
                                  style={"fontSize": "0.75rem", "fontWeight": "700", "color": "#D35400"}),
                    ], className="mb-1"),
                    html.Div([
                        html.Span("Housing avg: ", style={"fontSize": "0.65rem", "color": "#8898aa"}),
                        html.Span(f"{np.mean(list(by_region_supply.values())):.1f}%",
                                  style={"fontSize": "0.75rem", "fontWeight": "700", "color": "#2E86AB"}),
                    ]),
                ], className="text-center"),
            ], className="p-3")
        ], className="housing-kpi-card h-100", style=AffordabilityKPICard._card_style())

    # ── KPI 27: Net Internal Migration ─────────────────────────────────
    @staticmethod
    def create_migration_card(value: float, unit: str = "people/yr",
                               trend: str = "up", inflow_count: int = 5,
                               outflow_count: int = 4,
                               inflow_regions: list = None,
                               outflow_regions: list = None,
                               by_region: dict = None):
        accent = AffordabilityKPICard._accent_colors["migration"]
        is_positive = value >= 0

        return dbc.Card([
            dbc.CardBody([
                html.H6("KPI 27 — Net Internal Migration", style=AffordabilityKPICard._title_style()),
                html.P("People Moving In/Out", className="text-muted mb-1", style={"fontSize": "0.78rem"}),
                html.Div([
                    html.Span("+" if is_positive else "",
                              style={"fontSize": "2rem", "color": "#28a745", "fontWeight": "700"}),
                    html.Span(f"{abs(value):,}",
                              style={"fontSize": "2.8rem", "fontWeight": "700", "lineHeight": "1",
                                     "color": "#28a745" if is_positive else "#dc3545"}),
                    html.Span(" / yr", style={"fontSize": "0.9rem", "color": "#6c757d", "marginLeft": "2px"}),
                ], className="d-flex align-items-center justify-content-center mb-1"),
                html.Div([
                    html.Div([
                        html.Span("Inflow: ", style={"fontSize": "0.72rem", "color": "#28a745"}),
                        html.Span(str(inflow_count), style={"fontSize": "0.82rem", "fontWeight": "700", "color": "#28a745"}),
                        html.Span(" regions", style={"fontSize": "0.72rem", "color": "#8898aa"}),
                    ], className="d-inline-block mr-3"),
                    html.Div([
                        html.Span("Outflow: ", style={"fontSize": "0.72rem", "color": "#dc3545"}),
                        html.Span(str(outflow_count), style={"fontSize": "0.82rem", "fontWeight": "700", "color": "#dc3545"}),
                        html.Span(" regions", style={"fontSize": "0.72rem", "color": "#8898aa"}),
                    ], className="d-inline-block"),
                ], className="text-center mb-2"),
                html.Hr(style={"margin": "6px 0"}),
                html.Div([
                    html.Span("Top inflow: ", style={"fontSize": "0.65rem", "color": "#8898aa"}),
                    html.Span(", ".join((inflow_regions or [])[:3]),
                              style={"fontSize": "0.72rem", "fontWeight": "600", "color": "#28a745"}),
                ], className="text-center"),
            ], className="p-3")
        ], className="housing-kpi-card h-100", style=AffordabilityKPICard._card_style())


class ForecastKPICard:
    """KPIs 28-34: Forecast & Risk (Price Forecast, Confidence, OCR/Tourism Impact, Risk, Model Confidence)."""

    _accent_colors = {
        "forecast": "#2E86AB",
        "confidence": "#148F77",
        "ocr": "#1A5276",
        "tourism": "#D35400",
        "risk": "#E74C3C",
        "model": "#8E44AD",
    }

    @staticmethod
    def _card_style() -> dict:
        return {
            "borderRadius": "12px",
            "border": "1px solid rgba(0,0,0,0.06)",
            "boxShadow": "0 2px 8px rgba(0,0,0,0.06)",
            "background": "#fff",
        }

    @staticmethod
    def _title_style() -> dict:
        return {
            "fontSize": "0.68rem",
            "fontWeight": "600",
            "color": "#8898aa",
            "letterSpacing": "0.5px",
            "textTransform": "uppercase",
            "marginBottom": "4px",
        }

    @staticmethod
    def _sparkline_line(data: list, width: int = 100, height: int = 28,
                        color: str = "#2E86AB") -> html.Div:
        if not data:
            return html.Div()
        bars = []
        max_v, min_v = max(data), min(data)
        rng = max_v - min_v if max_v != min_v else 1
        for v in data:
            bar_h = max(2, int((v - min_v) / rng * (height - 4)))
            bars.append(html.Div(style={
                "flex": "1", "height": f"{bar_h}px",
                "background": color, "borderRadius": "1px 1px 0 0", "margin": "0 0.5px",
            }))
        return html.Div(bars, style={"display": "flex", "alignItems": "flex-end", "gap": "1px", "height": f"{height}px"})

    def _range_bar(low: float, high: float, midpoint: float, color: str) -> html.Div:
        rng_span = high - low
        low_pct = (low / midpoint) * 50
        mid_pct = ((midpoint - low) / rng_span) * 100
        high_pct = ((high - midpoint) / rng_span) * 100
        return html.Div([
            html.Div(style={"flex": str(low_pct), "height": "8px", "background": "#dee2e6"}),
            html.Div(style={"flex": str(mid_pct), "height": "8px", "background": color}),
            html.Div(style={"flex": str(high_pct), "height": "8px", "background": "#dee2e6"}),
        ], style={"display": "flex", "borderRadius": "4px", "overflow": "hidden"})

    # ── KPI 28: 12-Month Price Forecast ─────────────────────────────────
    @staticmethod
    def create_price_forecast_card(value: float, unit: str = "NZD",
                                     current: float = 0, change_pct: float = 0,
                                     trend: str = "up",
                                     sparkline: list = None,
                                     forecast_series: list = None):
        accent = ForecastKPICard._accent_colors["forecast"]
        trend_color = "#28a745" if trend == "up" else "#dc3545"
        trend_icon = "↑" if trend == "up" else "↓"

        return dbc.Card([
            dbc.CardBody([
                html.H6("KPI 28 — 12-Month Price Forecast", style=ForecastKPICard._title_style()),
                html.P("Median Price Forecast", className="text-muted mb-1", style={"fontSize": "0.78rem"}),
                html.Div([
                    html.Span(f"${value:,.0f}",
                              style={"fontSize": "2.4rem", "fontWeight": "700", "lineHeight": "1", "color": accent}),
                ], className="text-center mb-1"),
                html.Div([
                    html.Span(f"{change_pct:+.1f}%", style={"color": trend_color, "fontWeight": "600", "fontSize": "0.85rem"}),
                    html.Span(" vs current", style={"color": "#8898aa", "fontSize": "0.72rem", "marginLeft": "2px"}),
                    html.Span(trend_icon, style={"color": trend_color, "marginLeft": "4px"}),
                ], className="text-center mb-2"),
                ForecastKPICard._sparkline_line(sparkline, 100, 28, color=accent) if sparkline else None,
                html.Hr(style={"margin": "8px 0 6px"}),
                html.Div([
                    html.Span("Current: ", style={"fontSize": "0.65rem", "color": "#8898aa"}),
                    html.Span(f"${current:,.0f}", style={"fontSize": "0.75rem", "fontWeight": "600", "color": "#495057"}),
                ], className="text-center"),
            ], className="p-3")
        ], className="housing-kpi-card h-100", style=ForecastKPICard._card_style())

    # ── KPI 29: Confidence Range ─────────────────────────────────────────
    @staticmethod
    def create_confidence_range_card(range_80_low: float, range_80_high: float,
                                      range_95_low: float, range_95_high: float,
                                      midpoint: float = 0):
        accent = ForecastKPICard._accent_colors["confidence"]

        return dbc.Card([
            dbc.CardBody([
                html.H6("KPI 29 — Confidence Range", style=ForecastKPICard._title_style()),
                html.P("Prediction Interval", className="text-muted mb-2", style={"fontSize": "0.78rem"}),
                html.Div([
                    html.Span(f"${range_80_low:,.0f}", style={"fontSize": "1.0rem", "fontWeight": "700", "color": accent}),
                    html.Span(" → ", style={"fontSize": "0.9rem", "color": "#dee2e6"}),
                    html.Span(f"${range_80_high:,.0f}", style={"fontSize": "1.0rem", "fontWeight": "700", "color": accent}),
                ], className="text-center mb-1"),
                html.Div([
                    html.Span("80% interval", style={"fontSize": "0.65rem", "color": "#8898aa"}),
                ], className="text-center mb-2"),
                html.Div([
                    html.Div(style={"flex": "1", "height": "6px", "background": "#dee2e6", "borderRadius": "3px 0 0 3px"}),
                    html.Div(style={"flex": "0", "height": "6px"}),
                    html.Div(style={"flex": "1", "height": "6px", "background": accent, "borderRadius": "0 3px 3px 0"}),
                ], className="d-flex mb-1"),
                html.Div([
                    html.Span(f"95%: ${range_95_low:,.0f} – ${range_95_high:,.0f}",
                              style={"fontSize": "0.65rem", "color": "#8898aa"}),
                ], className="text-center"),
            ], className="p-3")
        ], className="housing-kpi-card h-100", style=ForecastKPICard._card_style())

    # ── KPI 30: OCR +0.5% Impact ─────────────────────────────────────────
    @staticmethod
    def create_ocr_impact_card(value: float, unit: str = "%",
                                 direction: str = "down",
                                 base_ocr: float = 3.50,
                                 scenario_ocr: float = 4.00):
        accent = ForecastKPICard._accent_colors["ocr"]
        direction_color = "#dc3545" if direction == "down" else "#28a745"
        direction_icon = "↓" if direction == "down" else "↑"

        return dbc.Card([
            dbc.CardBody([
                html.H6("KPI 30 — OCR +0.5% Impact", style=ForecastKPICard._title_style()),
                html.P("Interest Rate Sensitivity", className="text-muted mb-1", style={"fontSize": "0.78rem"}),
                html.Div([
                    html.Span(f"{value:+.1f}",
                              style={"fontSize": "2.8rem", "fontWeight": "700", "lineHeight": "1", "color": direction_color}),
                    html.Span("%", style={"fontSize": "1.2rem", "color": direction_color}),
                    html.Span(direction_icon, style={"fontSize": "1.4rem", "color": direction_color, "marginLeft": "6px"}),
                ], className="d-flex align-items-center justify-content-center mb-1"),
                html.Div([
                    html.Span("on house prices", style={"color": "#8898aa", "fontSize": "0.78rem"}),
                ], className="text-center mb-2"),
                html.Hr(style={"margin": "6px 0"}),
                html.Div([
                    html.Span(f"OCR {base_ocr:.2f}% → {scenario_ocr:.2f}%", style={"fontSize": "0.72rem", "fontWeight": "600", "color": accent}),
                ], className="text-center"),
            ], className="p-3")
        ], className="housing-kpi-card h-100", style=ForecastKPICard._card_style())

    # ── KPI 31: Tourism +20% Impact on DOM ─────────────────────────────
    @staticmethod
    def create_tourism_impact_card(value: float, unit: str = "days",
                                    direction: str = "up",
                                    scenario_pct: int = 20):
        accent = ForecastKPICard._accent_colors["tourism"]
        direction_color = "#dc3545" if direction == "up" else "#28a745"
        direction_icon = "↑" if direction == "up" else "↓"

        return dbc.Card([
            dbc.CardBody([
                html.H6("KPI 31 — Tourism +20% Impact (DOM)", style=ForecastKPICard._title_style()),
                html.P("Tourism Scenario Effect", className="text-muted mb-1", style={"fontSize": "0.78rem"}),
                html.Div([
                    html.Span(f"+{value:.0f}" if direction == "up" else f"{value:.0f}",
                              style={"fontSize": "2.8rem", "fontWeight": "700", "lineHeight": "1", "color": direction_color}),
                    html.Span(" days", style={"fontSize": "1rem", "color": "#6c757d", "marginLeft": "2px"}),
                    html.Span(direction_icon, style={"fontSize": "1.4rem", "color": direction_color, "marginLeft": "6px"}),
                ], className="d-flex align-items-center justify-content-center mb-1"),
                html.Div([
                    html.Span(f"if tourism +{scenario_pct}%", style={"color": "#8898aa", "fontSize": "0.78rem"}),
                ], className="text-center mb-2"),
                html.Hr(style={"margin": "6px 0"}),
                html.Div([
                    html.Span("DOM increase expected", style={"fontSize": "0.68rem", "color": "#8898aa"}),
                ], className="text-center"),
            ], className="p-3")
        ], className="housing-kpi-card h-100", style=ForecastKPICard._card_style())

    # ── KPI 33: High Risk Regions ───────────────────────────────────────
    @staticmethod
    def create_risk_regions_card(regions: list = None,
                                  risk_data: dict = None,
                                  count: int = 7):
        accent = ForecastKPICard._accent_colors["risk"]
        if regions is None:
            regions = ["Auckland", "Wellington", "Christchurch", "Hamilton", "Dunedin", "Tauranga", "Queenstown"]

        region_tags = []
        for r in regions[:5]:
            risk_level = (risk_data or {}).get(r, {}).get("risk", "Moderate")
            tag_color = "#dc3545" if risk_level == "High" else "#ffc107"
            region_tags.append(html.Span(r, style={
                "fontSize": "0.68rem", "fontWeight": "600",
                "background": tag_color + "20", "color": tag_color,
                "padding": "2px 8px", "borderRadius": "4px", "marginRight": "4px",
            }))
        if len(regions) > 5:
            region_tags.append(html.Span(f"+{len(regions) - 5}", style={
                "fontSize": "0.68rem", "color": "#8898aa",
            }))

        return dbc.Card([
            dbc.CardBody([
                html.H6("KPI 33 — High Risk Regions", style=ForecastKPICard._title_style()),
                html.P("Divergence Alert", className="text-muted mb-2", style={"fontSize": "0.78rem"}),
                html.Div([
                    html.Span(f"{count}",
                              style={"fontSize": "2.8rem", "fontWeight": "700", "lineHeight": "1", "color": accent}),
                    html.Span(" regions", style={"fontSize": "1rem", "color": "#6c757d", "marginLeft": "2px"}),
                ], className="text-center mb-2"),
                html.Div(region_tags, className="d-flex flex-wrap gap-1"),
            ], className="p-3")
        ], className="housing-kpi-card h-100", style=ForecastKPICard._card_style())

    # ── KPI 34: Model Confidence Score ──────────────────────────────────
    @staticmethod
    def create_model_confidence_card(value: float, unit: str = "/100",
                                      metrics: dict = None):
        accent = ForecastKPICard._accent_colors["model"]

        mape = (metrics or {}).get("MAPE", 4.2)
        r2 = (metrics or {}).get("R-squared", 0.85)

        fill_pct = min(value, 100)

        return dbc.Card([
            dbc.CardBody([
                html.H6("KPI 34 — Model Confidence Score", style=ForecastKPICard._title_style()),
                html.P("Model Reliability", className="text-muted mb-1", style={"fontSize": "0.78rem"}),
                html.Div([
                    html.Span(f"{value:.0f}",
                              style={"fontSize": "2.8rem", "fontWeight": "700", "lineHeight": "1", "color": accent}),
                    html.Span("/100", style={"fontSize": "1rem", "color": "#6c757d"}),
                ], className="text-center mb-2"),
                html.Div([
                    html.Div(style={"flex": str(fill_pct), "height": "8px", "background": accent, "borderRadius": "4px 0 0 4px"}),
                    html.Div(style={"flex": str(100 - fill_pct), "height": "8px", "background": "#dee2e6", "borderRadius": "0 4px 4px 0"}),
                ], className="d-flex mb-2", style={"borderRadius": "4px", "overflow": "hidden"}),
                html.Hr(style={"margin": "6px 0"}),
                html.Div([
                    html.Span(f"MAPE: {mape:.1f}%", style={"fontSize": "0.68rem", "color": "#8898aa", "marginRight": "8px"}),
                    html.Span(f"R²: {r2:.2f}", style={"fontSize": "0.68rem", "color": "#8898aa"}),
                ], className="text-center"),
            ], className="p-3")
        ], className="housing-kpi-card h-100", style=ForecastKPICard._card_style())
