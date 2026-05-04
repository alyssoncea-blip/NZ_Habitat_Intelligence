"""Deployment definitions for NZ Habitat Intelligence Prefect flows."""
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from prefect.deployments import Deployment
from prefect.filesystems import LocalFileSystem
from prefect.infrastructure import Process

from data_pipeline.orchestration.flows.daily_pipeline import run_daily_pipeline
from data_pipeline.orchestration.flows.scheduled_flows import (
    run_daily_ingestion,
    run_weekly_ingestion,
    run_monthly_ingestion,
    run_full_pipeline,
    daily_ingestion_schedule,
    weekly_ingestion_schedule,
    monthly_ingestion_schedule,
    full_pipeline_schedule,
)


def build_deployments():
    """Build and apply all deployments."""
    deployments = [
        Deployment.build_from_flow(
            flow=run_daily_pipeline,
            name="daily-pipeline",
            schedule=None,
            work_queue_name="nz-habitat",
            infra_overrides={"env": {"PYTHONUNBUFFERED": "1"}},
            apply=True,
        ),
        Deployment.build_from_flow(
            flow=run_daily_ingestion,
            name="daily-ingestion",
            schedule=daily_ingestion_schedule,
            work_queue_name="nz-habitat-ingestion",
            infra_overrides={"env": {"PYTHONUNBUFFERED": "1"}},
            apply=True,
        ),
        Deployment.build_from_flow(
            flow=run_weekly_ingestion,
            name="weekly-ingestion",
            schedule=weekly_ingestion_schedule,
            work_queue_name="nz-habitat-ingestion",
            infra_overrides={"env": {"PYTHONUNBUFFERED": "1"}},
            apply=True,
        ),
        Deployment.build_from_flow(
            flow=run_monthly_ingestion,
            name="monthly-ingestion",
            schedule=monthly_ingestion_schedule,
            work_queue_name="nz-habitat-ingestion",
            infra_overrides={"env": {"PYTHONUNBUFFERED": "1"}},
            apply=True,
        ),
        Deployment.build_from_flow(
            flow=run_full_pipeline,
            name="full-pipeline",
            schedule=full_pipeline_schedule,
            work_queue_name="nz-habitat",
            infra_overrides={"env": {"PYTHONUNBUFFERED": "1"}},
            apply=True,
        ),
    ]
    return deployments


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Deploy Prefect flows")
    parser.add_argument(
        "action",
        choices=["build", "apply", "all"],
        default="all",
        nargs="?",
        help="Action to perform",
    )
    args = parser.parse_args()

    print("Building deployments...")
    deployments = build_deployments()
    print(f"Deployed {len(deployments)} flows:")
    for d in deployments:
        print(f"  - {d.name} ({d.flow_name})")
