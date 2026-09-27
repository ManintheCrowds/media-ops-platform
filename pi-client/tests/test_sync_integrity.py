"""Integrity gate: checksum mismatch must fail closed before extract."""

from __future__ import annotations

import asyncio
import hashlib
import io
import tarfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from pi_client.cache.sync import SyncManager


def _make_manager(tmp_path: Path) -> SyncManager:
    config = MagicMock()
    config.sync_interval = 60
    config.device.device_id = "pi-1"
    manager = SyncManager.__new__(SyncManager)
    manager.config = config
    manager.cache_manager = MagicMock()
    manager.cache_manager.storage.cache_dir = tmp_path
    manager.running = False
    manager._sync_task = None
    manager._last_sync = None
    return manager


def _write_tar_gz(path: Path, member_name: str, payload: bytes) -> None:
    with tarfile.open(path, "w:gz") as tar:
        info = tarfile.TarInfo(name=member_name)
        info.size = len(payload)
        tar.addfile(info, io.BytesIO(payload))


def test_checksum_mismatch_skips_extract(tmp_path):
    manager = _make_manager(tmp_path)
    package = tmp_path / "pkg.tar.gz"
    _write_tar_gz(package, "content_1/metadata.json", b'{"ok": true}')

    client = MagicMock()
    client.download_package = AsyncMock(return_value=str(package))
    client._request = AsyncMock()

    with patch.object(
        manager, "_extract_package", new_callable=AsyncMock
    ) as extract:
        asyncio.run(
            manager._process_package(
                client,
                {
                    "id": 42,
                    "package_type": "full",
                    "checksum": "0" * 64,
                },
            )
        )
        extract.assert_not_called()
        client._request.assert_not_called()


def test_matching_checksum_extracts(tmp_path):
    manager = _make_manager(tmp_path)
    package = tmp_path / "pkg.tar.gz"
    payload = b'{"ok": true}'
    _write_tar_gz(package, "content_1/metadata.json", payload)

    digest = hashlib.sha256(package.read_bytes()).hexdigest()
    client = MagicMock()
    client.download_package = AsyncMock(return_value=str(package))
    client._request = AsyncMock()

    with patch.object(
        manager, "_extract_package", new_callable=AsyncMock
    ) as extract:
        asyncio.run(
            manager._process_package(
                client,
                {
                    "id": 7,
                    "package_type": "full",
                    "checksum": digest,
                },
            )
        )
        extract.assert_awaited_once()
        client._request.assert_awaited()


def test_verify_checksum_helper(tmp_path):
    manager = _make_manager(tmp_path)
    path = tmp_path / "blob.bin"
    data = b"abc123"
    path.write_bytes(data)
    good = hashlib.sha256(data).hexdigest()
    assert manager._verify_checksum(str(path), good) is True
    assert manager._verify_checksum(str(path), "deadbeef") is False
