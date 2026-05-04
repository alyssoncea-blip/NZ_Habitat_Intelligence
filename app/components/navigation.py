"""
Components de navigation para dashboard premium
Navbar, sidebar e elementos de navigation
"""
import dash_bootstrap_components as dbc
from dash import html, dcc

def create_navbar():
    """Create premium dashboard navbar."""
    return dbc.Navbar(
        dbc.Container([
            # Logo e brand
            dbc.NavbarBrand([
                html.Div(
                    "NZ",
                    className="navbar-logo",
                    style={
                        "width": "40px",
                        "height": "40px",
                        "display": "flex",
                        "alignItems": "center",
                        "justifyContent": "center",
                        "background": "#2E86AB",
                        "color": "#ffffff",
                        "borderRadius": "10px",
                        "fontWeight": "700",
                        "letterSpacing": "0.04em"
                    }
                ),
                html.Div([
                    html.Span(
                        "NZ Habitat Intelligence Dashboard",
                        className="navbar-brand-text"
                    ),
                    html.Small(
                        "Premium Executive Edition",
                        className="navbar-subtitle"
                    )
                ], className="navbar-brand-copy")
            ], href="/"),
            
            # Right-side controls
            dbc.NavbarToggler(id="navbar-toggler"),
            
            dbc.Collapse(
                dbc.Row([
                    # Links de navigation
                    dbc.Col(
                        dbc.Nav([
                            dbc.NavItem(dbc.NavLink("Executive", href="/", active="exact", className="nav-link-custom")),
                            dbc.NavItem(dbc.NavLink("Housing", href="/housing", active="exact", className="nav-link-custom")),
                            dbc.NavItem(dbc.NavLink("Tourism", href="/tourism", active="exact", className="nav-link-custom")),
                            dbc.NavItem(dbc.NavLink("Macro", href="/macro", active="exact", className="nav-link-custom")),
                            dbc.NavItem(dbc.NavLink("Affordability", href="/affordability", active="exact", className="nav-link-custom")),
                            dbc.NavItem(dbc.NavLink("Forecast", href="/forecast", active="exact", className="nav-link-custom")),
                        ], navbar=True),
                        width="auto",
                        className="nav-links-col"
                    ),
                    
                    # Indicador de status
                    dbc.Col([
                        html.Div([
                            html.Span("●", className="status-dot status-live"),
                            html.Span("Live Data", className="status-text")
                        ], className="status-indicator"),
                        html.Small(id="last-update-time", className="update-time")
                    ], width="auto", className="status-col"),
                    
                    # Action buttons
                    dbc.Col(
                        dbc.ButtonGroup([
                            dbc.Button(
                                "🌙",
                                id="btn-dark-mode",
                                color="outline-light",
                                size="sm",
                                title="Toggle dark mode",
                            ),
                            dbc.Button(
                                "Refresh",
                                id="btn-refresh",
                                color="primary",
                                size="sm",
                                outline=True
                            ),
                            dbc.Button(
                                "Export",
                                id="btn-export",
                                color="secondary", 
                                size="sm",
                                outline=True
                            ),
                            dbc.DropdownMenu(
                                label="More",
                                children=[
                                    dbc.DropdownMenuItem("Settings", id="menu-settings"),
                                    dbc.DropdownMenuItem("Help", id="menu-help"),
                                    dbc.DropdownMenuItem(divider=True),
                                    dbc.DropdownMenuItem("About", id="menu-about"),
                                ],
                                size="sm",
                                className="more-menu"
                            )
                        ]),
                        width="auto",
                        className="action-buttons-col"
                    ),
                ], className="g-0"),
                id="navbar-collapse",
                is_open=False,
                navbar=True,
            ),
        ], fluid=True),
        color="dark",
        dark=True,
        className="dashboard-navbar",
        fixed="top"
    )

def create_sidebar():
    """Create sidebar for lateral navigation (optional)."""
    return html.Div(
        id="sidebar",
        className="dashboard-sidebar",
        children=[
            html.Div([
                html.H5("Dashboards", className="sidebar-title"),
                dcc.Link("Executive Overview", href="/", className="sidebar-link"),
                dcc.Link("Housing Market", href="/housing", className="sidebar-link"),
                dcc.Link("Tourism Impact", href="/tourism", className="sidebar-link"),
                dcc.Link("Macroeconomic", href="/macro", className="sidebar-link"),
                dcc.Link("Affordability", href="/affordability", className="sidebar-link"),
                dcc.Link("Forecast & Risk", href="/forecast", className="sidebar-link"),
            ], className="sidebar-section"),
            
            html.Hr(),
            
            html.Div([
                html.H5("Filters", className="sidebar-title"),
                html.Label("Time Range", className="filter-label"),
                dcc.Dropdown(
                    id="time-range-filter",
                    options=[
                        {"label": "Last Month", "value": "1M"},
                        {"label": "Last Quarter", "value": "3M"},
                        {"label": "Last Year", "value": "1Y"},
                        {"label": "All Time", "value": "ALL"},
                    ],
                    value="1Y",
                    clearable=False,
                    className="filter-dropdown"
                ),
                
                html.Label("Regions", className="filter-label"),
                dcc.Dropdown(
                    id="region-filter",
                    options=[
                        {"label": "All Regions", "value": "all"},
                        {"label": "North Island", "value": "north"},
                        {"label": "South Island", "value": "south"},
                        {"label": "Auckland", "value": "auckland"},
                        {"label": "Wellington", "value": "wellington"},
                    ],
                    value="all",
                    multi=True,
                    className="filter-dropdown"
                ),
                
                html.Button(
                    "Apply Filters",
                    id="btn-apply-filters",
                    className="btn btn-primary btn-sm mt-3 w-100"
                ),
                html.Button(
                    "Reset Filters",
                    id="btn-reset-filters",
                    className="btn btn-outline-secondary btn-sm mt-2 w-100"
                ),
            ], className="sidebar-section"),
            
            html.Hr(),
            
            html.Div([
                html.H5("Data Quality", className="sidebar-title"),
                html.Div(id="data-quality-indicator", className="quality-indicator"),
                html.Button(
                    "Check Data Integrity",
                    id="btn-check-integrity",
                    className="btn btn-outline-info btn-sm mt-2 w-100"
                ),
                html.Small(
                    "Last checked: Today",
                    className="text-muted d-block mt-2"
                ),
            ], className="sidebar-section"),
        ]
    )

def create_breadcrumbs(current_page):
    """Create breadcrumbs for hierarchical navigation"""
    pages = {
        "/": "Executive Dashboard",
        "/housing": "Housing Market",
        "/tourism": "Tourism Impact", 
        "/macro": "Macroeconomic",
        "/affordability": "Affordability",
        "/forecast": "Forecast & Risk"
    }
    
    breadcrumb_items = []
    breadcrumb_items.append(
        dbc.BreadcrumbItem("Home", href="/")
    )
    
    if current_page != "/":
        breadcrumb_items.append(
            dbc.BreadcrumbItem(pages.get(current_page, "Page"), active=True)
        )
    
    return dbc.Breadcrumb(breadcrumb_items, className="dashboard-breadcrumbs")

def create_dashboard_switcher(current_dashboard):
    """Create dashboard selector in card format."""
    dashboards = [
        {
            "id": "executive",
            "title": "Executive",
            "icon": "📊",
            "description": "Overview & Key Metrics",
            "href": "/"
        },
        {
            "id": "housing", 
            "title": "Housing",
            "icon": "🏠",
            "description": "Market Trends & Supply",
            "href": "/housing"
        },
        {
            "id": "tourism",
            "title": "Tourism", 
            "icon": "✈️",
            "description": "Impact & Seasonality",
            "href": "/tourism"
        },
        {
            "id": "macro",
            "title": "Macro",
            "icon": "📈", 
            "description": "Economic Indicators",
            "href": "/macro"
        },
        {
            "id": "affordability",
            "title": "Affordability",
            "icon": "💰",
            "description": "Housing Costs & Ratios",
            "href": "/affordability"
        },
        {
            "id": "forecast",
            "title": "Forecast",
            "icon": "🔮",
            "description": "Predictions & Risk",
            "href": "/forecast"
        }
    ]
    
    switcher_cards = []
    
    for dashboard in dashboards:
        is_active = current_dashboard == dashboard["href"] or (
            current_dashboard == "/" and dashboard["id"] == "executive"
        )
        
        card_class = "dashboard-switcher-card"
        if is_active:
            card_class += " active"
        
        card = dbc.Card([
            dbc.CardBody([
                html.Div([
                    html.Span(dashboard["icon"], className="switcher-icon"),
                    html.H6(dashboard["title"], className="switcher-title"),
                ], className="switcher-header"),
                html.P(dashboard["description"], className="switcher-description"),
                html.A(
                    "Open Dashboard",
                    href=dashboard["href"],
                    className="btn btn-outline-primary btn-sm switcher-btn"
                )
            ])
        ], className=card_class)
        
        switcher_cards.append(
            dbc.Col(card, width=6, md=4, lg=2, className="switcher-col")
        )
    
    return dbc.Row(switcher_cards, className="dashboard-switcher-row")

def create_tab_navigation(current_view):
    """Create tab navigation for views within the dashboard."""
    tabs = []
    
    if current_view == "executive":
        tabs = [
            {"label": "Overview", "value": "overview"},
            {"label": "KPIs", "value": "kpis"},
            {"label": "Trends", "value": "trends"},
            {"label": "Insights", "value": "insights"}
        ]
    elif current_view == "housing":
        tabs = [
            {"label": "Market Overview", "value": "overview"},
            {"label": "Supply & Demand", "value": "supply"},
            {"label": "Prices & Trends", "value": "prices"},
            {"label": "Rental Market", "value": "rental"}
        ]
    elif current_view == "forecast":
        tabs = [
            {"label": "12-Month Forecast", "value": "forecast"},
            {"label": "Risk Analysis", "value": "risk"},
            {"label": "Scenarios", "value": "scenarios"},
            {"label": "Model Confidence", "value": "confidence"}
        ]
    else:
        tabs = [
            {"label": "Overview", "value": "overview"},
            {"label": "Details", "value": "details"},
            {"label": "Charts", "value": "charts"}
        ]
    
    return dbc.Tabs(
        [dbc.Tab(label=tab["label"], tab_id=f"tab-{tab['value']}") for tab in tabs],
        id="dashboard-tabs",
        active_tab=f"tab-{tabs[0]['value']}",
        className="dashboard-tabs"
    )
