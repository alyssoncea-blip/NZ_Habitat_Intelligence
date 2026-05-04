"""Lightweight Data Catalog for NZ Habitat Intelligence.

Provides metadata discovery, lineage tracking, and dataset documentation
across all pipeline layers (Bronze, Silver, Gold).

This is a lightweight alternative to DataHub/Amundsen, suitable for
single-team projects. It catalogs datasets with:
- Schema information
- Data contracts (provenance, confidence)
- Lineage (parent → child relationships)
- Freshness metrics
- Quality scores
"""
import json
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class DatasetEntry:
    """A single dataset entry in the catalog."""
    name: str
    layer: str  # bronze, silver, gold
    path: str
    format: str  # json, parquet
    row_count: int = 0
    column_count: int = 0
    columns: List[str] = field(default_factory=list)
    source: str = ""
    confidence_score: float = 0.0
    created_at: str = ""
    updated_at: str = ""
    parent_datasets: List[str] = field(default_factory=list)
    description: str = ""
    tags: List[str] = field(default_factory=list)
    freshness_days: float = 0.0
    null_percentage: float = 0.0


class DataCatalog:
    """Lightweight data catalog for the NZ Habitat Intelligence pipeline."""

    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.entries: Dict[str, DatasetEntry] = {}

    def scan_layer(self, layer: str, layer_dir: Optional[str] = None) -> List[DatasetEntry]:
        """Scan a pipeline layer and catalog all datasets.

        Args:
            layer: Layer name (bronze, silver, gold).
            layer_dir: Override directory path.

        Returns:
            List of cataloged dataset entries.
        """
        if layer_dir is None:
            layer_dir = str(self.project_root / "data_pipeline" / layer)

        entries = []
        ldir = Path(layer_dir)
        if not ldir.exists():
            logger.warning("Layer directory not found: %s", layer_dir)
            return entries

        # Scan data files
        for ext, fmt in [(".json", "json"), (".parquet", "parquet")]:
            for fp in ldir.glob(f"*{ext}"):
                if ".contract." in fp.name:
                    continue
                entry = self._scan_file(fp, layer, fmt)
                if entry:
                    entries.append(entry)
                    self.entries[entry.name] = entry

        # Load contracts for additional metadata
        for fp in ldir.glob("*.contract.json"):
            try:
                with open(fp, "r", encoding="utf-8") as f:
                    contract = json.load(f)
                artifact_name = contract.get("artifact_name", "")
                if artifact_name in self.entries:
                    self._enrich_from_contract(self.entries[artifact_name], contract)
            except Exception as e:
                logger.warning("Failed to load contract %s: %s", fp.name, e)

        return entries

    def _scan_file(self, fp: Path, layer: str, fmt: str) -> Optional[DatasetEntry]:
        """Scan a single data file and create a catalog entry."""
        try:
            if fmt == "json":
                with open(fp, "r", encoding="utf-8") as f:
                    data = json.load(f)
                records = data.get("data", []) if isinstance(data, dict) else data
                row_count = len(records)
                columns = list(records[0].keys()) if records else []
            elif fmt == "parquet":
                df = pd.read_parquet(fp)
                row_count = len(df)
                columns = list(df.columns)
            else:
                return None

            name = fp.stem
            if fmt == "parquet":
                name = name.replace("_features", "").replace("_complete", "")

            mtime = datetime.fromtimestamp(fp.stat().st_mtime)
            freshness = (datetime.now() - mtime).total_seconds() / 86400

            return DatasetEntry(
                name=name,
                layer=layer,
                path=str(fp.relative_to(self.project_root)),
                format=fmt,
                row_count=row_count,
                column_count=len(columns),
                columns=columns,
                created_at=mtime.isoformat(),
                updated_at=mtime.isoformat(),
                freshness_days=round(freshness, 1),
            )
        except Exception as e:
            logger.warning("Failed to scan %s: %s", fp.name, e)
            return None

    def _enrich_from_contract(self, entry: DatasetEntry, contract: Dict[str, Any]) -> None:
        """Enrich a catalog entry with contract metadata."""
        entry.source = contract.get("source", entry.source)
        entry.confidence_score = contract.get("confidence_score", entry.confidence_score)
        entry.null_percentage = contract.get("null_percentage", entry.null_percentage)
        entry.description = contract.get("notes", entry.description)

        parent_contracts = contract.get("parent_contracts", [])
        if parent_contracts:
            entry.parent_datasets = [
                pc.get("artifact_name", pc) if isinstance(pc, dict) else pc
                for pc in parent_contracts
            ]

    def scan_all(self) -> Dict[str, List[DatasetEntry]]:
        """Scan all pipeline layers."""
        result = {}
        for layer in ["bronze", "silver", "gold"]:
            entries = self.scan_layer(layer)
            result[layer] = entries
        return result

    def get_entry(self, name: str) -> Optional[DatasetEntry]:
        """Get a catalog entry by name."""
        return self.entries.get(name)

    def search(self, query: str, layer: Optional[str] = None) -> List[DatasetEntry]:
        """Search catalog entries by name, description, or tags."""
        query_lower = query.lower()
        results = []
        for entry in self.entries.values():
            if layer and entry.layer != layer:
                continue
            if (query_lower in entry.name.lower() or
                    query_lower in entry.description.lower() or
                    any(query_lower in t.lower() for t in entry.tags)):
                results.append(entry)
        return results

    def get_lineage(self, dataset_name: str) -> Dict[str, Any]:
        """Get lineage information for a dataset.

        Returns:
            Dict with upstream and downstream dependencies.
        """
        entry = self.entries.get(dataset_name)
        if not entry:
            return {"error": f"Dataset not found: {dataset_name}"}

        upstream = []
        for parent_name in entry.parent_datasets:
            parent = self.entries.get(parent_name)
            if parent:
                upstream.append({
                    "name": parent.name,
                    "layer": parent.layer,
                    "confidence": parent.confidence_score,
                })

        downstream = []
        for name, other in self.entries.items():
            if dataset_name in other.parent_datasets:
                downstream.append({
                    "name": other.name,
                    "layer": other.layer,
                    "confidence": other.confidence_score,
                })

        return {
            "dataset": dataset_name,
            "layer": entry.layer,
            "upstream": upstream,
            "downstream": downstream,
        }

    def export(self, output_path: Optional[str] = None) -> str:
        """Export catalog to JSON.

        Args:
            output_path: Path for the output file.

        Returns:
            Path to the exported file.
        """
        if output_path is None:
            output_path = str(self.project_root / "data_pipeline" / "catalog.json")

        data = {
            "generated_at": datetime.now().isoformat(),
            "total_datasets": len(self.entries),
            "datasets": {
                name: {
                    "name": e.name,
                    "layer": e.layer,
                    "path": e.path,
                    "format": e.format,
                    "row_count": e.row_count,
                    "column_count": e.column_count,
                    "columns": e.columns,
                    "source": e.source,
                    "confidence_score": e.confidence_score,
                    "description": e.description,
                    "parent_datasets": e.parent_datasets,
                    "freshness_days": e.freshness_days,
                    "null_percentage": e.null_percentage,
                }
                for name, e in self.entries.items()
            },
        }

        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)

        logger.info("Catalog exported to %s (%d datasets)", output_path, len(self.entries))
        return output_path

    def generate_report(self) -> str:
        """Generate a human-readable catalog report."""
        lines = [
            "=" * 60,
            "NZ HABITAT INTELLIGENCE — DATA CATALOG",
            "=" * 60,
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"Total datasets: {len(self.entries)}",
            "",
        ]

        for layer in ["bronze", "silver", "gold"]:
            layer_entries = [e for e in self.entries.values() if e.layer == layer]
            if not layer_entries:
                continue

            lines.append(f"{'─' * 40}")
            lines.append(f"  {layer.upper()} LAYER ({len(layer_entries)} datasets)")
            lines.append(f"{'─' * 40}")

            for entry in sorted(layer_entries, key=lambda e: e.name):
                status = "TRUSTED" if entry.confidence_score >= 70 else "UNTRUSTED"
                lines.append(f"  [{status}] {entry.name}")
                lines.append(f"    Path: {entry.path}")
                lines.append(f"    Format: {entry.format} | Rows: {entry.row_count:,} | Columns: {entry.column_count}")
                lines.append(f"    Source: {entry.source} | Confidence: {entry.confidence_score:.0f}%")
                lines.append(f"    Freshness: {entry.freshness_days:.1f} days ago")
                if entry.parent_datasets:
                    lines.append(f"    Parents: {', '.join(entry.parent_datasets)}")
                if entry.description:
                    lines.append(f"    Description: {entry.description[:80]}")
                lines.append("")

        return "\n".join(lines)


def build_catalog(project_root: str = ".") -> DataCatalog:
    """Build a complete data catalog for the project.

    Args:
        project_root: Path to the project root directory.

    Returns:
        Populated DataCatalog instance.
    """
    catalog = DataCatalog(project_root)
    catalog.scan_all()
    return catalog


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    catalog = build_catalog()
    print(catalog.generate_report())
    catalog.export()
