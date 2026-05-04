#!/usr/bin/env python3
"""Simple Gold data validation (schema + freshness)."""

import argparse
import os
import sys
from datetime import datetime, timedelta

import pandas as pd

EXPECTED_FILES = [
    "kpis-01-executive_complete.parquet",
    "kpis-02-housing_complete.parquet",
    "kpis-03-tourism_complete.parquet",
    "kpis-04-macro_complete.parquet",
    "kpis-05-affordability_complete.parquet",
    "kpis-06-forecast_complete.parquet",
]

REQUIRED_COLUMNS = ["name", "value", "unit", "description", "category", "source"]


def validate_gold_data(base_dir, max_age_days=45):
    issues = []
    stats = {}
    newest_mtime = None

    for filename in EXPECTED_FILES:
        path = os.path.join(base_dir, filename)
        if not os.path.exists(path):
            issues.append(f"missing_file:{filename}")
            continue

        mtime = datetime.fromtimestamp(os.path.getmtime(path))
        if newest_mtime is None or mtime > newest_mtime:
            newest_mtime = mtime

        try:
            df = pd.read_parquet(path)
        except Exception as exc:
            issues.append(f"read_error:{filename}:{exc}")
            continue

        missing_columns = [col for col in REQUIRED_COLUMNS if col not in df.columns]
        if missing_columns:
            issues.append(
                f"schema_error:{filename}:missing={','.join(missing_columns)}"
            )

        row_count = len(df)
        null_value_count = (
            int(df["value"].isna().sum()) if "value" in df.columns else row_count
        )

        if row_count == 0:
            issues.append(f"empty_file:{filename}")

        stats[filename] = {
            "rows": row_count,
            "null_values": null_value_count,
            "updated_at": mtime.isoformat(),
        }

    if newest_mtime is None:
        issues.append("freshness_error:no_files_found")
    else:
        age = datetime.now() - newest_mtime
        if age > timedelta(days=max_age_days):
            issues.append(f"freshness_error:latest_file_age_days={age.days}")

    return len(issues) == 0, issues, stats


def main():
    parser = argparse.ArgumentParser(description="Validate Gold KPI files.")
    parser.add_argument(
        "--gold-dir",
        default=os.path.join("data_pipeline", "gold"),
        help="Gold directory path",
    )
    parser.add_argument(
        "--max-age-days",
        type=int,
        default=45,
        help="Maximum allowed age (days) for latest Gold file",
    )
    parser.add_argument(
        "--quiet", action="store_true", help="Only print one-line result"
    )
    args = parser.parse_args()

    ok, issues, stats = validate_gold_data(args.gold_dir, args.max_age_days)

    if args.quiet:
        if ok:
            print("data_check=OK")
            return 0
        print(f"data_check=FAIL issues={len(issues)}")
        return 1

    print("=" * 60)
    print("NZ Habitat Intelligence - Gold Data Check")
    print("=" * 60)

    if ok:
        print("Status: OK")
    else:
        print("Status: FAIL")
        for issue in issues:
            print(f" - {issue}")

    if stats:
        print("\nFiles:")
        for filename, info in stats.items():
            print(
                f" - {filename}: rows={info['rows']} null_values={info['null_values']} updated_at={info['updated_at']}"
            )

    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
