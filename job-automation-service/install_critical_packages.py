"""Install critical packages first, skipping problematic ones."""

import sys
import subprocess
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

def install_package(package_spec):
    """Install a single package."""
    # #region agent log
    log_entry("install-critical", "run1", "H-INSTALL", "install_critical_packages.py:install_package", f"Installing {package_spec}", {
        "package": package_spec
    })
    # #endregion agent log
    
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", package_spec, "--quiet"],
            capture_output=True,
            text=True,
            timeout=120
        )
        
        success = result.returncode == 0
        # #region agent log
        log_entry("install-critical", "run1", "H-INSTALL", "install_critical_packages.py:install_package", f"Install result for {package_spec}", {
            "package": package_spec,
            "success": success,
            "returncode": result.returncode,
            "has_error": "error" in result.stderr.lower() if result.stderr else False
        })
        # #endregion agent log
        
        return {"success": success, "stdout": result.stdout, "stderr": result.stderr}
    except Exception as e:
        # #region agent log
        log_entry("install-critical", "run1", "H-INSTALL", "install_critical_packages.py:install_package", f"Exception installing {package_spec}", {
            "package": package_spec,
            "error": str(e)
        })
        # #endregion agent log
        return {"success": False, "error": str(e)}

def main():
    """Install critical packages needed for scripts to run."""
    print("=" * 80)
    print("INSTALLING CRITICAL PACKAGES")
    print("=" * 80)
    print()
    print("Installing packages needed for test scripts to run...")
    print("(Skipping psycopg2-binary - will handle separately)")
    print()
    
    # #region agent log
    log_entry("install-critical", "run1", "H0", "install_critical_packages.py:main", "Starting critical package installation", {})
    # #endregion agent log
    
    # Critical packages needed for scripts (in dependency order)
    critical_packages = [
        "httpx==0.25.2",
        "pydantic==2.5.0",
        "pydantic-settings==2.1.0",
        "fastapi==0.104.1",
        "uvicorn[standard]==0.24.0",
        "python-multipart==0.0.6",
        "sqlalchemy==2.0.23",
        "alembic==1.12.1",
    ]
    
    successful = []
    failed = []
    
    for pkg in critical_packages:
        pkg_name = pkg.split("==")[0].split("[")[0].strip()
        print(f"Installing {pkg_name}...", end=" ", flush=True)
        
        result = install_package(pkg)
        if result["success"]:
            print("OK")
            successful.append(pkg_name)
        else:
            error_msg = result.get("stderr", result.get("error", "Unknown error"))[:100]
            print(f"FAILED: {error_msg}")
            failed.append(pkg_name)
    
    print()
    print("=" * 80)
    print("INSTALLATION SUMMARY")
    print("=" * 80)
    print(f"Successful: {len(successful)}/{len(critical_packages)}")
    if failed:
        print(f"Failed: {len(failed)}")
        for pkg in failed:
            print(f"  - {pkg}")
    print()
    
    # #region agent log
    log_entry("install-critical", "run1", "H-COMPLETE", "install_critical_packages.py:main", "Critical installation complete", {
        "successful": successful,
        "failed": failed
    })
    # #endregion agent log
    
    if len(successful) >= 6:  # At least httpx, pydantic, pydantic-settings, fastapi, uvicorn, sqlalchemy
        print("Critical packages installed! You can now run the test scripts.")
        print()
        print("Note: psycopg2-binary can be installed separately if needed:")
        print("  pip install --only-binary :all: psycopg2-binary")
    else:
        print("WARNING: Some critical packages failed to install.")
        print("Check the errors above and try installing manually.")

if __name__ == "__main__":
    main()
