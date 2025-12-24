"""Performance benchmark agent for load testing and metrics."""

import asyncio
import logging
import httpx
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.agent_task import AgentTask

logger = logging.getLogger(__name__)


async def performance_benchmark_agent(task: AgentTask) -> Dict[str, Any]:
    """Benchmark performance metrics.
    
    Args:
        task: Agent task
        
    Returns:
        Dictionary with performance metrics
    """
    results = {
        "baseline_metrics": {},
        "load_test_results": {},
        "concurrent_test_results": {},
        "database_performance": {},
        "recommendations": []
    }
    
    base_url = "http://localhost:8004"
    
    # Baseline metrics - single request
    async with httpx.AsyncClient(timeout=30.0) as client:
        baseline_endpoints = [
            "/health",
            "/api/v1/jobs/recommended?min_score=0.7&limit=10",
            "/api/v1/matching/stats",
        ]
        
        for endpoint in baseline_endpoints:
            times = []
            for _ in range(3):  # 3 requests for baseline
                try:
                    start = asyncio.get_event_loop().time()
                    response = await client.get(f"{base_url}{endpoint}")
                    elapsed = asyncio.get_event_loop().time() - start
                    
                    if response.status_code == 200:
                        times.append(elapsed)
                except Exception as e:
                    logger.warning(f"Baseline test failed for {endpoint}: {e}")
            
            if times:
                results["baseline_metrics"][endpoint] = {
                    "avg_ms": sum(times) / len(times) * 1000,
                    "min_ms": min(times) * 1000,
                    "max_ms": max(times) * 1000,
                    "requests": len(times)
                }
        
        # Load test - multiple sequential requests
        load_endpoint = "/api/v1/jobs/recommended?min_score=0.7&limit=10"
        load_times = []
        
        for i in range(10):  # 10 sequential requests
            try:
                start = asyncio.get_event_loop().time()
                response = await client.get(f"{base_url}{load_endpoint}")
                elapsed = asyncio.get_event_loop().time() - start
                
                if response.status_code == 200:
                    load_times.append(elapsed)
            except Exception as e:
                logger.warning(f"Load test request {i+1} failed: {e}")
        
        if load_times:
            results["load_test_results"] = {
                "endpoint": load_endpoint,
                "total_requests": 10,
                "successful_requests": len(load_times),
                "avg_ms": sum(load_times) / len(load_times) * 1000,
                "min_ms": min(load_times) * 1000,
                "max_ms": max(load_times) * 1000,
                "total_time_ms": sum(load_times) * 1000
            }
        
        # Concurrent test - parallel requests
        concurrent_endpoint = "/api/v1/matching/stats"
        concurrent_tasks = []
        
        async def make_request():
            try:
                start = asyncio.get_event_loop().time()
                response = await client.get(f"{base_url}{concurrent_endpoint}")
                elapsed = asyncio.get_event_loop().time() - start
                return {"success": response.status_code == 200, "time": elapsed}
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        # Create 5 concurrent requests
        concurrent_tasks = [make_request() for _ in range(5)]
        concurrent_results = await asyncio.gather(*concurrent_tasks)
        
        successful = [r for r in concurrent_results if r.get("success")]
        if successful:
            concurrent_times = [r["time"] for r in successful]
            results["concurrent_test_results"] = {
                "endpoint": concurrent_endpoint,
                "concurrent_requests": 5,
                "successful": len(successful),
                "avg_ms": sum(concurrent_times) / len(concurrent_times) * 1000,
                "min_ms": min(concurrent_times) * 1000,
                "max_ms": max(concurrent_times) * 1000
            }
    
    # Database performance
    db = SessionLocal()
    try:
        import time
        
        # Test query performance
        start = time.time()
        job_count = db.query(JobListing).count()
        query_time = (time.time() - start) * 1000
        
        results["database_performance"] = {
            "query_time_ms": query_time,
            "job_count": job_count,
            "performance": "good" if query_time < 100 else "slow" if query_time < 500 else "poor"
        }
        
        if query_time > 100:
            results["recommendations"].append({
                "type": "database",
                "issue": f"Slow query performance: {query_time:.2f}ms",
                "suggestion": "Consider adding indexes or optimizing queries"
            })
    except Exception as e:
        logger.error(f"Database performance test failed: {e}")
        results["database_performance"]["error"] = str(e)
    finally:
        db.close()
    
    # Generate recommendations
    for endpoint, metrics in results["baseline_metrics"].items():
        if metrics["avg_ms"] > 1000:  # > 1 second
            results["recommendations"].append({
                "type": "performance",
                "endpoint": endpoint,
                "issue": f"Slow response time: {metrics['avg_ms']:.2f}ms",
                "suggestion": "Consider caching or optimization",
                "priority": "high"
            })
        elif metrics["avg_ms"] > 500:  # > 500ms
            results["recommendations"].append({
                "type": "performance",
                "endpoint": endpoint,
                "issue": f"Moderate response time: {metrics['avg_ms']:.2f}ms",
                "suggestion": "Monitor and optimize if needed",
                "priority": "medium"
            })
    
    return results

