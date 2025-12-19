#!/usr/bin/env python3
"""Script to register default services in the platform."""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models import Service, Base
from app.config import settings
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Default services to register
DEFAULT_SERVICES = [
    {
        "name": "seafile",
        "service_type": "file_storage",
        "base_url": "http://seafile:80",
        "api_url": "http://seafile:80/api2",
        "health_check_url": "http://seafile:80/api2/ping/",
        "requires_auth": True,
        "is_active": True
    },
    {
        "name": "jellyfin",
        "service_type": "media_server",
        "base_url": "http://jellyfin:8096",
        "api_url": "http://jellyfin:8096",
        "health_check_url": "http://jellyfin:8096/health",
        "requires_auth": True,
        "is_active": True
    },
    {
        "name": "gitea",
        "service_type": "dev_tools",
        "base_url": "http://gitea:3000",
        "api_url": "http://gitea:3000/api/v1",
        "health_check_url": "http://gitea:3000/api/v1/version",
        "requires_auth": True,
        "is_active": True
    },
    {
        "name": "prometheus",
        "service_type": "monitoring",
        "base_url": "http://prometheus:9090",
        "api_url": "http://prometheus:9090/api/v1",
        "health_check_url": "http://prometheus:9090/-/healthy",
        "requires_auth": False,
        "is_active": True
    },
    {
        "name": "grafana",
        "service_type": "monitoring",
        "base_url": "http://grafana:3000",
        "api_url": "http://grafana:3000/api",
        "health_check_url": "http://grafana:3000/api/health",
        "requires_auth": True,
        "is_active": True
    },
    {
        "name": "vaultwarden",
        "service_type": "security",
        "base_url": "http://vaultwarden:80",
        "api_url": "http://vaultwarden:80",
        "health_check_url": "http://vaultwarden:80/",
        "requires_auth": True,
        "is_active": True
    },
    {
        "name": "bookstack",
        "service_type": "productivity",
        "base_url": "http://bookstack:80",
        "api_url": "http://bookstack:80/api",
        "health_check_url": "http://bookstack:80/",
        "requires_auth": True,
        "is_active": True
    }
]


def register_services():
    """Register default services in the database."""
    engine = create_engine(settings.database_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    db = SessionLocal()
    
    try:
        registered = 0
        skipped = 0
        
        for service_data in DEFAULT_SERVICES:
            # Check if service already exists
            existing = db.query(Service).filter(Service.name == service_data["name"]).first()
            
            if existing:
                print(f"Service '{service_data['name']}' already exists, skipping...")
                skipped += 1
                continue
            
            # Create new service
            service = Service(**service_data)
            db.add(service)
            registered += 1
            print(f"Registered service: {service_data['name']} ({service_data['service_type']})")
        
        db.commit()
        print(f"\n✅ Successfully registered {registered} services")
        if skipped > 0:
            print(f"⏭️  Skipped {skipped} existing services")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error registering services: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        db.close()
    
    return 0


if __name__ == "__main__":
    sys.exit(register_services())

