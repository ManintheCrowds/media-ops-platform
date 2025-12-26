#!/usr/bin/env python3
"""CLI entrypoint for breach checking."""

import sys
import asyncio
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.breach_monitor.main import main

if __name__ == "__main__":
    asyncio.run(main())

