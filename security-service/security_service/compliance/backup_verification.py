"""Backup verification service."""

import hashlib
import subprocess
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional
from pathlib import Path


class BackupVerifier:
    """Backup integrity verification and monitoring."""
    
    def __init__(self, backup_dirs: List[str] = None):
        self.backup_dirs = backup_dirs or ["/backups"]
        self.verification_results = []
        
    def verify_backup_integrity(self, backup_path: str) -> Dict[str, Any]:
        """Verify backup file integrity."""
        backup_file = Path(backup_path)
        
        if not backup_file.exists():
            return {
                "valid": False,
                "error": "Backup file not found",
                "verified_at": datetime.now(timezone.utc).isoformat()
            }
        
        # Check file size
        file_size = backup_file.stat().st_size
        if file_size == 0:
            return {
                "valid": False,
                "error": "Backup file is empty",
                "verified_at": datetime.now(timezone.utc).isoformat()
            }
        
        # Calculate checksum
        checksum = self._calculate_checksum(backup_path)
        
        # For database backups, try to verify structure
        if backup_path.endswith('.sql') or backup_path.endswith('.dump'):
            structure_valid = self._verify_database_backup_structure(backup_path)
        else:
            structure_valid = True
        
        result = {
            "valid": structure_valid and file_size > 0,
            "backup_path": backup_path,
            "file_size": file_size,
            "checksum": checksum,
            "verified_at": datetime.now(timezone.utc).isoformat()
        }
        
        if not structure_valid:
            result["error"] = "Backup structure validation failed"
        
        self.verification_results.append(result)
        return result
    
    def _calculate_checksum(self, file_path: str) -> str:
        """Calculate SHA-256 checksum of backup file."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    def _verify_database_backup_structure(self, backup_path: str) -> bool:
        """Verify database backup structure (basic check)."""
        try:
            with open(backup_path, 'r', encoding='utf-8', errors='ignore') as f:
                # Read first few lines to check for SQL structure
                first_lines = [f.readline() for _ in range(10)]
                content = " ".join(first_lines).lower()
                
                # Check for common SQL keywords
                sql_indicators = ["create", "insert", "table", "database", "postgresql"]
                return any(indicator in content for indicator in sql_indicators)
        except Exception:
            return False
    
    def test_backup_restoration(self, backup_path: str, test_db_name: str = "backup_test") -> Dict[str, Any]:
        """Test backup restoration (dry run)."""
        # This would attempt to restore to a test database
        # For safety, this is a placeholder
        return {
            "tested": False,
            "message": "Backup restoration testing requires manual intervention",
            "backup_path": backup_path,
            "tested_at": datetime.now(timezone.utc).isoformat()
        }
    
    def check_backup_schedule(self, expected_schedule: Dict[str, Any]) -> Dict[str, Any]:
        """Check if backups are being created according to schedule."""
        results = {
            "on_schedule": True,
            "missing_backups": [],
            "checked_at": datetime.now(timezone.utc).isoformat()
        }
        
        # Check each backup directory
        for backup_dir in self.backup_dirs:
            backup_path = Path(backup_dir)
            if not backup_path.exists():
                results["on_schedule"] = False
                results["missing_backups"].append(backup_dir)
                continue
            
            # Check for recent backups
            recent_backups = [
                f for f in backup_path.iterdir()
                if f.is_file() and (datetime.now() - datetime.fromtimestamp(f.stat().st_mtime)).days < 1
            ]
            
            if not recent_backups:
                results["on_schedule"] = False
                results["missing_backups"].append(backup_dir)
        
        return results
    
    def get_backup_statistics(self) -> Dict[str, Any]:
        """Get backup statistics."""
        total_size = 0
        backup_count = 0
        oldest_backup = None
        newest_backup = None
        
        for backup_dir in self.backup_dirs:
            backup_path = Path(backup_dir)
            if backup_path.exists():
                for backup_file in backup_path.iterdir():
                    if backup_file.is_file():
                        backup_count += 1
                        file_size = backup_file.stat().st_size
                        total_size += file_size
                        
                        mtime = datetime.fromtimestamp(backup_file.stat().st_mtime)
                        if oldest_backup is None or mtime < oldest_backup:
                            oldest_backup = mtime
                        if newest_backup is None or mtime > newest_backup:
                            newest_backup = mtime
        
        return {
            "total_backups": backup_count,
            "total_size_bytes": total_size,
            "total_size_gb": total_size / (1024 ** 3),
            "oldest_backup": oldest_backup.isoformat() if oldest_backup else None,
            "newest_backup": newest_backup.isoformat() if newest_backup else None
        }




