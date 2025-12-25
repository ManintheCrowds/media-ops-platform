"""Test if the server can start successfully."""

import sys
import json
from pathlib import Path

LOG_PATH = Path(r"d:\CodeRepositories\.cursor\debug.log")

def log_entry(session_id, run_id, hypothesis_id, location, message, data):
    """Write debug log entry."""
    entry = {
        "sessionId": session_id,
        "runId": run_id,
        "hypothesisId": hypothesis_id,
        "location": location,
        "message": message,
        "data": data,
        "timestamp": int(__import__('time').time() * 1000)
    }
    try:
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception:
        pass

def test_imports():
    """Test if all required imports work."""
    # #region agent log
    log_entry("server-test", "run1", "H-IMPORTS", "test_server_startup.py:test_imports", "Testing required imports", {
        "python": sys.executable,
        "version": sys.version
    })
    # #endregion agent log
    
    imports_to_test = [
        ("pydantic_settings", "pydantic_settings"),
        ("httpx", "httpx"),
        ("fastapi", "fastapi"),
        ("uvicorn", "uvicorn"),
        ("sqlalchemy", "sqlalchemy"),
        ("psycopg2", "psycopg2"),
    ]
    
    results = {}
    for pkg_name, import_name in imports_to_test:
        try:
            __import__(import_name)
            results[pkg_name] = {"success": True}
            # #region agent log
            log_entry("server-test", "run1", "H-IMPORTS", "test_server_startup.py:test_imports", f"Import successful: {pkg_name}", {
                "package": pkg_name,
                "success": True
            })
            # #endregion agent log
        except ImportError as e:
            results[pkg_name] = {"success": False, "error": str(e)}
            # #region agent log
            log_entry("server-test", "run1", "H-IMPORTS", "test_server_startup.py:test_imports", f"Import failed: {pkg_name}", {
                "package": pkg_name,
                "success": False,
                "error": str(e)
            })
            # #endregion agent log
    
    return results

def test_app_import():
    """Test if the FastAPI app can be imported."""
    # #region agent log
    log_entry("server-test", "run1", "H-APP-IMPORT", "test_server_startup.py:test_app_import", "Testing app.main import", {})
    # #endregion agent log
    
    try:
        from app.main import app
        # #region agent log
        log_entry("server-test", "run1", "H-APP-IMPORT", "test_server_startup.py:test_app_import", "App import successful", {
            "success": True,
            "app_type": type(app).__name__
        })
        # #endregion agent log
        return {"success": True}
    except Exception as e:
        # #region agent log
        log_entry("server-test", "run1", "H-APP-IMPORT", "test_server_startup.py:test_app_import", "App import failed", {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__
        })
        # #endregion agent log
        import traceback
        return {"success": False, "error": str(e), "traceback": traceback.format_exc()}

def main():
    """Run server startup tests."""
    print("=" * 80)
    print("SERVER STARTUP DIAGNOSTICS")
    print("=" * 80)
    print()
    
    # #region agent log
    log_entry("server-test", "run1", "H0", "test_server_startup.py:main", "Starting server startup tests", {
        "python": sys.executable,
        "version": sys.version
    })
    # #endregion agent log
    
    print(f"Python: {sys.executable}")
    print(f"Version: {sys.version}")
    print()
    
    # Test imports
    print("1. Testing required package imports...")
    import_results = test_imports()
    
    all_imports_ok = True
    for pkg, result in import_results.items():
        status = "OK" if result["success"] else "FAIL"
        print(f"   {status}: {pkg}")
        if not result["success"]:
            all_imports_ok = False
            print(f"      Error: {result.get('error', 'Unknown')}")
    
    print()
    
    if not all_imports_ok:
        print("=" * 80)
        print("ERROR: Some required packages are missing!")
        print("=" * 80)
        print()
        print("Install dependencies with:")
        print("  python install_dependencies_fixed.py")
        print("  python -m pip install --only-binary :all: psycopg2-binary")
        return False
    
    # Test app import
    print("2. Testing FastAPI app import...")
    app_result = test_app_import()
    
    if app_result["success"]:
        print("   OK: App imported successfully")
        print()
        print("=" * 80)
        print("SUCCESS: Server can start!")
        print("=" * 80)
        print()
        print("Start the server with:")
        print("  .\\restart_server.ps1")
        return True
    else:
        print(f"   FAIL: {app_result.get('error', 'Unknown error')}")
        print()
        print("=" * 80)
        print("ERROR: Cannot import FastAPI app")
        print("=" * 80)
        print()
        if "traceback" in app_result:
            print("Traceback:")
            print(app_result["traceback"])
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

