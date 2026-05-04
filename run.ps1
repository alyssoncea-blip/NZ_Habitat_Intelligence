# NZ Habitat Intelligence Pipeline - PowerShell Task Runner
# Replaces Makefile for Windows environment
# Usage: .\run.ps1 <target>

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$DataPipeline = "$ProjectRoot\data_pipeline"

function Show-Help {
    Write-Host @"
NZ Habitat Intelligence - Pipeline Task Runner
================================================

Available targets:
  bronze      - Run raw data ingestion (6 ingestors)
  bronze-force - Force refresh all ingestors
  silver      - Transform Bronze to Silver (feature engineering)
  gold        - Build Gold tables (KPI calculation)
  pipeline    - Run full enhanced pipeline (bronze -> silver -> dbt -> GE)
  dashboard   - Start Plotly Dash dashboard
  all         - Run complete pipeline + start dashboard
  check       - System health check
  clean       - Remove temporary files and caches
  help        - Show this help message

Examples:
  .\run.ps1 bronze
  .\run.ps1 pipeline
  .\run.ps1 dashboard

"@
}

function Invoke-Bronze {
    Write-Host "Running Bronze ingestion..." -ForegroundColor Cyan
    Set-Location "$DataPipeline\bronze"
    & python bronze_orchestrator.py --run all
    if ($LASTEXITCODE -ne 0) { throw "Bronze ingestion failed" }
    Set-Location $ProjectRoot
}

function Invoke-BronzeForce {
    Write-Host "Running Bronze ingestion (force refresh)..." -ForegroundColor Cyan
    Set-Location "$DataPipeline\bronze"
    & python bronze_orchestrator.py --run all --force
    if ($LASTEXITCODE -ne 0) { throw "Bronze ingestion failed" }
    Set-Location $ProjectRoot
}

function Invoke-Silver {
    Write-Host "Running Silver feature engineering..." -ForegroundColor Cyan
    Set-Location $DataPipeline
    & python -m silver.feature_engineer
    if ($LASTEXITCODE -ne 0) { throw "Silver transformation failed" }
    Set-Location $ProjectRoot
}

function Invoke-Gold {
    Write-Host "Running Gold KPI calculation..." -ForegroundColor Cyan
    Set-Location $DataPipeline
    & python -m gold.kpi_calculator
    if ($LASTEXITCODE -ne 0) { throw "Gold calculation failed" }
    Set-Location $ProjectRoot
}

function Invoke-Pipeline {
    Write-Host "Running enhanced pipeline (bronze -> silver -> dbt -> GE)..." -ForegroundColor Cyan
    Set-Location $ProjectRoot
    & python data_pipeline/run_enhanced_pipeline.py --force
    if ($LASTEXITCODE -ne 0) { throw "Pipeline failed" }
}

function Invoke-Dashboard {
    Write-Host "Starting Dashboard..." -ForegroundColor Cyan
    Set-Location $ProjectRoot
    & python run_dashboard.py
}

function Invoke-All {
    Write-Host "Running complete pipeline: Bronze -> Silver -> Gold" -ForegroundColor Green
    Invoke-Pipeline
    Write-Host "Pipeline completed successfully!" -ForegroundColor Green
    Write-Host "Dashboards available at: http://127.0.0.1:8050/" -ForegroundColor Yellow
}

function Invoke-Check {
    Write-Host "System Health Check" -ForegroundColor Cyan
    Write-Host "====================" -ForegroundColor Cyan

    $bronzeFiles = Get-ChildItem -Path "$DataPipeline\bronze" -Filter "*.json" -ErrorAction SilentlyContinue | Where-Object { $_.Name -notlike "*.contract.*" }
    if ($bronzeFiles) {
        Write-Host "[OK] Bronze: $($bronzeFiles.Count) raw data files found" -ForegroundColor Green
    } else {
        Write-Host "[WARN] Bronze: No raw data files found" -ForegroundColor Yellow
    }

    $silverFiles = Get-ChildItem -Path "$DataPipeline\silver" -Filter "*.parquet" -ErrorAction SilentlyContinue
    if ($silverFiles) {
        Write-Host "[OK] Silver: $($silverFiles.Count) engineered features found" -ForegroundColor Green
    } else {
        Write-Host "[WARN] Silver: No features found" -ForegroundColor Yellow
    }

    $goldFiles = Get-ChildItem -Path "$DataPipeline\gold" -Filter "kpis-*_complete.parquet" -ErrorAction SilentlyContinue
    if ($goldFiles) {
        Write-Host "[OK] Gold: $($goldFiles.Count) KPI files found" -ForegroundColor Green
    } else {
        Write-Host "[WARN] Gold: No KPIs found" -ForegroundColor Yellow
    }

    if (Test-Path "$ProjectRoot\run_dashboard.py") {
        Write-Host "[OK] Dashboard runner exists" -ForegroundColor Green
    } else {
        Write-Host "[WARN] Dashboard runner not found" -ForegroundColor Yellow
    }

    if (Test-Path "$ProjectRoot\app\main.py") {
        Write-Host "[OK] Modular app exists" -ForegroundColor Green
    } else {
        Write-Host "[WARN] Modular app not found" -ForegroundColor Yellow
    }

    Write-Host "`nAvailable commands:" -ForegroundColor Cyan
    Write-Host "  .\run.ps1 bronze     - Run data ingestion"
    Write-Host "  .\run.ps1 pipeline   - Run full enhanced pipeline"
    Write-Host "  .\run.ps1 dashboard  - Start dashboard"
    Write-Host "  .\run.ps1 check      - System health check"
}

function Invoke-Clean {
    Write-Host "Cleaning temporary files..." -ForegroundColor Cyan

    Get-ChildItem -Path $ProjectRoot -Recurse -Directory -Filter "__pycache__" -ErrorAction SilentlyContinue | ForEach-Object {
        Remove-Item $_.FullName -Recurse -Force
        Write-Host "Removed: $($_.FullName)" -ForegroundColor Gray
    }

    Get-ChildItem -Path $ProjectRoot -Recurse -Filter "*.pyc" -ErrorAction SilentlyContinue | ForEach-Object {
        Remove-Item $_.FullName -Force
        Write-Host "Removed: $($_.FullName)" -ForegroundColor Gray
    }

    Get-ChildItem -Path "$ProjectRoot\logs" -Filter "*.log" -ErrorAction SilentlyContinue | ForEach-Object {
        Remove-Item $_.FullName -Force
        Write-Host "Removed: $($_.FullName)" -ForegroundColor Gray
    }

    if (Test-Path "$ProjectRoot\.pytest_cache") {
        Remove-Item "$ProjectRoot\.pytest_cache" -Recurse -Force
        Write-Host "Removed: .pytest_cache" -ForegroundColor Gray
    }

    Write-Host "Clean completed" -ForegroundColor Green
}

# Main entry point
$target = $args[0]

switch ($target) {
    "bronze"      { Invoke-Bronze }
    "bronze-force" { Invoke-BronzeForce }
    "silver"      { Invoke-Silver }
    "gold"        { Invoke-Gold }
    "pipeline"    { Invoke-Pipeline }
    "dashboard"   { Invoke-Dashboard }
    "all"         { Invoke-All }
    "check"       { Invoke-Check }
    "clean"       { Invoke-Clean }
    "help"        { Show-Help }
    Default       {
        if ($target) {
            Write-Host "Unknown target: $target" -ForegroundColor Red
        }
        Show-Help
    }
}
