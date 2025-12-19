"""Tests for cache management."""

import pytest
import tempfile
import shutil
from pathlib import Path
from pi_client.cache.manager import CacheManager
from pi_client.cache.storage import CacheStorage
from pi_client.config import Config


@pytest.fixture
def temp_cache_dir():
    """Create temporary cache directory."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def config(temp_cache_dir):
    """Create test configuration."""
    config = Config()
    config.cache.directory = temp_cache_dir
    config.cache.max_size_mb = 100
    return config


def test_cache_storage_save_load(temp_cache_dir):
    """Test saving and loading metadata."""
    storage = CacheStorage(temp_cache_dir)
    
    metadata = {"id": 1, "title": "Test Content"}
    storage.save_metadata(1, metadata)
    
    loaded = storage.load_metadata(1)
    assert loaded is not None
    assert loaded["id"] == 1
    assert loaded["title"] == "Test Content"


def test_cache_manager_get_content(config):
    """Test getting cached content."""
    manager = CacheManager(config)
    
    # Cache content
    metadata = {"id": 1, "title": "Test"}
    manager.cache_content(1, metadata)
    
    # Retrieve content
    cached = manager.get_content(1)
    assert cached is not None
    assert cached["id"] == 1


def test_cache_manager_invalidate(config):
    """Test invalidating cached content."""
    manager = CacheManager(config)
    
    # Cache content
    metadata = {"id": 1, "title": "Test"}
    manager.cache_content(1, metadata)
    
    # Invalidate
    manager.invalidate_content(1)
    
    # Should not be in cache
    cached = manager.get_content(1)
    assert cached is None

