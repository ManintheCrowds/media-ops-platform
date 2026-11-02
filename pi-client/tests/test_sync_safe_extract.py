"""Safe tar extraction tests for Pi sync manager."""

import asyncio
import io
import tarfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from pi_client.cache.sync import SyncManager


def _make_manager(tmp_path: Path) -> SyncManager:
    config = MagicMock()
    config.sync_interval = 60
    manager = SyncManager.__new__(SyncManager)
    manager.config = config
    manager.cache_manager = MagicMock()
    manager.cache_manager.storage.cache_dir = tmp_path
    manager.running = False
    manager._sync_task = None
    manager._last_sync = None
    return manager


def test_rejects_path_traversal(tmp_path):
    manager = _make_manager(tmp_path)
    evil = tmp_path / "evil.tar.gz"
    with tarfile.open(evil, "w:gz") as tar:
        info = tarfile.TarInfo(name="../escape.txt")
        data = b"nope"
        info.size = len(data)
        tar.addfile(info, io.BytesIO(data))

    with pytest.raises(ValueError, match="Unsafe tar member"):
        asyncio.run(manager._extract_package(str(evil), 99))


def test_safe_member_helper(tmp_path):
    extract = tmp_path / "extract"
    extract.mkdir()
    good = tarfile.TarInfo(name="content_1/metadata.json")
    assert SyncManager._is_safe_tar_member(good, extract) is True
    bad = tarfile.TarInfo(name="../etc/passwd")
    assert SyncManager._is_safe_tar_member(bad, extract) is False
    abs_path = tarfile.TarInfo(name="/etc/passwd")
    assert SyncManager._is_safe_tar_member(abs_path, extract) is False
