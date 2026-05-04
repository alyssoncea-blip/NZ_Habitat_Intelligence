import requests
import json

# Try to find working NZ GeoJSON sources
# Approach: Try multiple known sources systematically

sources = [
    # 1. Stats NZ ArcGIS - try service root
    (
        "Stats NZ ArcGIS root",
        "https://services2.arcgis.com/Iu3D1lHt5NUkVU3S/arcgis/rest/services/Regional_Council_2024/FeatureServer",
        None,
    ),
    # 2. Try different Stats NZ service names
    (
        "Stats NZ RC2024",
        "https://services2.arcgis.com/Iu3D1lHt5NUkVU3S/arcgis/rest/services/Regional_Council_2024/FeatureServer/0",
        None,
    ),
    # 3. Try data.govt.nz API
    (
        "data.govt.nz API",
        "https://data.govt.nz/api/3/action/package_search",
        {"q": "regional council boundaries"},
    ),
    # 4. Try Stats NZ data portal
    (
        "Stats NZ portal",
        "https://www.stats.govt.nz/tools-and-services/datafinder/",
        None,
    ),
    # 5. Try LINZ Data Service
    (
        "LINZ WFS",
        "https://data.linz.govt.nz/services;key=/wfs",
        {
            "service": "WFS",
            "request": "GetCapabilities",
        },
    ),
]

for name, url, params in sources:
    print(f"\n{name}:")
    try:
        if params:
            r = requests.get(
                url, params=params, timeout=15, headers={"User-Agent": "Mozilla/5.0"}
            )
        else:
            r = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})

        print(f"  Status: {r.status_code}")
        print(f"  Content-Type: {r.headers.get('content-type', '?')[:50]}")

        if r.status_code == 200:
            ct = r.headers.get("content-type", "")
            if "json" in ct.lower() or "geojson" in ct.lower():
                try:
                    data = r.json()
                    if "features" in data:
                        n = len(data["features"])
                        print(f"  GeoJSON: {n} features")
                        if n > 0:
                            props = data["features"][0].get("properties", {})
                            print(f"  Keys: {list(props.keys())[:5]}")
                            with open(
                                "app/assets/nz_regions_official.geojson", "w"
                            ) as f:
                                json.dump(data, f)
                            print("  ** SAVED **")
                            break
                    elif "results" in data:
                        print(f"  Search results: {len(data['results'])} items")
                        for item in data["results"][:3]:
                            print(f"    - {item.get('title', '?')}")
                            # Check if it has GeoJSON resources
                            resources = item.get("resources", [])
                            for res in resources:
                                if res.get("format", "").lower() == "geojson":
                                    print(
                                        f"      GeoJSON resource: {res.get('url', '?')}"
                                    )
                                    # Try to download it
                                    r2 = requests.get(
                                        res["url"],
                                        timeout=15,
                                        headers={"User-Agent": "Mozilla/5.0"},
                                    )
                                    if r2.status_code == 200:
                                        try:
                                            geo = r2.json()
                                            n = len(geo.get("features", []))
                                            print(f"      Downloaded: {n} features")
                                            if n > 0:
                                                with open(
                                                    "app/assets/nz_regions_official.geojson",
                                                    "w",
                                                ) as f:
                                                    json.dump(geo, f)
                                                print("      ** SAVED **")
                                                break
                                        except Exception:
                                            print("      Not GeoJSON")
                    else:
                        print(f"  JSON keys: {list(data.keys())[:5]}")
                except Exception as e:
                    print(f"  Parse error: {str(e)[:60]}")
            else:
                print(f"  Preview: {r.text[:100]}")
        else:
            print(f"  Error: {r.text[:100]}")
    except Exception as e:
        print(f"  Exception: {str(e)[:80]}")

print("\nDone")
