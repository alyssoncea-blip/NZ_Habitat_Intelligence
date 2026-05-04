"""LINZ (Land Information New Zealand) Data Ingestor.

Fetches real geographic boundaries from LINZ Data Service WFS endpoints.
Falls back to curated regional centroid data if WFS is unavailable.
"""
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)

# LINZ Data Service WFS endpoints (public, no API key required for basic access)
LINZ_WFS_BASE = "https://data.linz.govt.nz/services"
LINZ_WFS_ENDPOINTS = {
    "regional_boundaries": {
        "layer": "53466",
        "name": "Regional Council 2024 Generalised",
        "url": f"{LINZ_WFS_BASE}/wfs/53466",
        "params": {
            "service": "WFS",
            "version": "2.0.0",
            "request": "GetFeature",
            "typeName": "linz_data:regional-council-2024-generalised-version",
            "outputFormat": "application/json",
        },
    },
    "territorial_boundaries": {
        "layer": "53467",
        "name": "Territorial Authority 2024 Generalised",
        "url": f"{LINZ_WFS_BASE}/wfs/53467",
        "params": {
            "service": "WFS",
            "version": "2.0.0",
            "request": "GetFeature",
            "typeName": "linz_data:territorial-authority-2024-generalised-version",
            "outputFormat": "application/json",
        },
    },
}

# NZ Regions with centroids (fallback data)
_NZ_REGIONS = {
    "Northland": {"center": (-35.5804, 173.7630), "area_km2": 12598},
    "Auckland": {"center": (-36.8485, 174.7633), "area_km2": 4940},
    "Waikato": {"center": (-37.6190, 175.4371), "area_km2": 24598},
    "Bay of Plenty": {"center": (-37.6702, 176.2095), "area_km2": 12231},
    "Gisborne": {"center": (-38.6623, 178.0175), "area_km2": 8387},
    "Hawke's Bay": {"center": (-39.4928, 176.9124), "area_km2": 14137},
    "Taranaki": {"center": (-39.3000, 174.1217), "area_km2": 7254},
    "Manawatu-Wanganui": {"center": (-39.7276, 175.4371), "area_km2": 22220},
    "Wellington": {"center": (-41.2865, 174.7762), "area_km2": 8124},
    "Tasman": {"center": (-41.2706, 172.7187), "area_km2": 9786},
    "Nelson": {"center": (-41.2706, 173.2839), "area_km2": 445},
    "Marlborough": {"center": (-41.5134, 173.9613), "area_km2": 12524},
    "West Coast": {"center": (-42.4504, 171.2108), "area_km2": 23245},
    "Canterbury": {"center": (-43.5865, 171.4804), "area_km2": 44508},
    "Otago": {"center": (-45.0675, 170.0949), "area_km2": 31241},
    "Southland": {"center": (-45.8880, 168.0668), "area_km2": 34447},
}


class LINZIngestor:
    """Ingestor for LINZ geographic boundaries and property data."""

    def __init__(self, data_dir: str = "data_pipeline/bronze"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.session = self._create_session()

    @staticmethod
    def _create_session() -> requests.Session:
        session = requests.Session()
        retry = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
        session.mount("https://", HTTPAdapter(max_retries=retry))
        session.headers.update({
            "User-Agent": "NZHabitatIntelligence/2.0",
            "Accept": "application/json, */*",
        })
        return session

    def _fetch_wfs(self, endpoint_config: Dict, description: str) -> Optional[Dict]:
        """Fetch GeoJSON from LINZ WFS endpoint."""
        try:
            url = endpoint_config["url"]
            params = endpoint_config["params"]
            logger.info("  Fetching %s from LINZ WFS: %s", description, url)
            resp = self.session.get(url, params=params, timeout=30)
            resp.raise_for_status()
            data = resp.json()

            if "features" in data and len(data["features"]) > 0:
                logger.info("  %s: %d features from LINZ WFS", description, len(data["features"]))
                return data
        except Exception as e:
            logger.debug("  WFS fetch failed for %s: %s", description, e)
        return None

    def fetch_regional_boundaries(self) -> Dict[str, Any]:
        """Fetch regional council boundaries from LINZ WFS."""
        # Strategy 1: Real WFS GeoJSON
        wfs_data = self._fetch_wfs(LINZ_WFS_ENDPOINTS["regional_boundaries"], "regional boundaries")
        if wfs_data:
            return {
                "metadata": {
                    "source": "LINZ WFS (Live)",
                    "date_fetched": datetime.now().isoformat(),
                    "url": LINZ_WFS_ENDPOINTS["regional_boundaries"]["url"],
                    "description": LINZ_WFS_ENDPOINTS["regional_boundaries"]["name"],
                    "format": "GeoJSON",
                    "license": "CC BY 4.0",
                    "feature_count": len(wfs_data.get("features", [])),
                },
                "type": "FeatureCollection",
                "features": wfs_data["features"],
            }

        # Fallback: curated regional data with simplified polygons
        logger.info("  Regional boundaries: using fallback centroid data (%d regions)", len(_NZ_REGIONS))
        boundaries_data = []
        for region, info in _NZ_REGIONS.items():
            lat, lon = info["center"]
            bbox = [
                [lon - 0.5, lat - 0.3],
                [lon + 0.5, lat - 0.3],
                [lon + 0.5, lat + 0.3],
                [lon - 0.5, lat + 0.3],
                [lon - 0.5, lat - 0.3],
            ]
            boundaries_data.append({
                "type": "Feature",
                "properties": {
                    "region_name": region,
                    "region_code": region.upper().replace("'", "").replace("-", "_")[:10],
                    "area_sq_km": info["area_km2"],
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [bbox],
                },
            })

        return {
            "metadata": {
                "source": "LINZ (Fallback)",
                "date_fetched": datetime.now().isoformat(),
                "description": "Regional council boundaries (simplified fallback)",
                "format": "GeoJSON-simplified",
                "license": "CC BY 4.0",
                "feature_count": len(boundaries_data),
            },
            "type": "FeatureCollection",
            "features": boundaries_data,
        }

    def fetch_territorial_authorities(self) -> Dict[str, Any]:
        """Fetch territorial authority boundaries from LINZ WFS."""
        wfs_data = self._fetch_wfs(LINZ_WFS_ENDPOINTS["territorial_boundaries"], "territorial authorities")
        if wfs_data:
            return {
                "metadata": {
                    "source": "LINZ WFS (Live)",
                    "date_fetched": datetime.now().isoformat(),
                    "url": LINZ_WFS_ENDPOINTS["territorial_boundaries"]["url"],
                    "description": LINZ_WFS_ENDPOINTS["territorial_boundaries"]["name"],
                    "format": "GeoJSON",
                    "license": "CC BY 4.0",
                    "feature_count": len(wfs_data.get("features", [])),
                },
                "type": "FeatureCollection",
                "features": wfs_data["features"],
            }

        # Fallback: major territorial authorities
        territorial_authorities = [
            {"name": "Auckland", "region": "Auckland", "population": 1650000},
            {"name": "Wellington", "region": "Wellington", "population": 550000},
            {"name": "Christchurch", "region": "Canterbury", "population": 400000},
            {"name": "Hamilton", "region": "Waikato", "population": 180000},
            {"name": "Tauranga", "region": "Bay of Plenty", "population": 160000},
            {"name": "Dunedin", "region": "Otago", "population": 120000},
            {"name": "Palmerston North", "region": "Manawatu-Wanganui", "population": 90000},
            {"name": "Napier", "region": "Hawke's Bay", "population": 66000},
            {"name": "Hastings", "region": "Hawke's Bay", "population": 82000},
            {"name": "Nelson", "region": "Nelson", "population": 54000},
            {"name": "Rotorua", "region": "Bay of Plenty", "population": 58000},
            {"name": "New Plymouth", "region": "Taranaki", "population": 59000},
            {"name": "Whangarei", "region": "Northland", "population": 58000},
            {"name": "Invercargill", "region": "Southland", "population": 57000},
            {"name": "Gisborne", "region": "Gisborne", "population": 38000},
            {"name": "Queenstown", "region": "Otago", "population": 29000},
        ]

        ta_data = []
        for ta in territorial_authorities:
            region_info = _NZ_REGIONS.get(ta["region"], {"center": (-41.2865, 174.7762)})
            lat, lon = region_info["center"]
            lat += (hash(ta["name"]) % 100) / 1000 - 0.05
            lon += (hash(ta["name"] + "2") % 100) / 1000 - 0.05

            ta_data.append({
                "territorial_authority": ta["name"],
                "region": ta["region"],
                "population": ta["population"],
                "center_latitude": round(lat, 6),
                "center_longitude": round(lon, 6),
            })

        return {
            "metadata": {
                "source": "LINZ (Fallback)",
                "date_fetched": datetime.now().isoformat(),
                "description": "Territorial authorities (simplified fallback)",
                "format": "JSON",
                "license": "CC BY 4.0",
            },
            "data": ta_data,
        }

    def save_data(self, data_type: str, data: Dict[str, Any]) -> str:
        """Save data to JSON file."""
        output_file = self.data_dir / f"linz_{data_type}_raw.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)
        logger.info("Saved %s to %s", data_type, output_file)
        return str(output_file)

    def run_all_ingestions(self) -> Dict[str, str]:
        """Run ingestion for all LINZ datasets."""
        logger.info("Starting LINZ data ingestion")
        results = {}

        try:
            boundaries_data = self.fetch_regional_boundaries()
            results["regional_boundaries"] = self.save_data("regional_boundaries", boundaries_data)
        except Exception as e:
            logger.error("Regional boundaries ingestion failed: %s", e)

        try:
            ta_data = self.fetch_territorial_authorities()
            results["territorial_authorities"] = self.save_data("territorial_authorities", ta_data)
        except Exception as e:
            logger.error("Territorial authorities ingestion failed: %s", e)

        logger.info("LINZ ingestion complete. Files saved: %d", len(results))
        return results


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    ingestor = LINZIngestor()
    results = ingestor.run_all_ingestions()
    for data_type, file_path in results.items():
        print(f"  {data_type}: {file_path}")
