"""dbt runner for NZ Habitat Intelligence Silver→Gold transformations."""
import logging
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

DBT_PROJECT_DIR = Path(__file__).parent.parent / "dbt_nz"


def run_dbt_command(
    command: str,
    project_dir: Optional[Path] = None,
    profiles_dir: Optional[Path] = None,
    target: str = "dev",
    extra_args: Optional[list] = None,
) -> Dict[str, Any]:
    """Run a dbt command and return results."""
    project_dir = project_dir or DBT_PROJECT_DIR
    profiles_dir = profiles_dir or (project_dir)

    cmd = [
        "dbt", command,
        "--project-dir", str(project_dir),
        "--profiles-dir", str(profiles_dir),
        "--target", target,
    ]
    if extra_args:
        cmd.extend(extra_args)

    logger.info("Running dbt command: %s", " ".join(cmd))

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,
            cwd=str(project_dir),
        )

        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
        }

    except subprocess.TimeoutExpired:
        return {"success": False, "error": "dbt command timed out after 300s"}
    except FileNotFoundError:
        return {"success": False, "error": "dbt not found. Install with: pip install dbt-core dbt-duckdb"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def run_dbt_run(models: Optional[str] = None, full_refresh: bool = False) -> Dict[str, Any]:
    """Run dbt models (Silver→Gold transformations)."""
    args = []
    if models:
        args.extend(["--select", models])
    if full_refresh:
        args.append("--full-refresh")

    result = run_dbt_command("run", extra_args=args if args else None)

    if result["success"]:
        logger.info("dbt run completed successfully")
    else:
        logger.error("dbt run failed: %s", result.get("stderr", result.get("error", "")))

    return result


def run_dbt_test(models: Optional[str] = None) -> Dict[str, Any]:
    """Run dbt tests on models."""
    args = []
    if models:
        args.extend(["--select", models])

    result = run_dbt_command("test", extra_args=args if args else None)

    if result["success"]:
        logger.info("dbt tests passed")
    else:
        logger.warning("dbt tests had failures: %s", result.get("stderr", ""))

    return result


def run_dbt_seed() -> Dict[str, Any]:
    """Load seed data (nz_regions reference table)."""
    result = run_dbt_command("seed")

    if result["success"]:
        logger.info("dbt seed loaded successfully")
    else:
        logger.error("dbt seed failed: %s", result.get("stderr", result.get("error", "")))

    return result


def run_dbt_docs_generate() -> Dict[str, Any]:
    """Generate dbt documentation."""
    result = run_dbt_command("docs", "generate")

    if result["success"]:
        logger.info("dbt docs generated")
    else:
        logger.error("dbt docs generation failed: %s", result.get("stderr", ""))

    return result


def run_full_pipeline() -> Dict[str, Any]:
    """Run complete dbt pipeline: seed → run → test."""
    results = {}

    logger.info("Starting dbt pipeline: seed → run → test")

    results["seed"] = run_dbt_seed()
    if not results["seed"]["success"]:
        logger.warning("dbt seed failed, continuing with run...")

    results["run"] = run_dbt_run()
    if not results["run"]["success"]:
        logger.error("dbt run failed, skipping tests")
        return results

    results["test"] = run_dbt_test()

    return results


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    import argparse

    parser = argparse.ArgumentParser(description="dbt runner for NZ Habitat Intelligence")
    parser.add_argument("command", choices=["run", "test", "seed", "docs", "pipeline"], default="pipeline", nargs="?")
    parser.add_argument("--models", help="Select specific models")
    parser.add_argument("--full-refresh", action="store_true", help="Full refresh all models")

    args = parser.parse_args()

    if args.command == "run":
        result = run_dbt_run(models=args.models, full_refresh=args.full_refresh)
    elif args.command == "test":
        result = run_dbt_test(models=args.models)
    elif args.command == "seed":
        result = run_dbt_seed()
    elif args.command == "docs":
        result = run_dbt_docs_generate()
    elif args.command == "pipeline":
        result = run_full_pipeline()
    else:
        result = {"success": False, "error": f"Unknown command: {args.command}"}

    if result.get("success"):
        print("dbt command completed successfully")
        if result.get("stdout"):
            print(result["stdout"])
        sys.exit(0)
    else:
        print(f"dbt command failed: {result.get('error', result.get('stderr', 'Unknown error'))}")
        if result.get("stderr"):
            print(result["stderr"])
        sys.exit(1)
