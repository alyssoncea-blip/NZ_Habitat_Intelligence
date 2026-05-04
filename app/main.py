"""
NZ Habitat Intelligence Dashboard - Main Application
Modular entry point with premium structure
"""
import dash
import dash_bootstrap_components as dbc
from dash import html, dcc
import pandas as pd
from .components.layout import create_layout
from .pages import (
    create_executive_dashboard,
    create_housing_dashboard,
    create_tourism_dashboard,
    create_macro_dashboard,
    create_affordability_dashboard,
    create_forecast_dashboard
)
from .utils.logger import get_logger

# App configuration
logger = get_logger(__name__)
app = dash.Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        "https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&display=swap"
    ],
    suppress_callback_exceptions=True,
    meta_tags=[
        {"name": "viewport", "content": "width=device-width, initial-scale=1"}
    ]
)

app.title = "NZ Habitat Intelligence Dashboard - Premium Edition"
server = app.server

# Main layout
app.layout = create_layout()

# Export modal
export_modal = dbc.Modal(
    [
        dbc.ModalHeader(dbc.ModalTitle("Export Dashboard")),
        dbc.ModalBody([
            html.P("Choose export format:"),
            dbc.ButtonGroup([
                dbc.Button("PNG Image", id="btn-export-png", color="primary", className="me-2"),
                dbc.Button("SVG Vector", id="btn-export-svg", color="secondary", className="me-2"),
                dbc.Button("HTML Report", id="btn-export-html", color="info"),
            ], className="w-100"),
            html.Hr(),
            html.Small("Charts export via Plotly. Full page export uses browser print-to-PDF.", className="text-muted"),
        ]),
        dbc.ModalFooter(
            dbc.Button("Close", id="btn-close-export-modal", color="secondary")
        ),
    ],
    id="export-modal",
    size="sm",
    centered=True,
)

app.layout = html.Div([
    create_layout(),
    export_modal,
    dcc.Download(id="download-export"),
])

# Navigation callbacks
@app.callback(
    dash.dependencies.Output("page-content", "children"),
    [dash.dependencies.Input("url", "pathname")]
)
def display_page(pathname):
    """Route pages"""
    logger.info(f"Navigating to: {pathname}")
    
    if pathname == "/" or pathname == "/executive":
        return create_executive_dashboard()
    elif pathname == "/housing":
        return create_housing_dashboard()
    elif pathname == "/tourism":
        return create_tourism_dashboard()
    elif pathname == "/macro":
        return create_macro_dashboard()
    elif pathname == "/affordability":
        return create_affordability_dashboard()
    elif pathname == "/forecast":
        return create_forecast_dashboard()
    else:
        return html.Div([
            html.H1("404: Page not found", className="text-danger"),
            html.P(f"The pathname {pathname} was not recognized."),
            html.A("Go to Executive Dashboard", href="/", className="btn btn-primary")
        ])

# Additional callbacks (examples)
@app.callback(
    dash.dependencies.Output("data-quality-indicator", "children"),
    [dash.dependencies.Input("interval-update", "n_intervals")]
)
def update_quality_indicator(n):
    """Update data quality indicator"""
    # Implementation will be added later
    return "Data Quality: Good"

@app.callback(
    dash.dependencies.Output("last-update-time", "children"),
    [dash.dependencies.Input("interval-update", "n_intervals")]
)
def update_last_update_time(n):
    """Update last update timestamp"""
    from datetime import datetime
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return f"Last updated: {now}"


@app.callback(
    dash.dependencies.Output("export-modal", "is_open"),
    [
        dash.dependencies.Input("btn-export", "n_clicks"),
        dash.dependencies.Input("btn-close-export-modal", "n_clicks"),
    ],
    [dash.dependencies.State("export-modal", "is_open")],
    prevent_initial_call=True,
)
def toggle_export_modal(btn_export, btn_close, is_open):
    """Toggle export modal visibility."""
    if dash.ctx.triggered_id:
        return not is_open
    return is_open


app.clientside_callback(
    """
    function(n_clicks) {
        if (!n_clicks) return window.dash_clientside.no_update;
        
        const exportDiv = document.createElement('div');
        exportDiv.style.position = 'fixed';
        exportDiv.style.top = '0';
        exportDiv.style.left = '0';
        exportDiv.style.width = '100%';
        exportDiv.style.height = '100%';
        exportDiv.style.backgroundColor = 'white';
        exportDiv.style.zIndex = '10000';
        exportDiv.style.padding = '20px';
        exportDiv.style.overflow = 'auto';
        
        const title = document.createElement('h1');
        title.textContent = 'NZ Habitat Intelligence Dashboard';
        title.style.textAlign = 'center';
        title.style.marginBottom = '10px';
        exportDiv.appendChild(title);
        
        const timestamp = document.createElement('p');
        timestamp.textContent = 'Generated: ' + new Date().toLocaleString();
        timestamp.style.textAlign = 'center';
        timestamp.style.color = '#666';
        timestamp.style.marginBottom = '20px';
        exportDiv.appendChild(timestamp);
        
        const plotlyDivs = document.querySelectorAll('.js-plotly-plot');
        plotlyDivs.forEach(function(div) {
            const clone = div.cloneNode(true);
            clone.style.width = '100%';
            clone.style.height = '400px';
            clone.style.marginBottom = '20px';
            clone.style.pageBreakInside = 'avoid';
            exportDiv.appendChild(clone);
        });
        
        document.body.appendChild(exportDiv);
        
        setTimeout(function() {
            window.print();
            document.body.removeChild(exportDiv);
        }, 500);
        
        return window.dash_clientside.no_update;
    }
    """,
    dash.dependencies.Output("download-export", "id"),
    [dash.dependencies.Input("btn-export-html", "n_clicks")],
)


@app.callback(
    [
        dash.dependencies.Output("page-content", "className", allow_duplicate=True),
        dash.dependencies.Output("btn-dark-mode", "children"),
        dash.dependencies.Output("url", "refresh"),
    ],
    [dash.dependencies.Input("btn-dark-mode", "n_clicks")],
    [dash.dependencies.State("page-content", "className")],
    prevent_initial_call=True,
)
def toggle_dark_mode(n_clicks, current_class):
    """Toggle dark mode on/off."""
    if not n_clicks:
        return current_class or "", "🌙", False

    is_dark = current_class and "dark-mode" in current_class
    if is_dark:
        new_class = current_class.replace("dark-mode", "").strip()
        return new_class, "🌙", False
    else:
        new_class = f"{current_class or ''} dark-mode"
        return new_class, "☀️", False


# Custom CSS is served automatically from app/assets/style.css by Dash

def run_app(debug=True, host='0.0.0.0', port=8050):
    """Run the application"""
    logger.info("=" * 60)
    logger.info("Starting NZ Habitat Intelligence Dashboard - Premium Edition")
    logger.info("=" * 60)
    
    print("\n" + "=" * 60)
    print("NZ HABITAT INTELLIGENCE DASHBOARD")
    print("=" * 60)
    print("Dashboard Modular - Premium Executive Design")
    print(f"URL: http://{host}:{port}")
    print("=" * 60 + "\n")
    
    app.run(debug=debug, host=host, port=port)

if __name__ == "__main__":
    run_app()
