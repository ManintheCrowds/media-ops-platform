"""Fixed dependency installer that handles psycopg2-binary issue."""

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
    log_entry("install-debug", "run1", "H-INSTALL", "install_dependencies_fixed.py:install_package", f"Installing {package_spec}", {
        "package": package_spec,
        "python": sys.executable
    })
    # #endregion agent log
    
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", package_spec],
            capture_output=True,
            text=True,
            timeout=300
        )
        
        # #region agent log
        log_entry("install-debug", "run1", "H-INSTALL", "install_dependencies_fixed.py:install_package", f"Install result for {package_spec}", {
            "package": package_spec,
            "returncode": result.returncode,
            "success": result.returncode == 0,
            "stdout_length": len(result.stdout),
            "stderr_length": len(result.stderr),
            "has_error": "error" in result.stderr.lower() or "error" in result.stdout.lower()
        })
        # #endregion agent log
        
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr
        }
    except Exception as e:
        # #region agent log
        log_entry("install-debug", "run1", "H-INSTALL", "install_dependencies_fixed.py:install_package", f"Exception installing {package_spec}", {
            "package": package_spec,
            "error": str(e),
            "error_type": type(e).__name__
        })
        # #endregion agent log
        return {"success": False, "error": str(e)}

def main():
    """Install dependencies with workaround for psycopg2-binary."""
    print("=" * 80)
    print("FIXED DEPENDENCY INSTALLER")
    print("=" * 80)
    print()
    print("This script installs dependencies, skipping psycopg2-binary if it fails.")
    print("psycopg2-binary can be installed separately if needed.")
    print()
    
    # #region agent log
    log_entry("install-debug", "run1", "H0", "install_dependencies_fixed.py:main", "Starting dependency installation", {
        "python": sys.executable,
        "version": sys.version
    })
    # #endregion agent log
    
    # Read requirements
    req_file = Path(__file__).parent / "requirements.txt"
    if not req_file.exists():
        print(f"ERROR: requirements.txt not found at {req_file}")
        return
    
    with open(req_file) as f:
        requirements = [line.strip() for line in f if line.strip() and not line.startswith("#")]
    
    print(f"Found {len(requirements)} requirements")
    print()
    
    # Install packages one by one, skipping psycopg2-binary if it fails
    successful = []
    failed = []
    skipped = []
    
    for req in requirements:
        package_name = req.split("==")[0].split("[")[0].strip()
        print(f"Installing {package_name}...")
        
        if "psycopg2-binary" in package_name:
            print("   (psycopg2-binary - will try but skip if fails)")
            result = install_package(req)
            if not result["success"]:
                print(f"   WARNING: Failed to install {package_name} (this is OK, can install separately)")
                print(f"      Error: {result.get('stderr', result.get('error', 'Unknown'))[:200]}")
                skipped.append(package_name)
                continue
        else:
            result = install_package(req)
            if not result["success"]:
                print(f"   FAILED: {result.get('stderr', result.get('error', 'Unknown'))[:200]}")
                failed.append(package_name)
                continue
        
        print(f"   OK: Installed {package_name}")
        successful.append(package_name)
    
    print()
    print("=" * 80)
    print("INSTALLATION SUMMARY")
    print("=" * 80)
    print(f"OK: Successful: {len(successful)}")
    print(f"FAILED: {len(failed)}")
    print(f"SKIPPED: {len(skipped)}")
    print()
    
    if failed:
        print("Failed packages:")
        for pkg in failed:
            print(f"   - {pkg}")
        print()
    
    if skipped:
        print("Skipped packages (can install separately):")
        for pkg in skipped:
            print(f"   - {pkg}")
        print("   To install psycopg2-binary separately, try:")
        print("      pip install --only-binary :all: psycopg2-binary")
        print("   Or install PostgreSQL development tools first.")
        print()
    
    # #region agent log
    log_entry("install-debug", "run1", "H-COMPLETE", "install_dependencies_fixed.py:main", "Installation complete", {
        "successful_count": len(successful),
        "failed_count": len(failed),
        "skipped_count": len(skipped),
        "successful": successful,
        "failed": failed,
        "skipped": skipped
    })
    # #endregion agent log
    
    print("Check debug.log for detailed installation logs.")

if __name__ == "__main__":
    main()

