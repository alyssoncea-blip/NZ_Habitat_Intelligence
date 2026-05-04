
"""Choropleth map component for NZ regions using Plotly."""

import json
import os
from typing import Any, Dict, List

import plotly.graph_objects as go
from dash import dcc, html


NAME_MAPPING = {
    "Southland": "Southland",
    "Marlborough District": "Marlborough",
    "Nelson City": "Nelson",
    "Tasman District": "Tasman",
    "West Coast": "West Coast",
    "Otago": "Otago",
    "Canterbury": "Canterbury",
    "Auckland": "Auckland",
    "Waikato": "Waikato",
    "Wellington": "Wellington",
    "Manawatu-Wanganui": "Manawatu-Wanganui",
    "Taranaki": "Taranaki",
    "Northland": "Northland",
    "Bay of Plenty": "Bay of Plenty",
    "Gisborne District": "Gisborne",
    "Hawke's Bay": "Hawke's Bay",
}


def _load_nz_geojson() -> Dict[str, Any]:
    """Load and normalize NZ regions GeoJSON from app/assets/nz.json."""
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    geojson_path = os.path.join(base_dir, "app", "assets", "nz.json")

    with open(geojson_path, encoding="utf-8") as f:
        geojson = json.load(f)

    normalized = {
        "type": "FeatureCollection",
        "features": []
    }

    for feat in geojson["features"]:
        original_name = feat["properties"]["name"]
        if original_name in NAME_MAPPING:
            normalized_name = NAME_MAPPING[original_name]
            feat["properties"]["region"] = normalized_name
            normalized["features"].append(feat)

    return normalized


NZ_REGIONS_GEOJSON = _load_nz_geojson()


def create_choropleth_map(
    regions_data: List[Dict[str, Any]],
    color_column: str = "pressure",
    title: str = "Regional Housing Pressure Index",
    height: int = 400,
    colorscale: str = "RdYlGn_r",
) -> go.Figure:
    """Create a choropleth map of NZ regions.

    Args:
        regions_data: List of dicts with region, pressure, affordability,
                      price_mom, lat, lon
        color_column: Data field to use for coloring ('pressure' by default)
        title: Map title
        height: Map height in pixels
        colorscale: Plotly colorscale name

    Returns:
        Plotly figure
    """
    if not regions_data:
        return go.Figure()

    region_lookup = {r["region"]: r for r in regions_data}

    values = []
    hover_texts = []
    feature_names = []

    for feature in NZ_REGIONS_GEOJSON["features"]:
        name = feature["properties"]["region"]
        feature_names.append(name)
        rdata = region_lookup.get(name, {})
        if color_column == "pressure":
            val = rdata.get("pressure", 50)
        elif color_column == "affordability":
            val = rdata.get("affordability", 8)
        elif color_column == "price_mom":
            val = rdata.get("price_mom", 0)
        else:
            val = rdata.get(color_column, 50)
        values.append(val)

        aff = rdata.get("affordability", "N/A")
        mom = rdata.get("price_mom", "N/A")
        hover_texts.append(
            f"<b>{name}</b><br>"
            f"Pressure Index: {val}<br>"
            f"Affordability: {aff}x<br>"
            f"Price MoM: {mom}%"
        )

    fig = go.Figure(
        go.Choroplethmapbox(
            geojson=NZ_REGIONS_GEOJSON,
            locations=feature_names,
            z=values,
            featureidkey="properties.region",
            colorscale=colorscale,
            marker={"line": {"width": 1, "color": "#ffffff"}},
            colorbar={
                "title": {"text": "Index (0-100)", "side": "right"},
                "thickness": 12,
                "len": 0.6,
                "x": 0.95,
                "xpad": 0,
            },
            hovertext=hover_texts,
            hoverinfo="text",
            hovertemplate="%{hovertext}<extra></extra>",
        )
    )

    fig.update_layout(
        mapbox={
            "style": "carto-positron",
            "center": {"lat": -41.5, "lon": 173.5},
            "zoom": 4.2,
        },
        margin={"r": 0, "t": 30, "l": 0, "b": 0},
        height=height,
        title={
            "text": title,
            "x": 0.5,
            "xanchor": "center",
            "font": {"size": 14, "weight": 600},
        },
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )

    return fig


def create_mini_map_preview(
    regions_data: List[Dict[str, Any]],
    height: int = 180,
) -> go.Figure:
    """Create a small preview map for the KPI card.

    Args:
        regions_data: List of region dicts
        height: Card height

    Returns:
        Plotly figure (compact)
    """
    fig = create_choropleth_map(
        regions_data,
        height=height,
        title="",
    )
    fig.update_layout(
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        mapbox={"zoom": 4.0},
        paper_bgcolor="rgba(0,0,0,0)",
    )
    fig.update_traces(
        colorbar=None,
        marker={"line": {"width": 0.5, "color": "#cccccc"}},
    )
    return fig


def create_map_component(
    regions_data: List[Dict[str, Any]],
    map_id: str = "executive-choropleth",
    height: int = 400,
) -> html.Div:
    """Create a complete Dash map component with wrapper.

    Args:
        regions_data: List of region dicts
        map_id: HTML id for the graph
        height: Map height

    Returns:
        Div wrapping the Plotly graph
    """
    fig = create_choropleth_map(regions_data, height=height)

    return html.Div(
        dcc.Graph(
            id=map_id,
            figure=fig,
            config={"displayModeBar": False, "scrollZoom": True},
            style={"height": f"{height}px"},
        ),
        className="map-container",
    )
