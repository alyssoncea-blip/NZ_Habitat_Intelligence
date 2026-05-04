@echo off
set START_DASHBOARD=1
if "%1"=="--no-dashboard" set START_DASHBOARD=0

echo ======================================
echo NZ HABITAT INTELLIGENCE - DATA PIPELINE
echo ======================================

echo.
echo [1/4] RUNNING ENHANCED PIPELINE...
python data_pipeline\run_enhanced_pipeline.py --force
if errorlevel 1 goto :error

echo.
echo [2/4] PIPELINE COMPLETE
echo.
if "%START_DASHBOARD%"=="1" (
    echo [3/4] STARTING DASHBOARD...
    echo Dashboard will be available at: http://127.0.0.1:8050/
    echo.
    python run_dashboard.py
    if errorlevel 1 goto :error
    pause
) else (
    echo Skipping dashboard start (--no-dashboard).
)
goto :eof

:error
echo.
echo Pipeline failed. Check the error logs above.
pause
exit /b 1
