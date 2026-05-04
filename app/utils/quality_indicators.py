"""
Data quality indicators
Utilities for displaying data source quality information
"""
import dash_bootstrap_components as dbc
from dash import html
import pandas as pd
from .data_loader import load_kpis_for_dashboard
from .logger import get_logger

logger = get_logger(__name__)

def get_data_quality_score(dashboard_name):
    """
    Calculate data quality score for a dashboard

    Args:
        dashboard_name: Name of the dashboard

    Returns:
        int: Quality score (0-100)
    """
    kpis_df = load_kpis_for_dashboard(dashboard_name)

    if kpis_df is None or kpis_df.empty:
        return 0

    score = 50  # Base score

    # Positive factors
    if 'source' in kpis_df.columns:
        sources = kpis_df['source'].dropna().astype(str)

        # Points for reliable sources
        if sources.str.contains('World Bank', case=False).any():
            score += 20
        if sources.str.contains('Stats NZ', case=False).any():
            score += 20
        if sources.str.contains('Real', case=False).any():
            score += 15

        # Penalties for proxy/synthetic sources
        if sources.str.contains('Synthetic', case=False).any():
            score -= 10
        if sources.str.contains('Proxy', case=False).any():
            score -= 5
        if sources.str.contains('Estimated', case=False).any():
            score -= 5

    # Points for complete structure
    required_cols = ['name', 'value', 'unit', 'description']
    if all(col in kpis_df.columns for col in required_cols):
        score += 15

    # Points for volume
    if len(kpis_df) >= 5:
        score += 5
    if len(kpis_df) >= 10:
        score += 5

    # Clamp between 0-100
    return max(0, min(100, score))

def show_data_source_info(dashboard_name):
    """
    Create component with data source information

    Args:
        dashboard_name: Name of the dashboard

    Returns:
        Dash component with information
    """
    kpis_df = load_kpis_for_dashboard(dashboard_name)

    if kpis_df is None or kpis_df.empty:
        return dbc.Alert(
            "No data available for this dashboard",
            color="warning",
            className="data-quality-alert"
        )

    # Calculate statistics
    quality_score = get_data_quality_score(dashboard_name)
    kpi_count = len(kpis_df)

    # Analyze sources
    sources = []
    if 'source' in kpis_df.columns:
        source_counts = kpis_df['source'].value_counts()
        for source, count in source_counts.items():
            if pd.notna(source):
                sources.append((source, count))

    # Determine badge color based on score
    if quality_score >= 80:
        color = "success"
        quality_text = "High Quality"
    elif quality_score >= 60:
        color = "warning"
        quality_text = "Moderate Quality"
    else:
        color = "danger"
        quality_text = "Low Quality"

    # Create component
    return dbc.Card(
        dbc.CardBody([
            html.Div([
                html.H6("Data Quality", className="quality-title"),
                dbc.Badge(f"{quality_score}/100", color=color, className="quality-badge"),
                html.Span(quality_text, className="quality-text")
            ], className="quality-header"),

            html.Hr(className="quality-divider"),

            html.Div([
                html.Small(f"KPIs: {kpi_count}", className="quality-stat"),
                html.Br(),
                html.Small(f"Sources: {len(sources)}", className="quality-stat"),
            ], className="quality-stats"),

            html.Div([
                html.Small("Sources:", className="sources-label"),
                html.Ul([
                    html.Li(f"{source} ({count} KPIs)") for source, count in sources[:3]
                ], className="sources-list")
            ], className="quality-sources") if sources else html.Div(),

            html.Div([
                html.Small(
                    "Data quality score based on source credibility, completeness, and volume",
                    className="quality-note"
                )
            ], className="quality-footer")
        ]),
        className="data-quality-card"
    )

def create_quality_indicator(dashboard_name, compact=False):
    """
    Create compact quality indicator

    Args:
        dashboard_name: Name of the dashboard
        compact: If True, shows compact version

    Returns:
        Compact component
    """
    quality_score = get_data_quality_score(dashboard_name)

    if quality_score >= 80:
        color = "success"
        icon = "check"
    elif quality_score >= 60:
        color = "warning"
        icon = "alert"
    else:
        color = "danger"
        icon = "x"

    if compact:
        return html.Span([
            html.Span(icon, className="quality-icon"),
            html.Span(f"{quality_score}", className="quality-score")
        ], className=f"quality-indicator quality-{color}")
    else:
        return html.Div([
            html.Span("Data Quality: ", className="quality-label"),
            html.Span(icon, className="quality-icon"),
            html.Span(f"{quality_score}/100", className="quality-score"),
            html.Span(f" ({get_quality_description(quality_score)})", className="quality-desc")
        ], className=f"quality-indicator quality-{color}")

def get_quality_description(score):
    """Return text description for quality score."""
    if score >= 90:
        return "Excellent"
    elif score >= 80:
        return "Very Good"
    elif score >= 70:
        return "Good"
    elif score >= 60:
        return "Moderate"
    elif score >= 50:
        return "Fair"
    elif score >= 40:
        return "Poor"
    else:
        return "Very Poor"

def check_data_completeness(dashboard_name):
    """
    Check data completeness for a dashboard

    Args:
        dashboard_name: Name of the dashboard

    Returns:
        dict: Completeness statistics
    """
    kpis_df = load_kpis_for_dashboard(dashboard_name)

    if kpis_df is None or kpis_df.empty:
        return {
            "total_kpis": 0,
            "complete_kpis": 0,
            "completeness_ratio": 0,
            "missing_fields": []
        }

    # Required fields for "complete" consideration
    required_fields = ['name', 'value', 'unit', 'description']

    complete_count = 0
    missing_by_field = {field: 0 for field in required_fields}

    for idx, row in kpis_df.iterrows():
        is_complete = True

        for field in required_fields:
            if field in kpis_df.columns:
                value = row[field]
                if pd.isna(value) or (isinstance(value, str) and str(value).strip() == ''):
                    missing_by_field[field] += 1
                    is_complete = False
            else:
                missing_by_field[field] += 1
                is_complete = False

        if is_complete:
            complete_count += 1

    total_kpis = len(kpis_df)
    completeness_ratio = (complete_count / total_kpis * 100) if total_kpis > 0 else 0

    return {
        "total_kpis": total_kpis,
        "complete_kpis": complete_count,
        "completeness_ratio": completeness_ratio,
        "missing_fields": {k: v for k, v in missing_by_field.items() if v > 0}
    }

def create_data_health_dashboard():
    """
    Create data health dashboard for all dashboards

    Returns:
        Component with overview of data health
    """
    dashboards = ['executive', 'housing', 'tourism', 'macro', 'affordability', 'forecast']

    health_cards = []

    for dashboard in dashboards:
        quality_score = get_data_quality_score(dashboard)
        completeness = check_data_completeness(dashboard)

        if quality_score >= 80:
            color = "success"
            status = "Healthy"
        elif quality_score >= 60:
            color = "warning"
            status = "Needs Review"
        else:
            color = "danger"
            status = "At Risk"

        health_cards.append(
            dbc.Col(
                dbc.Card([
                    dbc.CardHeader([
                        html.H6(dashboard.title(), className="dashboard-health-title")
                    ]),
                    dbc.CardBody([
                        html.Div([
                            html.Span(f"Quality: {quality_score}/100", className="health-score"),
                            dbc.Badge(status, color=color, className="health-status")
                        ], className="health-header"),

                        html.Div([
                            html.Small(f"KPIs: {completeness['total_kpis']}", className="health-stat"),
                            html.Br(),
                            html.Small(f"Complete: {completeness['complete_kpis']} ({completeness['completeness_ratio']:.0f}%)", className="health-stat"),
                        ], className="health-stats"),

                        html.Div([
                            html.Small("Missing Fields:", className="health-label"),
                            html.Ul([
                                html.Li(f"{field}: {count}")
                                for field, count in completeness['missing_fields'].items()
                            ], className="health-list") if completeness['missing_fields'] else html.Span("All fields present", className="health-ok")
                        ], className="health-details")
                    ])
                ], className="health-card"),
                width=6, lg=4
            )
        )

    return dbc.Container([
        html.H4("Data Health Dashboard", className="health-dashboard-title"),
        html.P("Overview of data quality across all dashboards", className="health-dashboard-subtitle"),
        dbc.Row(health_cards, className="health-cards-row")
    ], className="data-health-dashboard")


def get_data_quality_score_legacy(dashboard_name):
    """Legacy alias for backward compatibility."""
    return get_data_quality_score(dashboard_name)
