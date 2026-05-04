#!/usr/bin/env python3
"""
NZ Habitat Intelligence Dashboard Runner
Simplified entry point to run the modular dashboard
"""
import sys
import os

def check_data_requirements():
    """Check if required data files are available"""
    gold_dir = os.path.join(os.path.dirname(__file__), 'data_pipeline', 'gold')
    
    # List of expected parquet files
    expected_files = [
        'kpis-01-executive_complete.parquet',
        'kpis-02-housing_complete.parquet',
        'kpis-03-tourism_complete.parquet',
        'kpis-04-macro_complete.parquet',
        'kpis-05-affordability_complete.parquet',
        'kpis-06-forecast_complete.parquet'
    ]
    
    missing_files = []
    for file in expected_files:
        filepath = os.path.join(gold_dir, file)
        if not os.path.exists(filepath):
            missing_files.append(file)
    
    if missing_files:
        print("WARNING: Some data files are missing:")
        for file in missing_files:
            print(f"   - {file}")
        
        response = input("\nDo you want to run the data pipeline first? (y/N): ").strip().lower()
        if response == 'y':
            print("\nRunning data pipeline...")
            try:
                import subprocess
                result = subprocess.run(
                    [sys.executable, "data_pipeline/run_enhanced_pipeline.py", "--force"],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    print("Pipeline executed successfully!")
                else:
                    print(f"Error running pipeline: {result.stderr}")
                    return False
            except Exception as e:
                print(f"Error: {e}")
                return False
        else:
            print("WARNING: Dashboard may not work correctly without complete data.")
            return True
    
    return True

def main():
    """Main function"""
    print("\n" + "=" * 60)
    print("STARTING NZ HABITAT INTELLIGENCE DASHBOARD")
    print("=" * 60)
    
    # Check requirements
    print("\nChecking requirements...")
    
    # 1. Python version
    python_version = sys.version_info
    if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 8):
        print(f"ERROR: Python 3.8+ required (current: {sys.version})")
        return 1
    
    # 2. Data requirements
    if not check_data_requirements():
        print("ERROR: Data requirements not met")
        return 1
    
    # 3. Dependencies
    print("Checking dependencies...")
    try:
        import dash
        import dash_bootstrap_components
        import pandas
        import duckdb
        print("Main dependencies OK")
    except ImportError as e:
        print(f"ERROR: Missing dependency: {e}")
        print("   Run: pip install -r requirements.txt")
        return 1

    # 4. Data integrity check (verify gold parquet files exist and are readable)
    print("Running data integrity check...")
    try:
        import glob
        gold_dir = os.path.join(os.path.dirname(__file__), 'data_pipeline', 'gold')
        parquet_files = glob.glob(os.path.join(gold_dir, 'kpis-*_complete.parquet'))
        if len(parquet_files) < 6:
            print(f"WARNING: Only {len(parquet_files)}/6 gold KPI files found")
            print("   Run: python data_pipeline/run_enhanced_pipeline.py --force")
        else:
            # Verify files are readable
            import pandas as pd
            for f in parquet_files:
                df = pd.read_parquet(f)
                if df.empty:
                    print(f"WARNING: {os.path.basename(f)} is empty")
            print(f"Data check OK ({len(parquet_files)} gold files verified)")
    except Exception as e:
        print(f"WARNING: Could not verify data integrity: {e}")
        print("   Dashboard may show incomplete data")
    
    # 5. Import and run the app
    print("\nStarting dashboard...")
    try:
        from app.main import run_app
        
        # Configuration
        host = '0.0.0.0'
        port = 8050
        
        # Optional host/port configuration
        if len(sys.argv) > 1:
            if sys.argv[1] in ['--help', '-h']:
                print("\nUSAGE: python run_dashboard.py [host] [port]")
                print("\nExamples:")
                print("  python run_dashboard.py                 # localhost:8050")
                print("  python run_dashboard.py 0.0.0.0 8080   # network:8080")
                print("  python run_dashboard.py --help         # this help")
                return 0
            
            host = sys.argv[1]
            if len(sys.argv) > 2:
                try:
                    port = int(sys.argv[2])
                except ValueError:
                    print(f"ERROR: Invalid port: {sys.argv[2]}")
                    return 1
        
        # Run dashboard
        run_app(debug=True, host=host, port=port)
        return 0
        
    except Exception as e:
        print(f"\nCRITICAL ERROR: {e}")
        print("\nTroubleshooting:")
        print("1. Check if data pipeline was executed")
        print("2. Check if all dependencies are installed")
        print("3. Run 'python check_data.py' for diagnosis")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
