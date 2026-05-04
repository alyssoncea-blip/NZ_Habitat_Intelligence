"""Unit tests for Prefect orchestration flows and tasks."""

import pytest

# Skip all tests if prefect is not installed
pytest.importorskip("prefect", reason="Prefect not installed")


class TestPrefectImports:
    """Test that all Prefect modules import correctly."""

    def test_import_bronze_tasks(self):
        """Test bronze tasks import."""
        from data_pipeline.orchestration.tasks.bronze_tasks import (
            ingest_world_bank,
            ingest_rbnz,
            ingest_stats_nz,
            ingest_mbie_tourism,
            ingest_linz,
            ingest_reinz,
            ingest_all_bronze,
        )

        assert ingest_world_bank is not None
        assert ingest_rbnz is not None
        assert ingest_stats_nz is not None
        assert ingest_mbie_tourism is not None
        assert ingest_linz is not None
        assert ingest_reinz is not None
        assert ingest_all_bronze is not None

    def test_import_silver_tasks(self):
        """Test silver tasks import."""
        from data_pipeline.orchestration.tasks.silver_tasks import (
            compute_affordability,
            compute_interest_rate_lag,
            compute_tourism_pressure,
            compute_supply_deficit,
            compute_rent_income_ratio,
            compute_tourism_lag_analysis,
        )

        assert compute_affordability is not None
        assert compute_interest_rate_lag is not None
        assert compute_tourism_pressure is not None
        assert compute_supply_deficit is not None
        assert compute_rent_income_ratio is not None
        assert compute_tourism_lag_analysis is not None

    def test_import_dbt_tasks(self):
        """Test dbt tasks import."""
        from data_pipeline.orchestration.tasks.dbt_tasks import (
            dbt_seed_task,
            dbt_run_task,
            dbt_test_task,
        )

        assert dbt_seed_task is not None
        assert dbt_run_task is not None
        assert dbt_test_task is not None

    def test_import_ge_tasks(self):
        """Test GE tasks import."""
        from data_pipeline.orchestration.tasks.ge_tasks import (
            validate_bronze_layer,
            validate_silver_layer,
            validate_gold_layer,
        )

        assert validate_bronze_layer is not None
        assert validate_silver_layer is not None
        assert validate_gold_layer is not None

    def test_import_daily_pipeline_flow(self):
        """Test daily pipeline flow import."""
        from data_pipeline.orchestration.flows.daily_pipeline import run_daily_pipeline

        assert run_daily_pipeline is not None
        assert run_daily_pipeline.name == "nz-habitat-daily-pipeline"

    def test_import_scheduled_flows(self):
        """Test scheduled flows import."""
        from data_pipeline.orchestration.flows.scheduled_flows import (
            run_daily_ingestion,
            run_weekly_ingestion,
            run_monthly_ingestion,
            run_full_pipeline,
        )

        assert run_daily_ingestion is not None
        assert run_weekly_ingestion is not None
        assert run_monthly_ingestion is not None
        assert run_full_pipeline is not None

    def test_import_config_settings(self):
        """Test config settings import."""
        from data_pipeline.orchestration.config.settings import (
            PROJECT_ROOT,
            RETRY_CONFIG,
        )

        assert PROJECT_ROOT is not None
        assert RETRY_CONFIG is not None
        assert "bronze" in RETRY_CONFIG
        assert "silver" in RETRY_CONFIG
        assert "dbt" in RETRY_CONFIG
        assert "ge" in RETRY_CONFIG

    def test_bronze_task_retry_config(self):
        """Test bronze tasks have correct retry config."""
        from data_pipeline.orchestration.tasks.bronze_tasks import ingest_world_bank

        assert ingest_world_bank.retries == 3
        assert ingest_world_bank.retry_delay_seconds == 60

    def test_silver_task_retry_config(self):
        """Test silver tasks have correct retry config."""
        from data_pipeline.orchestration.tasks.silver_tasks import compute_affordability

        assert compute_affordability.retries == 2
        assert compute_affordability.retry_delay_seconds == 30

    def test_dbt_task_retry_config(self):
        """Test dbt tasks have correct retry config."""
        from data_pipeline.orchestration.tasks.dbt_tasks import dbt_seed_task

        assert dbt_seed_task.retries == 2
        assert dbt_seed_task.retry_delay_seconds == 120

    def test_ge_task_retry_config(self):
        """Test GE tasks have correct retry config."""
        from data_pipeline.orchestration.tasks.ge_tasks import validate_bronze_layer

        assert validate_bronze_layer.retries == 1
        assert validate_bronze_layer.retry_delay_seconds == 30

    def test_flow_has_description(self):
        """Test flow has description."""
        from data_pipeline.orchestration.flows.daily_pipeline import run_daily_pipeline

        assert run_daily_pipeline.description is not None
        assert len(run_daily_pipeline.description) > 0

    def test_scheduled_flows_have_schedules(self):
        """Test scheduled flows have CronSchedule attached."""
        from data_pipeline.orchestration.flows.scheduled_flows import (
            daily_ingestion_schedule,
            weekly_ingestion_schedule,
            monthly_ingestion_schedule,
            full_pipeline_schedule,
        )

        assert daily_ingestion_schedule is not None
        assert weekly_ingestion_schedule is not None
        assert monthly_ingestion_schedule is not None
        assert full_pipeline_schedule is not None
