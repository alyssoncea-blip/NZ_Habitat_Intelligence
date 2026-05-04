"""Validate NZ regions GeoJSON against dataset regions.

This script loads the NZ regions GeoJSON file, normalizes region names,
validates against the expected dataset regions, and optionally displays
a test choropleth map.

Usage:
    python scripts/validate_geojson.py [--show-map]
"""
import json
import os
import argparse

import plotly.express as px
import pandas as pd

NZ_REGIONS = [
    "Northland", "Auckland", "Waikato", "Bay of Plenty", "Gisborne",
    "Hawke's Bay", "Taranaki", "Manawatū-Whanganui", "Wellington",
    "Tasman", "Nelson", "Marlborough", "West Coast", "Canterbury",
    "Otago", "Southland"
]

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
    "Manawatu-Wanganui": "Manawatū-Whanganui",
    "Taranaki": "Taranaki",
    "Northland": "Northland",
    "Bay of Plenty": "Bay of Plenty",
    "Gisborne District": "Gisborne",
    "Hawke's Bay": "Hawke's Bay",
}


def load_geojson(geojson_path: str) -> dict:
    """Load and parse the GeoJSON file."""
    with open(geojson_path, encoding="utf-8") as f:
        return json.load(f)


def normalize_geojson(geojson: dict) -> dict:
    """Normalize region names in GeoJSON features."""
    normalized = {"type": "FeatureCollection", "features": []}

    for feat in geojson["features"]:
        original_name = feat["properties"]["name"]
        if original_name in NAME_MAPPING:
            normalized_name = NAME_MAPPING[original_name]
            feat["properties"]["region"] = normalized_name
            feat["properties"]["original_name"] = original_name
            normalized["features"].append(feat)
        else:
            print(f"WARNING: Unknown region: {original_name}")

    return normalized


def validate_regions(geojson_norm: dict) -> bool:
    """Validate GeoJSON regions against expected dataset regions."""
    geojson_regions = {feat["properties"]["region"] for feat in geojson_norm["features"]}
    dataset_regions = set(NZ_REGIONS)

    missing_in_geojson = dataset_regions - geojson_regions
    missing_in_dataset = geojson_regions - dataset_regions

    print("\n=== VALIDATION ===")
    all_ok = True

    if missing_in_geojson:
        print(f"ERROR: Regions in dataset but NOT in GeoJSON: {missing_in_geojson}")
        all_ok = False
    else:
        print("OK: All dataset regions found in GeoJSON")

    if missing_in_dataset:
        print(f"WARNING: Regions in GeoJSON but NOT in dataset: {missing_in_dataset}")

    duplicates = [r for r in geojson_regions if NZ_REGIONS.count(r) > 1]
    if duplicates:
        print(f"ERROR: Duplicate regions: {duplicates}")
        all_ok = False
    else:
        print("OK: No duplicate regions")

    print(f"\nTotal features: {len(geojson_norm['features'])}")
    print(f"Dataset regions: {len(dataset_regions)}")
    print(f"GeoJSON regions: {len(geojson_regions)}")

    return all_ok


def show_test_map(geojson_norm: dict) -> None:
    """Display a test choropleth map with sample data."""
    df = pd.DataFrame({
        "region": NZ_REGIONS,
        "value": range(16)
    })

    fig = px.choropleth_map(
        df,
        geojson=geojson_norm,
        locations="region",
        featureidkey="properties.region",
        color="value",
        map_style="carto-positron",
        center={"lat": -41.5, "lon": 173.5},
        zoom=4.2
    )

    fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
    fig.show()


def main() -> None:
    """Run GeoJSON validation."""
    parser = argparse.ArgumentParser(description="Validate NZ regions GeoJSON")
    parser.add_argument("--show-map", action="store_true", help="Display test choropleth map")
    parser.add_argument("--output", type=str, help="Output path for normalized GeoJSON")
    args = parser.parse_args()

    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    geojson_path = os.path.join(project_root, "app", "assets", "nz.json")

    print(f"Loading GeoJSON from: {geojson_path}")
    geojson = load_geojson(geojson_path)

    print("Normalizing region names...")
    geojson_norm = normalize_geojson(geojson)
    print(f"Normalized {len(geojson_norm['features'])} features")

    # Save normalized GeoJSON
    output_path = args.output or os.path.join(project_root, "app", "assets", "nz_regions_clean.geojson")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(geojson_norm, f, ensure_ascii=False, indent=2)
    print(f"Saved normalized GeoJSON to: {output_path}")

    is_valid = validate_regions(geojson_norm)

    if args.show_map:
        print("\nDisplaying test map...")
        show_test_map(geojson_norm)

    if not is_valid:
        print("\nValidation FAILED — check errors above")
        exit(1)
    else:
        print("\nValidation PASSED")


if __name__ == "__main__":
    main()
