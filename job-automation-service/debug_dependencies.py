"""Debug script to diagnose dependency installation issues."""

import sys
import subprocess
import json
from pathlib import Path

# Log path from system reminder
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

def check_python_info():
    """Check Python version and path."""
    # #region agent log
    log_entry("dep-debug", "run1", "H1", "debug_dependencies.py:check_python_info", "Checking Python info", {
        "version": sys.version,
        "executable": sys.executable,
        "version_info": str(sys.version_info),
        "platform": sys.platform
    })
    # #endregion agent log
    
    return {
        "version": sys.version,
        "executable": sys.executable,
        "version_info": sys.version_info,
        "platform": sys.platform
    }

def check_pip_info():
    """Check pip version and location."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "--version"],
            capture_output=True,
            text=True,
            timeout=10
        )
        # #region agent log
        log_entry("dep-debug", "run1", "H2", "debug_dependencies.py:check_pip_info", "Checking pip info", {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        })
        # #endregion agent log
        
        return {
            "version_output": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        }
    except Exception as e:
        # #region agent log
        log_entry("dep-debug", "run1", "H2", "debug_dependencies.py:check_pip_info", "Error checking pip", {
            "error": str(e),
            "error_type": type(e).__name__
        })
        # #endregion agent log
        return {"error": str(e)}

def check_installed_packages():
    """Check which packages are installed."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "list"],
            capture_output=True,
            text=True,
            timeout=30
        )
        packages = {}
        for line in result.stdout.split('\n')[2:]:  # Skip header
            if line.strip():
                parts = line.split()
                if len(parts) >= 2:
                    packages[parts[0].lower()] = parts[1]
        
        # #region agent log
        log_entry("dep-debug", "run1", "H3", "debug_dependencies.py:check_installed_packages", "Checking installed packages", {
            "total_packages": len(packages),
            "has_httpx": "httpx" in packages,
            "has_pydantic_settings": "pydantic-settings" in packages or "pydantic_settings" in packages,
            "has_psycopg2": "psycopg2-binary" in packages or "psycopg2" in packages,
            "sample_packages": dict(list(packages.items())[:10])
        })
        # #endregion agent log
        
        return packages
    except Exception as e:
        # #region agent log
        log_entry("dep-debug", "run1", "H3", "debug_dependencies.py:check_installed_packages", "Error checking packages", {
            "error": str(e)
        })
        # #endregion agent log
        return {}

def try_import_package(package_name, import_name=None):
    """Try importing a package."""
    if import_name is None:
        import_name = package_name.replace("-", "_")
    
    try:
        module = __import__(import_name)
        version = getattr(module, "__version__", "unknown")
        # #region agent log
        log_entry("dep-debug", "run1", "H4", "debug_dependencies.py:try_import_package", f"Successfully imported {package_name}", {
            "package": package_name,
            "import_name": import_name,
            "version": version,
            "module_path": getattr(module, "__file__", "unknown")
        })
        # #endregion agent log
        return {"success": True, "version": version}
    except ImportError as e:
        # #region agent log
        log_entry("dep-debug", "run1", "H4", "debug_dependencies.py:try_import_package", f"Failed to import {package_name}", {
            "package": package_name,
            "import_name": import_name,
            "error": str(e),
            "error_type": type(e).__name__
        })
        # #endregion agent log
        return {"success": False, "error": str(e)}
    except Exception as e:
        # #region agent log
        log_entry("dep-debug", "run1", "H4", "debug_dependencies.py:try_import_package", f"Unexpected error importing {package_name}", {
            "package": package_name,
            "error": str(e),
            "error_type": type(e).__name__
        })
        # #endregion agent log
        return {"success": False, "error": str(e)}

def check_psycopg2_issue():
    """Check psycopg2-binary installation issue."""
    try:
        # Try to see if we can install without psycopg2 first
        result = subprocess.run(
            [sys.executable, "-m", "pip", "show", "psycopg2-binary"],
            capture_output=True,
            text=True,
            timeout=10
        )
        # #region agent log
        log_entry("dep-debug", "run1", "H5", "debug_dependencies.py:check_psycopg2_issue", "Checking psycopg2-binary status", {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
            "installed": result.returncode == 0
        })
        # #endregion agent log
        
        return {
            "installed": result.returncode == 0,
            "info": result.stdout if result.returncode == 0 else result.stderr
        }
    except Exception as e:
        # #region agent log
        log_entry("dep-debug", "run1", "H5", "debug_dependencies.py:check_psycopg2_issue", "Error checking psycopg2", {
            "error": str(e)
        })
        # #endregion agent log
        return {"error": str(e)}

def main():
    """Run all diagnostic checks."""
    print("=" * 80)
    print("DEPENDENCY DIAGNOSTIC TOOL")
    print("=" * 80)
    print()
    
    # #region agent log
    log_entry("dep-debug", "run1", "H0", "debug_dependencies.py:main", "Starting dependency diagnostics", {})
    # #endregion agent log
    
    print("1. Python Information:")
    python_info = check_python_info()
    print(f"   Version: {python_info['version']}")
    print(f"   Executable: {python_info['executable']}")
    print(f"   Platform: {python_info['platform']}")
    print()
    
    print("2. Pip Information:")
    pip_info = check_pip_info()
    if "version_output" in pip_info:
        print(f"   {pip_info['version_output']}")
    else:
        print(f"   Error: {pip_info.get('error', 'Unknown')}")
    print()
    
    print("3. Installed Packages:")
    packages = check_installed_packages()
    print(f"   Total packages: {len(packages)}")
    print(f"   httpx installed: {'httpx' in packages}")
    print(f"   pydantic-settings installed: {'pydantic-settings' in packages or 'pydantic_settings' in packages}")
    print(f"   psycopg2-binary installed: {'psycopg2-binary' in packages}")
    print()
    
    print("4. Import Tests:")
    test_packages = [
        ("httpx", "httpx"),
        ("pydantic-settings", "pydantic_settings"),
        ("psycopg2-binary", "psycopg2"),
    ]
    for pkg_name, import_name in test_packages:
        result = try_import_package(pkg_name, import_name)
        status = "OK" if result["success"] else "FAIL"
        print(f"   {status} {pkg_name}: {result.get('version', result.get('error', 'unknown'))}")
    print()
    
    print("5. psycopg2-binary Status:")
    psycopg2_status = check_psycopg2_issue()
    if "installed" in psycopg2_status:
        print(f"   Installed: {psycopg2_status['installed']}")
        if not psycopg2_status['installed']:
            print(f"   Info: {psycopg2_status.get('info', 'Not found')[:200]}")
    print()
    
    print("=" * 80)
    print("Diagnostics complete. Check debug.log for detailed information.")
    print("=" * 80)

if __name__ == "__main__":
    main()

