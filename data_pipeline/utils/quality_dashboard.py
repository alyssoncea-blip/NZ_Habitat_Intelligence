"""Data Quality Dashboard — Visualizes Great Expectations validation results.

Generates an HTML report with charts showing validation status,
expectation pass/fail rates, and data quality trends across pipeline layers.
"""
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def load_validation_results(validations_dir: str = "great_expectations/validations") -> List[Dict[str, Any]]:
    """Load all validation result JSON files.

    Args:
        validations_dir: Path to GE validation results directory.

    Returns:
        List of validation result dicts.
    """
    results = []
    vdir = Path(validations_dir)
    if not vdir.exists():
        logger.warning("Validations directory not found: %s", validations_dir)
        return results

    for fp in sorted(vdir.glob("*.json")):
        try:
            with open(fp, "r", encoding="utf-8") as f:
                data = json.load(f)
            data["_source_file"] = fp.name
            results.append(data)
        except Exception as e:
            logger.warning("Failed to load validation %s: %s", fp.name, e)

    return results


def summarize_validations(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Summarize validation results into aggregate metrics.

    Args:
        results: List of validation result dicts.

    Returns:
        Summary dict with pass/fail counts, success rate, and per-layer breakdown.
    """
    summary = {
        "total_validations": len(results),
        "total_expectations": 0,
        "passed_expectations": 0,
        "failed_expectations": 0,
        "success_rate": 0.0,
        "layers": {},
        "latest_by_layer": {},
        "generated_at": datetime.now().isoformat(),
    }

    for result in results:
        success = result.get("success", False)
        stats = result.get("statistics", {})
        n_evaluated = stats.get("evaluated_expectations", 0)
        n_successful = stats.get("successful_expectations", 0)
        n_failed = n_evaluated - n_successful

        summary["total_expectations"] += n_evaluated
        summary["passed_expectations"] += n_successful
        summary["failed_expectations"] += n_failed

        # Extract layer from result meta
        meta = result.get("meta", {})
        layer = meta.get("data_asset_name", meta.get("expectation_suite_name", "unknown"))
        if "/" in layer:
            layer = layer.split("/")[0]
        if "." in layer:
            layer = layer.split(".")[0]

        if layer not in summary["layers"]:
            summary["layers"][layer] = {
                "total": 0, "passed": 0, "failed": 0, "success": True,
                "validations": [],
            }

        summary["layers"][layer]["total"] += n_evaluated
        summary["layers"][layer]["passed"] += n_successful
        summary["layers"][layer]["failed"] += n_failed
        if not success:
            summary["layers"][layer]["success"] = False
        summary["layers"][layer]["validations"].append({
            "timestamp": result.get("meta", {}).get("run_id", {}).get("run_time", ""),
            "success": success,
            "evaluated": n_evaluated,
            "successful": n_successful,
        })

        # Track latest by layer
        ts = result.get("meta", {}).get("run_id", {}).get("run_time", "")
        if layer not in summary["latest_by_layer"] or ts > summary["latest_by_layer"][layer].get("timestamp", ""):
            summary["latest_by_layer"][layer] = {
                "timestamp": ts,
                "success": success,
                "evaluated": n_evaluated,
                "successful": n_successful,
                "failed": n_failed,
            }

    if summary["total_expectations"] > 0:
        summary["success_rate"] = round(
            summary["passed_expectations"] / summary["total_expectations"] * 100, 1
        )

    return summary


def generate_html_report(
    summary: Dict[str, Any],
    output_path: str = "great_expectations/validations/quality_report.html",
) -> str:
    """Generate an HTML data quality report.

    Args:
        summary: Validation summary dict from summarize_validations().
        output_path: Path to write the HTML report.

    Returns:
        Path to the generated report.
    """
    success_rate = summary["success_rate"]
    if success_rate >= 95:
        rate_color = "#10b981"
        rate_label = "Excellent"
    elif success_rate >= 80:
        rate_color = "#f59e0b"
        rate_label = "Good"
    elif success_rate >= 60:
        rate_color = "#f97316"
        rate_label = "Warning"
    else:
        rate_color = "#ef4444"
        rate_label = "Critical"

    layer_rows = ""
    for layer, info in summary["layers"].items():
        layer_rate = round(info["passed"] / info["total"] * 100, 1) if info["total"] > 0 else 0
        status_icon = "PASS" if info["success"] else "FAIL"
        status_color = "#10b981" if info["success"] else "#ef4444"
        layer_rows += f"""
        <tr>
            <td class="layer-name">{layer}</td>
            <td>{info['total']}</td>
            <td style="color:#10b981">{info['passed']}</td>
            <td style="color:{status_color}">{info['failed']}</td>
            <td>
                <div class="bar-bg">
                    <div class="bar-fill" style="width:{layer_rate}%;background:{status_color}"></div>
                </div>
                <span class="bar-label">{layer_rate}%</span>
            </td>
            <td style="color:{status_color};font-weight:bold">{status_icon}</td>
        </tr>"""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NZ Habitat Intelligence — Data Quality Report</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f8fafc; color: #1e293b; padding: 2rem; }}
        .container {{ max-width: 960px; margin: 0 auto; }}
        h1 {{ font-size: 1.75rem; margin-bottom: 0.25rem; }}
        .subtitle {{ color: #64748b; margin-bottom: 2rem; }}
        .summary-cards {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin-bottom: 2rem; }}
        .card {{ background: white; border-radius: 12px; padding: 1.5rem; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
        .card-label {{ font-size: 0.875rem; color: #64748b; margin-bottom: 0.5rem; }}
        .card-value {{ font-size: 2rem; font-weight: 700; }}
        .card-value.rate {{ color: {rate_color}; }}
        .card-sub {{ font-size: 0.75rem; color: #94a3b8; margin-top: 0.25rem; }}
        table {{ width: 100%; border-collapse: collapse; background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
        th {{ background: #f1f5f9; padding: 0.75rem 1rem; text-align: left; font-size: 0.875rem; color: #64748b; font-weight: 600; }}
        td {{ padding: 0.75rem 1rem; border-top: 1px solid #f1f5f9; font-size: 0.875rem; }}
        .layer-name {{ font-weight: 600; }}
        .bar-bg {{ width: 100px; height: 8px; background: #e2e8f0; border-radius: 4px; display: inline-block; vertical-align: middle; margin-right: 0.5rem; }}
        .bar-fill {{ height: 100%; border-radius: 4px; transition: width 0.3s; }}
        .bar-label {{ font-size: 0.75rem; color: #64748b; vertical-align: middle; }}
        .footer {{ margin-top: 2rem; text-align: center; color: #94a3b8; font-size: 0.75rem; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Data Quality Report</h1>
        <p class="subtitle">NZ Habitat Intelligence Pipeline — Great Expectations Validation Results</p>

        <div class="summary-cards">
            <div class="card">
                <div class="card-label">Overall Success Rate</div>
                <div class="card-value rate">{success_rate}%</div>
                <div class="card-sub">{rate_label}</div>
            </div>
            <div class="card">
                <div class="card-label">Total Expectations</div>
                <div class="card-value">{summary['total_expectations']}</div>
                <div class="card-sub">{summary['total_validations']} validations</div>
            </div>
            <div class="card">
                <div class="card-label">Passed</div>
                <div class="card-value" style="color:#10b981">{summary['passed_expectations']}</div>
            </div>
            <div class="card">
                <div class="card-label">Failed</div>
                <div class="card-value" style="color:#ef4444">{summary['failed_expectations']}</div>
            </div>
        </div>

        <table>
            <thead>
                <tr>
                    <th>Layer</th>
                    <th>Total</th>
                    <th>Passed</th>
                    <th>Failed</th>
                    <th>Rate</th>
                    <th>Status</th>
                </tr>
            </thead>
            <tbody>
                {layer_rows}
            </tbody>
        </table>

        <div class="footer">
            Generated at {summary['generated_at']}
        </div>
    </div>
</body>
</html>"""

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    logger.info("Data quality report generated: %s", output_path)
    return output_path


def run_quality_report(
    validations_dir: str = "great_expectations/validations",
    output_path: str = "great_expectations/validations/quality_report.html",
) -> Dict[str, Any]:
    """Run full quality report generation.

    Args:
        validations_dir: Path to GE validation results.
        output_path: Path for the HTML report.

    Returns:
        Validation summary dict.
    """
    results = load_validation_results(validations_dir)
    if not results:
        logger.warning("No validation results found")
        return {"total_validations": 0, "success_rate": 0.0}

    summary = summarize_validations(results)
    generate_html_report(summary, output_path)
    return summary
