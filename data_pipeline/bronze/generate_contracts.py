"""Generate data contracts for all Bronze layer raw JSON files.

Scans the bronze directory for *_raw.json files, analyzes their content,
and produces corresponding .contract.json files with provenance metadata.
"""
import json
import logging
from pathlib import Path
from typing import Dict, Any

from data_pipeline.utils.data_contract import (
    DataSource, DataContract, ColumnContract,
    get_data_quality,
)

logger = logging.getLogger(__name__)

_SOURCE_KEYWORDS = {
    "world_bank": ("world_bank_api", DataSource.REAL),
    "rbnz": ("rbnz_csv", DataSource.REAL),
    "stats_nz": ("stats_nz_csv", DataSource.REAL),
    "mbie": ("mbie_tourism_api", DataSource.REAL),
    "linz": ("linz_data_service", DataSource.REAL),
    "trade_me": ("trademe_scraper", DataSource.REAL),
}


def _detect_source(filename: str, metadata: Dict[str, Any]) -> tuple:
    """Detect data source from filename and metadata."""
    fname_lower = filename.lower()
    for keyword, (name, source) in _SOURCE_KEYWORDS.items():
        if keyword in fname_lower:
            # Check if metadata indicates fallback
            if metadata.get("status") in ("fallback", "error"):
                return (name, DataSource.FALLBACK)
            if "World Bank (Fallback)" in metadata.get("source", ""):
                return ("world_bank_fallback", DataSource.FALLBACK)
            return (name, source)
    return ("unknown", DataSource.UNKNOWN)


def _analyze_json_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze JSON data structure for contract metadata."""
    records = data.get("data", [])
    record_count = len(records)

    # Analyze fields from first few records
    fields = {}
    if records and isinstance(records[0], dict):
        sample = records[:min(10, len(records))]
        all_keys = set()
        for r in sample:
            all_keys.update(r.keys())

        for key in all_keys:
            values = [r.get(key) for r in sample if key in r]
            non_null = [v for v in values if v is not None]
            fields[key] = {
                "null_count": len(values) - len(non_null),
                "null_pct": round((len(values) - len(non_null)) / max(1, len(values)) * 100, 1),
                "unique_count": len(set(str(v) for v in non_null)),
                "sample": non_null[:3],
            }

    return {
        "record_count": record_count,
        "field_count": len(fields),
        "fields": fields,
    }


def generate_contracts(bronze_dir: str = "data_pipeline/bronze") -> Dict[str, str]:
    """Generate contracts for all Bronze layer raw JSON files."""
    bronze_path = Path(bronze_dir)
    contracts = {}

    for json_file in sorted(bronze_path.glob("*_raw.json")):
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            metadata = data.get("metadata", {})
            source_name, source = _detect_source(json_file.name, metadata)
            analysis = _analyze_json_data(data)

            # Build column contracts
            columns = []
            for field_name, field_info in analysis.get("fields", {}).items():
                columns.append(ColumnContract(
                    name=field_name,
                    dtype="string",
                    null_count=field_info["null_count"],
                    null_percentage=field_info["null_pct"],
                    unique_count=field_info["unique_count"],
                    sample_values=field_info["sample"],
                ))

            # Calculate quality metrics
            total_fields = max(1, analysis["field_count"])
            avg_null_pct = sum(f["null_pct"] for f in analysis.get("fields", {}).values()) / total_fields

            # Manual confidence calculation for JSON (no DataFrame)
            confidence = 0.0
            if source == DataSource.REAL:
                confidence += 50
            elif source == DataSource.FALLBACK:
                confidence += 10
            else:
                confidence += 15

            if avg_null_pct < 5:
                confidence += 30
            elif avg_null_pct < 15:
                confidence += 20
            elif avg_null_pct < 30:
                confidence += 10

            record_count = analysis["record_count"]
            if record_count >= 100:
                confidence += 5
            elif record_count >= 50:
                confidence += 3
            elif record_count >= 20:
                confidence += 1

            confidence = min(100.0, max(0.0, confidence))
            if source == DataSource.REAL:
                confidence = min(100, confidence + 20)
            elif source == DataSource.FALLBACK:
                confidence = max(10, confidence - 30)

            quality = get_data_quality(avg_null_pct, confidence, source)

            contract = DataContract(
                artifact_name=json_file.stem,
                artifact_path=str(json_file),
                layer="bronze",
                source=source,
                source_name=source_name,
                source_url=metadata.get("url"),
                quality=quality,
                confidence_score=confidence,
                record_count=analysis["record_count"],
                column_count=analysis["field_count"],
                null_percentage=avg_null_pct,
                columns=columns,
                data_from_date=metadata.get("date_from"),
                data_to_date=metadata.get("date_to"),
                notes=metadata.get("notes", ""),
            )

            contract_path = str(json_file).replace(".json", ".contract.json")
            contract.save(Path(contract_path))
            contracts[str(json_file)] = contract_path
            logger.info("  [%s] %s: %d records, confidence=%.0f",
                        source.value, json_file.name, analysis["record_count"], confidence)

        except Exception as e:
            logger.warning("  Failed to generate contract for %s: %s", json_file.name, e)

    return contracts


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    logger.info("Generating Bronze layer data contracts...")
    contracts = generate_contracts()
    print(f"\nGenerated {len(contracts)} contracts:")
    for src, dst in contracts.items():
        print(f"  {src} -> {dst}")
