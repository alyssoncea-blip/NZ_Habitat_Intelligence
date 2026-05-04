"""
Layout principal do dashboard
Header, sidebar e estrutura base
"""
import dash_bootstrap_components as dbc
from dash import html, dcc
from .navigation import create_navbar

def create_layout():
    """Create the main dashboard layout."""
    return dbc.Container(
        fluid=True,
        className="dashboard-container",
        children=[
            dcc.Location(id="url", refresh=False),
            dcc.Interval(id="interval-update", interval=60 * 1000, n_intervals=0),

            # Header 
            create_navbar(),

            # Main content
            dbc.Row([
                dbc.Col([
                    html.Main(id="page-content", className="page-content")
                ], width=12)
            ], className="content-row", style={"paddingTop": "88px"}),

            html.Div(id="data-quality-indicator", style={"display": "none"}),
            
            # Footer
            dbc.Row([
                dbc.Col([
                    html.Footer([
                        html.P([
                            "© 2026 NZ Habitat Intelligence Dashboard | ",
                            html.A("Data Sources", href="#data-sources", className="footer-link"),
                            " | ",
                            html.A("Methodology", href="#methodology", className="footer-link"),
                            " | ",
                            html.A("About", href="#about", className="footer-link")
                        ], className="footer-text")
                    ], className="dashboard-footer")
                ], width=12)
            ], className="footer-row")
        ]
    )

def create_section_header(title, subtitle=None):
    """Create a premium section header"""
    children = [
        html.H2(title, className="section-title")
    ]
    
    if subtitle:
        children.append(
            html.P(subtitle, className="section-subtitle")
        )
    
    return dbc.Row([
        dbc.Col(children, width=12)
    ], className="section-header")


def create_hero_section(title, kpi_value, kpi_subtitle=None):
    """Create a hero section for main KPI"""
    children = [
        html.H1(title, className="hero-title"),
        html.Div(str(kpi_value), className="hero-kpi-value"),
    ]

    if kpi_subtitle:
        children.append(
            html.P(kpi_subtitle, className="hero-subtitle")
        )

    return dbc.Row([
        dbc.Col(
            dbc.Card(
                dbc.CardBody(children),
                className="hero-card"
            ),
            width=12
        )
    ], className="hero-section")


def create_filter_bar(region_options, time_options):
    """
    Create the filter bar for the Executive Dashboard.
    
    Args:
        region_options: Lista de regiões para o dropdown
        time_options: Lista de opções de tempo (3M, 6M, 12M, etc.)
    
    Returns:
        Componente Dash com filtros de região e período
    """
    return dbc.Row([
        dbc.Col([
            html.Div([
                html.Span("Filters", className="me-3 text-muted", style={"fontSize": "0.85rem"}),
                
                # Region Selector
                dcc.Dropdown(
                    id="region-selector",
                    options=[{"label": r, "value": r} for r in region_options],
                    value="All Regions",
                    placeholder="Select Region",
                    clearable=False,
                    style={"width": "180px", "display": "inline-block"}
                ),
                
                html.Span("|", className="mx-3 text-muted"),
                
                # Time Selector Buttons
                dbc.ButtonGroup([
                    dbc.Button("3M", id="btn-3m", color="outline-primary", size="sm", active=True),
                    dbc.Button("6M", id="btn-6m", color="outline-primary", size="sm"),
                    dbc.Button("12M", id="btn-12m", color="outline-primary", size="sm"),
                    dbc.Button("1Y", id="btn-1y", color="outline-primary", size="sm"),
                    dbc.Button("5Y", id="btn-5y", color="outline-primary", size="sm"),
                ], size="sm")
                
            ], className="d-flex align-items-center justify-content-end py-2")
        ], width=12)
    ], className="filter-bar bg-white border-bottom",
        style={"position": "sticky", "top": "56px", "zIndex": "1020", "padding": "8px 24px"})


def create_loading_spinner(component_id: str, children=None, spinner_type: str = "default"):
    """Wrap a component with a loading spinner.

    Args:
        component_id: ID for the loading wrapper.
        children: Component(s) to wrap.
        spinner_type: 'default', 'graph', 'cube', 'circle', or 'dot'.

    Returns:
        dcc.Loading component with spinner.
    """
    valid_types = {"graph", "cube", "circle", "dot", "default"}
    spinner_type = spinner_type if spinner_type in valid_types else "default"

    return dcc.Loading(
        id=f"loading-{component_id}",
        type=spinner_type,
        color="#2E86AB",
        children=children or html.Div(id=f"{component_id}-loading-placeholder"),
        style={"minHeight": "50px"},
    )


def create_skeleton_card(width: int = 2):
    """Create a skeleton placeholder card for loading states."""
    return dbc.Col(
        dbc.Card(
            dbc.CardBody([
                html.Div(
                    style={
                        "backgroundColor": "#e9ecef",
                        "height": "12px",
                        "width": "60%",
                        "borderRadius": "4px",
                        "marginBottom": "8px",
                    }
                ),
                html.Div(
                    style={
                        "backgroundColor": "#e9ecef",
                        "height": "28px",
                        "width": "80%",
                        "borderRadius": "4px",
                        "marginBottom": "8px",
                    }
                ),
                html.Div(
                    style={
                        "backgroundColor": "#e9ecef",
                        "height": "10px",
                        "width": "40%",
                        "borderRadius": "4px",
                    }
                ),
            ]),
            className="skeleton-card",
        ),
        width=width,
        className="mb-3",
    )


def create_skeleton_row(n_cards: int = 6):
    """Create a row of skeleton cards for loading states."""
    return dbc.Row(
        [create_skeleton_card(width=12 // n_cards) for _ in range(n_cards)],
        className="g-3 mb-4",
    )
