#!/usr/bin/env python3
"""Test script to verify all services are accessible and working."""

import sys
import os
import asyncio
import httpx

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models import Service
from app.config import settings
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

async def test_service(service: Service):
    """Test if a service is accessible."""
    health_url = service.health_check_url or f"{service.base_url}/health"
    
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(health_url)
            return {
                "name": service.name,
                "status": "healthy" if response.status_code == 200 else "unhealthy",
                "status_code": response.status_code,
                "response_time_ms": response.elapsed.total_seconds() * 1000
            }
    except Exception as e:
        return {
            "name": service.name,
            "status": "unhealthy",
            "error": str(e)
        }

async def test_all_services():
    """Test all registered services."""
    engine = create_engine(settings.database_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    db = SessionLocal()
    
    try:
        services = db.query(Service).filter(Service.is_active == True).all()
        
        if not services:
            print("No services registered.")
            return
        
        print(f"Testing {len(services)} services...\n")
        
        tasks = [test_service(service) for service in services]
        results = await asyncio.gather(*tasks)
        
        print("Service Health Status:")
        print("=" * 60)
        
        for result in results:
            status_icon = "✅" if result["status"] == "healthy" else "❌"
            print(f"{status_icon} {result['name']:20s} - {result['status']:10s}", end="")
            
            if "status_code" in result:
                print(f" (HTTP {result['status_code']})", end="")
            if "response_time_ms" in result:
                print(f" - {result['response_time_ms']:.2f}ms", end="")
            if "error" in result:
                print(f" - Error: {result['error']}", end="")
            print()
        
        healthy = sum(1 for r in results if r["status"] == "healthy")
        print(f"\nSummary: {healthy}/{len(results)} services healthy")
        
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test_all_services())

