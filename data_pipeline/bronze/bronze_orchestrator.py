"""Bronze Layer Orchestrator - Coordinates all data ingestion."""

import hashlib
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

# Import individual ingestors
try:
    from data_pipeline.bronze.ingestors.rbnz_ingestor import RBNZIngestor
    from data_pipeline.bronze.ingestors.stats_nz_ingestor import StatsNZIngestor
    from data_pipeline.bronze.ingestors.linz_ingestor import LINZIngestor
    from data_pipeline.bronze.ingestors.mbie_tourism_ingestor import MBIEIngestor
    from data_pipeline.bronze.ingestors.world_bank_ingestor import WorldBankIngestor
    from data_pipeline.bronze.ingestors.reinz_ingestor import REINZIngestor

    HAS_INGESTORS = True
except ImportError as e:
    HAS_INGESTORS = False
    print(
        f"Warning: Some ingestors not available. Running in simulation mode. Error: {e}"
    )


class BronzeOrchestrator:
    """Orchestrates all bronze layer data ingestion."""

    def __init__(
        self, data_dir: str = "data_pipeline/bronze", cache_ttl_seconds: int = 86400
    ):
        """Initialize orchestrator.

        Args:
            data_dir: Directory for bronze layer data.
            cache_ttl_seconds: Cache time-to-live in seconds (default 24h).
        """
        self.logger = logging.getLogger(__name__)
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.cache_ttl_seconds = cache_ttl_seconds
        self.cache_file = self.data_dir / "ingestion_cache.json"

        # Initialize ingestors - ALL sources active
        self.ingestors = {}
        if HAS_INGESTORS:
            self.ingestors = {
                "world_bank": WorldBankIngestor(data_dir),
                "rbnz": RBNZIngestor(data_dir),
                "stats_nz": StatsNZIngestor(data_dir),
                "mbie_tourism": MBIEIngestor(data_dir),
                "linz": LINZIngestor(data_dir),
                "reinz": REINZIngestor(data_dir),
                # Trade Me requires Playwright; activate separately
                # "trade_me": TradeMeScraper(data_dir),
            }
        else:
            self.logger.warning(
                "Running in simulation mode - no real ingestors available"
            )

        # Ingestion schedule
        self.schedule = {
            "daily": ["world_bank", "reinz"],
            "weekly": ["rbnz", "stats_nz", "mbie_tourism"],
            "monthly": ["linz"],
        }

        # Status tracking
        self.ingestion_status = {}
        self._load_cache()

    def _load_cache(self):
        """Load ingestion cache from disk."""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, "r") as f:
                    self._cache = json.load(f)
            except (json.JSONDecodeError, IOError):
                self._cache = {}
        else:
            self._cache = {}

    def _save_cache(self):
        """Save ingestion cache to disk."""
        with open(self.cache_file, "w") as f:
            json.dump(self._cache, f, indent=2, default=str)

    @staticmethod
    def _compute_record_hash(record: Dict[str, Any]) -> str:
        """Compute a hash for a single record for deduplication."""
        # Sort keys for consistent hashing
        serialized = json.dumps(record, sort_keys=True, default=str)
        return hashlib.sha256(serialized.encode()).hexdigest()[:16]

    def deduplicate_records(
        self, records: List[Dict[str, Any]], source: str
    ) -> List[Dict[str, Any]]:
        """Remove duplicate records based on content hash.

        Args:
            records: List of data records to deduplicate.
            source: Source name for logging.

        Returns:
            Deduplicated list of records.
        """
        if not records:
            return records

        seen_hashes = set()
        unique_records = []
        duplicates = 0

        for record in records:
            record_hash = self._compute_record_hash(record)
            if record_hash not in seen_hashes:
                seen_hashes.add(record_hash)
                unique_records.append(record)
            else:
                duplicates += 1

        if duplicates > 0:
            self.logger.info(
                "  %s: removed %d duplicate records (%d → %d)",
                source,
                duplicates,
                len(records),
                len(unique_records),
            )

        return unique_records

    def _is_cache_valid(self, source: str) -> bool:
        """Check if cached data for source is still valid."""
        if source not in self._cache:
            return False
        cached_time = datetime.fromisoformat(self._cache[source]["cached_at"])
        age = (datetime.now() - cached_time).total_seconds()
        return age < self.cache_ttl_seconds

    def _get_cached_data(self, source: str) -> Optional[Dict]:
        """Get cached data if valid."""
        if self._is_cache_valid(source):
            self.logger.info(
                "  %s: using cached data (age: %dh)",
                source,
                (
                    datetime.now()
                    - datetime.fromisoformat(self._cache[source]["cached_at"])
                ).total_seconds()
                / 3600,
            )
            return self._cache[source].get("data")
        return None

    def _cache_data(self, source: str, data: Dict):
        """Cache ingestion results."""
        self._cache[source] = {
            "cached_at": datetime.now().isoformat(),
            "data": data,
            "record_count": data.get("metadata", {}).get("record_count", 0),
            "source_label": data.get("metadata", {}).get("source", "unknown"),
        }
        self._save_cache()

    def run_ingestor(
        self, ingestor_name: str, force_refresh: bool = False
    ) -> Dict[str, Any]:
        """Run a specific ingestor.

        Args:
            ingestor_name: Name of ingestor to run
            force_refresh: Skip cache and fetch fresh data

        Returns:
            Ingestion results
        """
        self.logger.info("Running ingestor: %s", ingestor_name)

        if ingestor_name not in self.ingestors and ingestor_name != "all":
            return {
                "success": False,
                "error": f"Ingestor '{ingestor_name}' not found",
                "timestamp": datetime.now().isoformat(),
            }

        try:
            start_time = datetime.now()

            if ingestor_name == "all":
                results = {}
                for name in self.ingestors:
                    result = self.run_ingestor(name, force_refresh=force_refresh)
                    results[name] = result

                run_time = (datetime.now() - start_time).total_seconds()
                total_success = sum(
                    1 for r in results.values() if r.get("success", False)
                )

                result = {
                    "success": total_success == len(self.ingestors),
                    "run_time_seconds": run_time,
                    "ingestors_run": len(self.ingestors),
                    "ingestors_successful": total_success,
                    "results": results,
                    "timestamp": datetime.now().isoformat(),
                }

            else:
                ingestor = self.ingestors[ingestor_name]

                # Check cache unless force refresh
                if not force_refresh and self._is_cache_valid(ingestor_name):
                    cached = self._get_cached_data(ingestor_name)
                    if cached:
                        return {
                            "success": True,
                            "cached": True,
                            "files_created": 0,
                            "run_time_seconds": 0,
                            "timestamp": datetime.now().isoformat(),
                        }

                result = self._run_single_ingestor(ingestor_name, ingestor)

                # Cache successful results
                if result.get("success"):
                    self._cache_ingestor_results(ingestor_name, result)

            # Update status
            self.ingestion_status[ingestor_name] = {
                "last_run": datetime.now().isoformat(),
                "success": result.get("success", False),
                "run_time": result.get("run_time_seconds", 0),
                "cached": result.get("cached", False),
            }

            return result

        except Exception as e:
            self.logger.error("Error running ingestor %s: %s", ingestor_name, e)
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    def _cache_ingestor_results(self, ingestor_name: str, result: Dict):
        """Cache metadata from ingestor results with deduplication."""
        for file_path in result.get("file_paths", []):
            try:
                with open(file_path, "r") as f:
                    data = json.load(f)

                # Deduplicate records if data has a 'data' key with a list
                if (
                    isinstance(data, dict)
                    and "data" in data
                    and isinstance(data["data"], list)
                ):
                    original_count = len(data["data"])
                    data["data"] = self.deduplicate_records(data["data"], ingestor_name)
                    if len(data["data"]) < original_count:
                        # Save deduplicated data back
                        with open(file_path, "w") as f:
                            json.dump(data, f, indent=2, default=str)

                source_key = Path(file_path).stem
                self._cache_data(source_key, data)
            except (IOError, json.JSONDecodeError):
                pass

    def _run_single_ingestor(self, ingestor_name: str, ingestor) -> Dict[str, Any]:
        """Run a single ingestor instance."""
        start_time = datetime.now()

        try:
            if ingestor_name == "trade_me":
                result = ingestor.run_scraping()
                if isinstance(result, dict):
                    return {
                        "success": result.get("success", False),
                        "listings_count": result.get("listings_count", 0),
                        "file_path": result.get("file_path"),
                        "run_time_seconds": (
                            datetime.now() - start_time
                        ).total_seconds(),
                        "timestamp": datetime.now().isoformat(),
                    }
                return {"success": False, "error": "Unexpected result format"}

            elif ingestor_name in ["rbnz", "world_bank", "reinz"]:
                results = ingestor.run_ingestion()
                return {
                    "success": bool(results),
                    "files_created": len(results),
                    "file_paths": list(results.values()),
                    "run_time_seconds": (datetime.now() - start_time).total_seconds(),
                    "timestamp": datetime.now().isoformat(),
                }

            elif ingestor_name in ["stats_nz", "linz", "mbie_tourism"]:
                results = (
                    ingestor.run_all_ingestions()
                    if hasattr(ingestor, "run_all_ingestions")
                    else ingestor.run_ingestion()
                )
                return {
                    "success": bool(results),
                    "files_created": len(results),
                    "file_paths": list(results.values()),
                    "run_time_seconds": (datetime.now() - start_time).total_seconds(),
                    "timestamp": datetime.now().isoformat(),
                }

            else:
                return {
                    "success": False,
                    "error": f"Unknown ingestor type: {ingestor_name}",
                }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "run_time_seconds": (datetime.now() - start_time).total_seconds(),
                "timestamp": datetime.now().isoformat(),
            }

    def run_scheduled_ingestion(
        self, schedule_type: str = "daily", force_refresh: bool = False
    ) -> Dict[str, Any]:
        """Run ingestion based on schedule."""
        if schedule_type not in self.schedule:
            return {
                "success": False,
                "error": f"Invalid schedule type: {schedule_type}",
                "timestamp": datetime.now().isoformat(),
            }

        ingestor_names = self.schedule[schedule_type]
        self.logger.info(
            "Running %s scheduled ingestion for: %s", schedule_type, ingestor_names
        )

        results = {}
        for ingestor_name in ingestor_names:
            result = self.run_ingestor(ingestor_name, force_refresh=force_refresh)
            results[ingestor_name] = result

        all_success = all(r.get("success", False) for r in results.values())

        return {
            "success": all_success,
            "schedule_type": schedule_type,
            "results": results,
            "timestamp": datetime.now().isoformat(),
        }

    def check_data_freshness(self) -> Dict[str, Any]:
        """Check freshness of all ingested data sources."""
        freshness_report = {
            "check_time": datetime.now().isoformat(),
            "sources": {},
            "overall_freshness_score": 0,
            "stale_sources": [],
            "warnings": [],
        }

        total_score = 0
        source_count = 0

        for source_name in self.ingestors:
            source_files = list(
                self.data_dir.glob(f"{source_name.replace('_tourism', '')}_*.json")
            )
            # Also check mbie_ files for mbie_tourism
            if source_name == "mbie_tourism":
                source_files = list(self.data_dir.glob("mbie_*.json"))

            if not source_files:
                freshness_report["sources"][source_name] = {
                    "status": "missing",
                    "file_count": 0,
                    "freshness_score": 0,
                    "age_days": None,
                    "issues": ["No data files found"],
                }
                freshness_report["stale_sources"].append(source_name)
                continue

            # Find most recent file
            latest_file = max(source_files, key=lambda f: f.stat().st_mtime)
            file_age_seconds = (
                datetime.now() - datetime.fromtimestamp(latest_file.stat().st_mtime)
            ).total_seconds()
            file_age_days = file_age_seconds / 86400

            # Determine expected freshness by source
            expected_freshness = {
                "world_bank": 7,  # Weekly updates
                "rbnz": 7,  # Weekly updates
                "stats_nz": 14,  # Bi-weekly updates
                "mbie_tourism": 30,  # Monthly updates
                "linz": 90,  # Quarterly updates
                "reinz": 7,  # Weekly updates
            }
            max_age_days = expected_freshness.get(source_name, 14)

            # Calculate freshness score (100 = fresh, 0 = very stale)
            if file_age_days <= max_age_days:
                score = max(0, 100 - (file_age_days / max_age_days) * 30)
                status = "fresh"
            elif file_age_days <= max_age_days * 2:
                score = max(0, 70 - (file_age_days / max_age_days) * 30)
                status = "aging"
                freshness_report["warnings"].append(
                    f"{source_name}: data is {file_age_days:.0f} days old"
                )
            else:
                score = max(0, 40 - (file_age_days / max_age_days) * 20)
                status = "stale"
                freshness_report["stale_sources"].append(source_name)
                freshness_report["warnings"].append(
                    f"{source_name}: data is STALE ({file_age_days:.0f} days)"
                )

            freshness_report["sources"][source_name] = {
                "status": status,
                "file_count": len(source_files),
                "freshness_score": round(score, 1),
                "age_days": round(file_age_days, 1),
                "max_age_days": max_age_days,
                "latest_file": latest_file.name,
                "issues": []
                if status == "fresh"
                else [f"Data is {file_age_days:.0f} days old (max: {max_age_days})"],
            }

            total_score += score
            source_count += 1

        if source_count > 0:
            freshness_report["overall_freshness_score"] = round(
                total_score / source_count, 1
            )

        return freshness_report

    def generate_ingestion_report(self) -> Dict[str, Any]:
        """Generate comprehensive ingestion report."""
        report = {
            "report_date": datetime.now().isoformat(),
            "ingestors_available": list(self.ingestors.keys()),
            "ingestion_status": self.ingestion_status,
            "data_directory": str(self.data_dir),
            "cache_entries": len(self._cache),
        }

        try:
            files = list(self.data_dir.glob("*.json"))
            report["file_count"] = len(files)

            file_info = []
            for file_path in files:
                stat = file_path.stat()
                file_info.append(
                    {
                        "filename": file_path.name,
                        "size_bytes": stat.st_size,
                        "last_modified": datetime.fromtimestamp(
                            stat.st_mtime
                        ).isoformat(),
                        "age_days": round(
                            (
                                datetime.now() - datetime.fromtimestamp(stat.st_mtime)
                            ).days,
                            1,
                        ),
                    }
                )

            report["file_details"] = sorted(
                file_info, key=lambda x: x["last_modified"], reverse=True
            )

            # Group by source
            sources = {}
            for file_path in files:
                filename = file_path.name
                if filename.startswith("rbnz_"):
                    source = "rbnz"
                elif filename.startswith("stats_nz_"):
                    source = "stats_nz"
                elif filename.startswith("linz_"):
                    source = "linz"
                elif filename.startswith("mbie_"):
                    source = "mbie"
                elif filename.startswith("reinz_"):
                    source = "reinz"
                elif filename.startswith("world_bank_"):
                    source = "world_bank"
                elif filename.startswith("trade_me"):
                    source = "trade_me"
                else:
                    source = "other"

                sources.setdefault(source, 0)
                sources[source] += 1

            report["files_by_source"] = sources

        except Exception as e:
            report["directory_error"] = str(e)

        return report

    def validate_data_quality(self) -> Dict[str, Any]:
        """Validate quality of ingested data."""
        quality_report = {
            "validation_date": datetime.now().isoformat(),
            "sources": {},
            "overall_quality_score": 0,
            "issues": [],
        }

        try:
            sources = ["rbnz", "stats_nz", "linz", "mbie", "reinz", "world_bank"]
            total_score = 0
            source_count = 0

            for source in sources:
                source_files = list(self.data_dir.glob(f"{source}_*.json"))

                if not source_files:
                    quality_report["sources"][source] = {
                        "status": "missing",
                        "file_count": 0,
                        "quality_score": 0,
                        "issues": ["No data files found"],
                    }
                    quality_report["issues"].append(f"{source}: No data files")
                    continue

                source_issues = []
                source_score = 80

                for file_path in source_files:
                    try:
                        with open(file_path, "r") as f:
                            data = json.load(f)

                        if isinstance(data, dict):
                            if "metadata" not in data:
                                source_issues.append(
                                    f"{file_path.name}: Missing metadata"
                                )
                                source_score -= 5

                            if "data" not in data and "features" not in data:
                                source_issues.append(
                                    f"{file_path.name}: No data/features key"
                                )
                                source_score -= 10

                        file_age = (
                            datetime.now()
                            - datetime.fromtimestamp(file_path.stat().st_mtime)
                        ).days
                        if file_age > 30:
                            source_issues.append(
                                f"{file_path.name}: Data is {file_age} days old"
                            )
                            source_score -= min(20, file_age - 30)

                    except json.JSONDecodeError:
                        source_issues.append(f"{file_path.name}: Invalid JSON")
                        source_score -= 15
                    except Exception as e:
                        source_issues.append(
                            f"{file_path.name}: Error reading - {str(e)[:50]}"
                        )
                        source_score -= 10

                source_score = max(0, min(100, source_score))

                quality_report["sources"][source] = {
                    "status": "present" if source_score >= 50 else "poor",
                    "file_count": len(source_files),
                    "quality_score": source_score,
                    "issues": source_issues,
                }

                total_score += source_score
                source_count += 1

            if source_count > 0:
                quality_report["overall_quality_score"] = round(
                    total_score / source_count, 1
                )

        except Exception as e:
            quality_report["validation_error"] = str(e)

        return quality_report

    def save_report(
        self, report: Dict[str, Any], report_name: str = "ingestion_report.json"
    ) -> str:
        """Save report to JSON file."""
        report_file = self.data_dir / report_name
        with open(report_file, "w") as f:
            json.dump(report, f, indent=2, default=str)
        self.logger.info("Saved report to %s", report_file)
        return str(report_file)


if __name__ == "__main__":
    import sys
    import argparse

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    parser = argparse.ArgumentParser(description="Bronze Layer Orchestrator")
    parser.add_argument(
        "--run",
        choices=[
            "all",
            "world_bank",
            "rbnz",
            "stats_nz",
            "linz",
            "mbie_tourism",
            "reinz",
            "trade_me",
        ],
        default="all",
        help="Ingestor(s) to run",
    )
    parser.add_argument(
        "--schedule",
        choices=["daily", "weekly", "monthly"],
        help="Run scheduled ingestion",
    )
    parser.add_argument(
        "--force", action="store_true", help="Force refresh (skip cache)"
    )
    parser.add_argument("--report", action="store_true", help="Generate report")
    parser.add_argument("--validate", action="store_true", help="Validate data quality")
    parser.add_argument("--freshness", action="store_true", help="Check data freshness")

    args = parser.parse_args()

    orchestrator = BronzeOrchestrator()

    try:
        if args.schedule:
            result = orchestrator.run_scheduled_ingestion(
                args.schedule, force_refresh=args.force
            )
            print(
                f"Scheduled ingestion ({args.schedule}): {'SUCCESS' if result['success'] else 'FAILED'}"
            )
            if not result["success"]:
                for ingestor, res in result["results"].items():
                    if not res.get("success", False):
                        print(f"  - {ingestor}: {res.get('error', 'Unknown error')}")

        elif args.freshness:
            freshness = orchestrator.check_data_freshness()
            print("Data Freshness Report:")
            print(f"Overall score: {freshness['overall_freshness_score']}/100")
            for source, info in freshness.get("sources", {}).items():
                status_icon = {
                    "fresh": "✓",
                    "aging": "~",
                    "stale": "✗",
                    "missing": "?",
                }.get(info.get("status"), "?")
                print(
                    f"  {status_icon} {source}: {info.get('freshness_score')}/100 (age: {info.get('age_days', 'N/A')} days)"
                )
            if freshness.get("warnings"):
                print("\nWarnings:")
                for w in freshness["warnings"]:
                    print(f"  - {w}")

        elif args.report:
            report = orchestrator.generate_ingestion_report()
            report_file = orchestrator.save_report(report)
            print(f"Report generated: {report_file}")
            print(f"Files in directory: {report.get('file_count', 0)}")
            print(f"Cache entries: {report.get('cache_entries', 0)}")

        elif args.validate:
            quality_report = orchestrator.validate_data_quality()
            print("Data Quality Report:")
            print(f"Overall score: {quality_report['overall_quality_score']}/100")
            for source, info in quality_report.get("sources", {}).items():
                status = "✓" if info.get("status") == "present" else "✗"
                print(
                    f"  {status} {source}: {info.get('quality_score')}/100 ({info.get('file_count')} files)"
                )
                if info.get("issues"):
                    for issue in info["issues"][:2]:
                        print(f"    - {issue}")

        else:
            result = orchestrator.run_ingestor(args.run, force_refresh=args.force)

            if args.run == "all":
                print(
                    f"Complete ingestion run: {'SUCCESS' if result['success'] else 'FAILED'}"
                )
                print(f"Time: {result.get('run_time_seconds', 0):.1f}s")
                print(
                    f"Ingestors: {result.get('ingestors_successful', 0)}/{result.get('ingestors_run', 0)} successful"
                )
            else:
                if result.get("success", False):
                    print(f"Ingestion {args.run}: SUCCESS")
                    if result.get("cached"):
                        print("  (served from cache)")
                    if "files_created" in result:
                        print(f"Files created: {result['files_created']}")
                else:
                    print(f"Ingestion {args.run}: FAILED")
                    print(f"Error: {result.get('error', 'Unknown error')}")

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

    sys.exit(0)
