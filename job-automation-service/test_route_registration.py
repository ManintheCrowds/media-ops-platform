#!/usr/bin/env python3
"""Diagnostic script to check route registration."""
from app.main import app

scheduler_routes = [r for r in app.routes if hasattr(r, 'path') and 'scheduler' in r.path]
print(f"Found {len(scheduler_routes)} scheduler routes:")
for route in scheduler_routes:
    methods = list(route.methods) if hasattr(route, 'methods') else []
    print(f"  {route.path} - {methods}")

# Specifically check for start/stop
start_stop = [r for r in scheduler_routes if 'start' in r.path or 'stop' in r.path]
print(f"\nStart/Stop routes: {len(start_stop)}")
for route in start_stop:
    methods = list(route.methods) if hasattr(route, 'methods') else []
    print(f"  {route.path} - {methods}")

# Verify imports work
try:
    from app.api import scheduler
    print(f"\n[OK] Scheduler module imported successfully")
    print(f"[OK] Router has {len(scheduler.router.routes)} routes")
except Exception as e:
    print(f"\n[ERROR] Error importing scheduler: {e}")

