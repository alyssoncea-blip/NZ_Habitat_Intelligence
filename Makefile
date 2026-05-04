# NZ Habitat Intelligence Pipeline Makefile

.PHONY: bronze silver gold pipeline dashboard lint test freshness validate docker-build docker-run docker-pipeline docker-dbt docker-ge all clean help dbt-run dbt-test dbt-seed ge-validate enhanced-pipeline prefect-server prefect-worker prefect-deploy prefect-run

PYTHON := python
PROJECT_ROOT := $(shell pwd)
DATA_PIPELINE := $(PROJECT_ROOT)/data_pipeline

# ── Data Pipeline ──────────────────────────────────────────────────────────
bronze:
	cd $(DATA_PIPELINE)/bronze && $(PYTHON) -m bronze_orchestrator --run all

bronze-force:
	cd $(DATA_PIPELINE)/bronze && $(PYTHON) -m bronze_orchestrator --run all --force

silver:
	cd $(DATA_PIPELINE) && $(PYTHON) -m silver.feature_engineer

gold:
	cd $(DATA_PIPELINE) && $(PYTHON) -m gold.kpi_calculator

pipeline: bronze silver gold

freshness:
	cd $(DATA_PIPELINE)/bronze && $(PYTHON) -m bronze_orchestrator --freshness

validate:
	cd $(DATA_PIPELINE)/bronze && $(PYTHON) -m bronze_orchestrator --validate

# ── dbt (Silver→Gold declarative) ─────────────────────────────────────────
dbt-seed:
	cd $(PROJECT_ROOT)/dbt_nz && $(PYTHON) -m dbt seed --profiles-dir .

dbt-run:
	cd $(PROJECT_ROOT)/dbt_nz && $(PYTHON) -m dbt run --profiles-dir .

dbt-test:
	cd $(PROJECT_ROOT)/dbt_nz && $(PYTHON) -m dbt test --profiles-dir .

dbt-docs:
	cd $(PROJECT_ROOT)/dbt_nz && $(PYTHON) -m dbt docs generate --profiles-dir .

dbt-full: dbt-seed dbt-run dbt-test

# ── Great Expectations ────────────────────────────────────────────────────
ge-validate:
	cd $(PROJECT_ROOT) && $(PYTHON) great_expectations/validate.py

# ── Enhanced Pipeline (bronze → silver → dbt → GE) ────────────────────────
enhanced-pipeline:
	cd $(PROJECT_ROOT) && $(PYTHON) data_pipeline/run_enhanced_pipeline.py

enhanced-pipeline-force:
	cd $(PROJECT_ROOT) && $(PYTHON) data_pipeline/run_enhanced_pipeline.py --force

# ── Prefect Orchestration ─────────────────────────────────────────────────
prefect-server:
	prefect server start

prefect-server-docker:
	docker compose up -d prefect-server

prefect-worker:
	prefect worker start -p nz-habitat

prefect-worker-docker:
	docker compose --profile prefect up -d prefect-worker prefect-worker-ingestion

prefect-deploy:
	cd $(PROJECT_ROOT) && $(PYTHON) data_pipeline/orchestration/deployments/deploy.py

prefect-deploy-yaml:
	cd $(PROJECT_ROOT) && prefect deploy

prefect-run:
	cd $(PROJECT_ROOT) && $(PYTHON) data_pipeline/orchestration/flows/daily_pipeline.py

prefect-run-force:
	cd $(PROJECT_ROOT) && $(PYTHON) data_pipeline/orchestration/flows/daily_pipeline.py --force

prefect-run-scheduled:
	cd $(PROJECT_ROOT) && $(PYTHON) data_pipeline/orchestration/flows/scheduled_flows.py

prefect-notifications:
	cd $(PROJECT_ROOT) && $(PYTHON) data_pipeline/orchestration/notifications/prefect_blocks.py

prefect-all: prefect-server-docker prefect-deploy prefect-worker-docker
	@echo ""
	@echo "Prefect orchestration started:"
	@echo "  UI: http://127.0.0.1:4200"
	@echo "  Dashboard: http://127.0.0.1:8050"

# ── Dashboard ─────────────────────────────────────────────────────────────
dashboard:
	cd $(PROJECT_ROOT) && $(PYTHON) run_dashboard.py

# ── Quality ───────────────────────────────────────────────────────────────
lint:
	ruff check app/ data_pipeline/ great_expectations/ --fix
	black app/ data_pipeline/ great_expectations/

lint-check:
	ruff check app/ data_pipeline/ great_expectations/
	black --check app/ data_pipeline/ great_expectations/

test:
	pytest -v --tb=short

# ── Docker ────────────────────────────────────────────────────────────────
docker-build:
	docker build -t nz-habitat-intelligence:latest .

docker-run:
	docker compose up -d dashboard

docker-pipeline:
	docker compose --profile pipeline run pipeline

docker-dbt:
	docker compose --profile dbt run dbt

docker-ge:
	docker compose --profile ge run ge-validation

docker-prefect:
	docker compose --profile prefect up -d prefect-server prefect-worker prefect-worker-ingestion

docker-stop:
	docker compose down

# ── Complete ──────────────────────────────────────────────────────────────
all: lint-check test enhanced-pipeline
	@echo ""
	@echo "Full pipeline completed: lint → test → bronze → silver → dbt → GE"
	@echo "Dashboard: http://127.0.0.1:8050/"

# ── Cleanup ───────────────────────────────────────────────────────────────
clean:
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -name "*.pyc" -delete 2>/dev/null || true
	@find . -name "*.log" -delete 2>/dev/null || true
	@rm -rf .pytest_cache 2>/dev/null || true
	@rm -rf dbt_nz/target 2>/dev/null || true
	@rm -rf dbt_nz/dbt_packages 2>/dev/null || true
	@echo "Clean completed"

# ── Help ──────────────────────────────────────────────────────────────────
help:
	@echo "NZ Habitat Intelligence - Pipeline Makefile"
	@echo "============================================"
	@echo ""
	@echo "Data Pipeline:"
	@echo "  bronze            - Run raw data ingestion (6 ingestors)"
	@echo "  bronze-force      - Force refresh (skip cache)"
	@echo "  silver            - Feature engineering (Python)"
	@echo "  gold              - KPI calculation (Python)"
	@echo "  pipeline          - bronze → silver → gold"
	@echo ""
	@echo "dbt (Declarative Silver→Gold):"
	@echo "  dbt-seed          - Load reference data (nz_regions)"
	@echo "  dbt-run           - Run all dbt models"
	@echo "  dbt-test          - Run dbt tests"
	@echo "  dbt-docs          - Generate dbt documentation"
	@echo "  dbt-full          - seed → run → test"
	@echo ""
	@echo "Great Expectations (Data Quality):"
	@echo "  ge-validate       - Run all GE validations"
	@echo ""
	@echo "Enhanced Pipeline (all stages):"
	@echo "  enhanced-pipeline - bronze → silver → dbt → GE"
	@echo "  enhanced-pipeline-force - Same with force refresh"
	@echo ""
	@echo "Prefect Orchestration:"
	@echo "  prefect-server    - Start local Prefect server (CLI)"
	@echo "  prefect-server-docker - Start Prefect server (Docker)"
	@echo "  prefect-worker    - Start Prefect worker (CLI)"
	@echo "  prefect-worker-docker - Start Prefect workers (Docker)"
	@echo "  prefect-deploy    - Deploy flows to Prefect"
	@echo "  prefect-deploy-yaml - Deploy flows via prefect.yaml"
	@echo "  prefect-run       - Run daily pipeline via Prefect"
	@echo "  prefect-run-force - Run with force refresh"
	@echo "  prefect-run-scheduled - Run scheduled ingestion flows"
	@echo "  prefect-notifications - Setup notification blocks"
	@echo "  prefect-all       - Start server + deploy + workers (Docker)"
	@echo ""
	@echo "Dashboard:"
	@echo "  dashboard         - Start Plotly Dash dashboard"
	@echo ""
	@echo "Quality:"
	@echo "  lint              - Run ruff + black (auto-fix)"
	@echo "  lint-check        - Run ruff + black (check only)"
	@echo "  test              - Run pytest"
	@echo ""
	@echo "Docker:"
	@echo "  docker-build      - Build Docker image"
	@echo "  docker-run        - Start dashboard"
	@echo "  docker-pipeline   - Run enhanced pipeline"
	@echo "  docker-dbt        - Run dbt transformations"
	@echo "  docker-ge         - Run GE validations"
	@echo "  docker-prefect    - Start Prefect server + workers"
	@echo "  docker-stop       - Stop all containers"
	@echo ""
	@echo "Other:"
	@echo "  all               - lint → test → enhanced-pipeline"
	@echo "  clean             - Remove temp files"
	@echo "  help              - Show this message"
