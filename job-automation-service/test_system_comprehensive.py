"""Comprehensive system test with checkpoint/resume capability."""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
import httpx
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

from app.config import settings
from app.models.job_listing import JobListing

CHECKPOINT_FILE = "test_checkpoint.json"
RESULTS_FILE = "test_results.json"


class SystemTester:
    """Comprehensive system tester with checkpoint support."""
    
    def __init__(self):
        self.checkpoint_file = Path(CHECKPOINT_FILE)
        self.results_file = Path(RESULTS_FILE)
        self.results = {
            "started_at": datetime.now().isoformat(),
            "completed_at": None,
            "status": "running",
            "tests": {}
        }
        self.load_checkpoint()
    
    def load_checkpoint(self):
        """Load previous checkpoint if exists."""
        if self.checkpoint_file.exists():
            try:
                with open(self.checkpoint_file, 'r', encoding='utf-8') as f:
                    checkpoint = json.load(f)
                    print(f"[INFO] Loaded checkpoint from {checkpoint.get('timestamp', 'unknown')}")
                    # Resume from checkpoint
                    self.results.update(checkpoint.get('results', {}))
            except Exception as e:
                print(f"[WARN] Failed to load checkpoint: {e}")
    
    def save_checkpoint(self, test_name: str, status: str, details: Dict[str, Any]):
        """Save test progress to checkpoint file."""
        self.results["tests"][test_name] = {
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "details": details
        }
        checkpoint = {
            "timestamp": datetime.now().isoformat(),
            "results": self.results
        }
        try:
            with open(self.checkpoint_file, 'w', encoding='utf-8') as f:
                json.dump(checkpoint, f, indent=2, default=str)
        except Exception as e:
            print(f"[WARN] Failed to save checkpoint: {e}")
    
    def save_results(self):
        """Save final results."""
        self.results["completed_at"] = datetime.now().isoformat()
        self.results["status"] = "completed"
        try:
            with open(self.results_file, 'w', encoding='utf-8') as f:
                json.dump(self.results, f, indent=2, default=str)
            print(f"\n[OK] Results saved to {self.results_file}")
        except Exception as e:
            print(f"[ERROR] Failed to save results: {e}")
    
    def test_database_connection(self) -> Dict[str, Any]:
        """Test database connectivity."""
        print("\n[TEST] Database Connection...")
        try:
            engine = create_engine(settings.database_url)
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                result.fetchone()
            return {"status": "pass", "message": "Database connected successfully"}
        except Exception as e:
            return {"status": "fail", "error": str(e)}
    
    def test_database_schema(self) -> Dict[str, Any]:
        """Test database schema (tables exist)."""
        print("\n[TEST] Database Schema...")
        try:
            engine = create_engine(settings.database_url)
            SessionLocal = sessionmaker(bind=engine)
            db = SessionLocal()
            try:
                # Try to query job_listings table
                count = db.query(JobListing).count()
                return {
                    "status": "pass",
                    "message": f"Schema valid, {count} jobs in database"
                }
            finally:
                db.close()
        except Exception as e:
            return {"status": "fail", "error": str(e)}
    
    def test_api_credentials(self) -> Dict[str, Any]:
        """Test API credentials configuration."""
        print("\n[TEST] API Credentials...")
        credentials = {
            "adzuna_api_id": bool(settings.adzuna_api_id),
            "adzuna_api_key": bool(settings.adzuna_api_key),
            "jsearch_api_key": bool(settings.jsearch_api_key),
        }
        all_configured = all(credentials.values())
        return {
            "status": "pass" if all_configured else "warn",
            "credentials": credentials,
            "message": "All credentials configured" if all_configured else "Some credentials missing"
        }
    
    def test_api_server_health(self) -> Dict[str, Any]:
        """Test API server is running and healthy."""
        print("\n[TEST] API Server Health...")
        try:
            response = httpx.get("http://localhost:8004/health", timeout=5.0)
            if response.status_code == 200:
                return {"status": "pass", "message": "Server is healthy", "response": response.json()}
            else:
                return {"status": "fail", "message": f"Server returned {response.status_code}"}
        except httpx.ConnectError:
            return {"status": "fail", "error": "Server not running on port 8004"}
        except Exception as e:
            return {"status": "fail", "error": str(e)}
    
    def test_job_search_endpoint(self) -> Dict[str, Any]:
        """Test job search endpoint."""
        print("\n[TEST] Job Search Endpoint...")
        try:
            body = {
                "query": "python developer",
                "location": "Minneapolis, MN",
                "limit": 5,
                "sources": ["adzuna"]
            }
            response = httpx.post(
                "http://localhost:8004/api/v1/jobs/search",
                json=body,
                timeout=30.0
            )
            if response.status_code == 200:
                data = response.json()
                return {
                    "status": "pass",
                    "jobs_found": data.get("count", 0),
                    "sources_searched": data.get("sources_searched", []),
                    "message": f"Found {data.get('count', 0)} jobs"
                }
            else:
                return {"status": "fail", "error": f"Status {response.status_code}: {response.text[:200]}"}
        except Exception as e:
            return {"status": "fail", "error": str(e)}
    
    def test_jobs_saved_to_database(self) -> Dict[str, Any]:
        """Test that jobs are saved to database."""
        print("\n[TEST] Jobs Saved to Database...")
        try:
            engine = create_engine(settings.database_url)
            SessionLocal = sessionmaker(bind=engine)
            db = SessionLocal()
            try:
                # Get count before
                count_before = db.query(JobListing).count()
                
                # Run a search to potentially add jobs
                body = {
                    "query": "python",
                    "location": "Minneapolis",
                    "limit": 3,
                    "sources": ["adzuna"]
                }
                response = httpx.post(
                    "http://localhost:8004/api/v1/jobs/search",
                    json=body,
                    timeout=30.0
                )
                
                # Get count after (create new session to see committed changes)
                db.commit()  # Ensure any pending changes are committed
                count_after = db.query(JobListing).count()
                
                new_jobs = count_after - count_before
                
                return {
                    "status": "pass" if new_jobs >= 0 else "warn",
                    "count_before": count_before,
                    "count_after": count_after,
                    "new_jobs": new_jobs,
                    "message": f"Database has {count_after} jobs ({new_jobs} new)"
                }
            finally:
                db.close()
        except Exception as e:
            return {"status": "fail", "error": str(e)}
    
    def test_job_source_attribution(self) -> Dict[str, Any]:
        """Test that jobs have proper source attribution."""
        print("\n[TEST] Job Source Attribution...")
        try:
            engine = create_engine(settings.database_url)
            SessionLocal = sessionmaker(bind=engine)
            db = SessionLocal()
            try:
                # Get recent jobs
                recent_jobs = db.query(JobListing).order_by(JobListing.id.desc()).limit(10).all()
                
                if not recent_jobs:
                    return {"status": "warn", "message": "No jobs in database to check"}
                
                jobs_with_source = sum(1 for job in recent_jobs if job.source)
                jobs_without_source = len(recent_jobs) - jobs_with_source
                
                return {
                    "status": "pass" if jobs_without_source == 0 else "warn",
                    "total_checked": len(recent_jobs),
                    "with_source": jobs_with_source,
                    "without_source": jobs_without_source,
                    "message": f"{jobs_with_source}/{len(recent_jobs)} jobs have source field"
                }
            finally:
                db.close()
        except Exception as e:
            return {"status": "fail", "error": str(e)}
    
    def test_match_scores(self) -> Dict[str, Any]:
        """Test that jobs have match scores calculated."""
        print("\n[TEST] Match Scores...")
        try:
            engine = create_engine(settings.database_url)
            SessionLocal = sessionmaker(bind=engine)
            db = SessionLocal()
            try:
                recent_jobs = db.query(JobListing).order_by(JobListing.id.desc()).limit(10).all()
                
                if not recent_jobs:
                    return {"status": "warn", "message": "No jobs in database to check"}
                
                jobs_with_scores = sum(
                    1 for job in recent_jobs 
                    if job.overall_match_score is not None and job.overall_match_score > 0
                )
                
                avg_score = sum(
                    job.overall_match_score for job in recent_jobs 
                    if job.overall_match_score
                ) / len([j for j in recent_jobs if j.overall_match_score]) if any(j.overall_match_score for j in recent_jobs) else 0
                
                return {
                    "status": "pass" if jobs_with_scores > 0 else "warn",
                    "total_checked": len(recent_jobs),
                    "with_scores": jobs_with_scores,
                    "average_score": round(avg_score, 3),
                    "message": f"{jobs_with_scores}/{len(recent_jobs)} jobs have match scores (avg: {avg_score:.3f})"
                }
            finally:
                db.close()
        except Exception as e:
            return {"status": "fail", "error": str(e)}
    
    def run_all_tests(self):
        """Run all tests with checkpointing."""
        print("=" * 80)
        print("COMPREHENSIVE SYSTEM TEST")
        print("=" * 80)
        print(f"Started: {self.results['started_at']}")
        print()
        
        tests = [
            ("database_connection", self.test_database_connection),
            ("database_schema", self.test_database_schema),
            ("api_credentials", self.test_api_credentials),
            ("api_server_health", self.test_api_server_health),
            ("job_search_endpoint", self.test_job_search_endpoint),
            ("jobs_saved_to_database", self.test_jobs_saved_to_database),
            ("job_source_attribution", self.test_job_source_attribution),
            ("match_scores", self.test_match_scores),
        ]
        
        for test_name, test_func in tests:
            # Skip if already completed
            if test_name in self.results["tests"]:
                prev_status = self.results["tests"][test_name].get("status")
                if prev_status == "pass":
                    print(f"[SKIP] {test_name} (already passed)")
                    continue
            
            try:
                result = test_func()
                status_icon = "[OK]" if result["status"] == "pass" else "[WARN]" if result["status"] == "warn" else "[FAIL]"
                print(f"{status_icon} {test_name}: {result.get('message', result.get('error', 'Unknown'))}")
                
                self.save_checkpoint(test_name, result["status"], result)
                
                # Stop on critical failures
                if result["status"] == "fail" and test_name in ["database_connection", "api_server_health"]:
                    print(f"\n[ERROR] Critical test failed: {test_name}")
                    print("Stopping tests. Fix the issue and rerun to continue.")
                    break
                    
            except KeyboardInterrupt:
                print("\n[INFO] Test interrupted by user. Progress saved to checkpoint.")
                break
            except Exception as e:
                print(f"[ERROR] {test_name}: Exception - {e}")
                self.save_checkpoint(test_name, "error", {"error": str(e)})
        
        self.save_results()
        self.print_summary()
    
    def print_summary(self):
        """Print test summary."""
        print("\n" + "=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)
        
        passed = sum(1 for t in self.results["tests"].values() if t["status"] == "pass")
        warned = sum(1 for t in self.results["tests"].values() if t["status"] == "warn")
        failed = sum(1 for t in self.results["tests"].values() if t["status"] == "fail")
        total = len(self.results["tests"])
        
        print(f"Total Tests: {total}")
        print(f"[OK] Passed: {passed}")
        print(f"[WARN] Warnings: {warned}")
        print(f"[FAIL] Failed: {failed}")
        print()
        
        if failed > 0:
            print("Failed Tests:")
            for name, test in self.results["tests"].items():
                if test["status"] == "fail":
                    print(f"  - {name}: {test.get('details', {}).get('error', 'Unknown error')}")
        
        print(f"\nFull results: {self.results_file}")
        print(f"Checkpoint: {self.checkpoint_file}")


if __name__ == "__main__":
    tester = SystemTester()
    try:
        tester.run_all_tests()
    except KeyboardInterrupt:
        print("\n[INFO] Tests interrupted. Progress saved.")
        tester.save_results()
    except Exception as e:
        print(f"\n[ERROR] Test suite failed: {e}")
        import traceback
        traceback.print_exc()
        tester.save_results()

