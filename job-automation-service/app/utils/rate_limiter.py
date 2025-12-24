"""Rate limiting utilities for web scrapers."""

import asyncio
import random
import time
from datetime import datetime
from typing import Optional
from app.config import settings


class RateLimiter:
    """Rate limiter with configurable delays and human-like behavior."""
    
    def __init__(
        self,
        min_delay: Optional[float] = None,
        max_delay: Optional[float] = None
    ):
        """Initialize rate limiter.
        
        Args:
            min_delay: Minimum delay in seconds (defaults to config)
            max_delay: Maximum delay in seconds (defaults to config)
        """
        self.min_delay = min_delay or settings.scraper_delay_min
        self.max_delay = max_delay or settings.scraper_delay_max
        self.last_request_time = 0.0
        self.use_human_delays = getattr(settings, 'use_human_delays', True)
    
    def _get_time_based_multiplier(self) -> float:
        """Get delay multiplier based on time of day.
        
        Returns:
            Multiplier (0.8-1.5) based on time of day
        """
        if not self.use_human_delays:
            return 1.0
        
        hour = datetime.now().hour
        
        # Business hours (9 AM - 5 PM): faster (0.8x)
        if 9 <= hour < 17:
            return 0.8
        # Evening (5 PM - 10 PM): normal (1.0x)
        elif 17 <= hour < 22:
            return 1.0
        # Night (10 PM - 6 AM): slower (1.3x)
        elif 22 <= hour or hour < 6:
            return 1.3
        # Early morning (6 AM - 9 AM): slightly slower (1.1x)
        else:
            return 1.1
    
    def _calculate_human_delay(self) -> float:
        """Calculate human-like delay with variations.
        
        Returns:
            Delay in seconds
        """
        base_delay = random.uniform(self.min_delay, self.max_delay)
        
        if not self.use_human_delays:
            return base_delay
        
        # Apply time-based multiplier
        multiplier = self._get_time_based_multiplier()
        
        # Add small random jitter (±10%)
        jitter = random.uniform(-0.1, 0.1)
        
        # Sometimes add longer pauses (simulating reading/thinking)
        if random.random() < 0.15:  # 15% chance
            extra_pause = random.uniform(2.0, 5.0)
            base_delay += extra_pause
        
        return base_delay * multiplier * (1 + jitter)
    
    async def wait(self):
        """Wait for the appropriate delay before next request."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        # Calculate delay (human-like if enabled)
        if self.use_human_delays:
            delay = self._calculate_human_delay()
        else:
            delay = random.uniform(self.min_delay, self.max_delay)
        
        # If enough time has passed, no need to wait
        if time_since_last < delay:
            wait_time = delay - time_since_last
            await asyncio.sleep(wait_time)
        
        self.last_request_time = time.time()
    
    async def exponential_backoff(self, attempt: int, base_delay: float = 2.0) -> float:
        """Calculate exponential backoff delay.
        
        Args:
            attempt: Current attempt number (0-indexed)
            base_delay: Base delay in seconds
        
        Returns:
            Delay in seconds
        """
        delay = base_delay * (2 ** attempt)
        # Add jitter to avoid thundering herd
        jitter = random.uniform(0.5, 1.5)
        return delay * jitter

