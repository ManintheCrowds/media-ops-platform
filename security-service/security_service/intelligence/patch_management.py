"""Patch management service."""

import subprocess
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from ..models.threats import PatchStatus


class PatchManager:
    """Security patch detection and management."""
    
    def __init__(self, db: Session):
        self.db = db
        
    def check_system_patches(self) -> List[PatchStatus]:
        """Check for available system patches."""
        patches = []
        
        try:
            # Check for apt updates (Debian/Ubuntu)
            result = subprocess.run(
                ["apt", "list", "--upgradable"],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                lines = result.stdout.strip().split("\n")[1:]  # Skip header
                for line in lines:
                    if line:
                        parts = line.split()
                        if len(parts) >= 2:
                            package_name = parts[0].split("/")[0]
                            current_version = parts[1]
                            available_version = parts[2] if len(parts) > 2 else current_version
                            
                            # Check if it's a security update
                            is_security = self._is_security_patch(package_name)
                            
                            patch = PatchStatus(
                                patch_type="system",
                                component_name=package_name,
                                current_version=current_version,
                                available_version=available_version,
                                is_security_patch="true" if is_security else "false",
                                patch_available="true",
                                last_checked=datetime.utcnow(),
                                status="update_available"
                            )
                            
                            # Check if already exists
                            existing = self.db.query(PatchStatus).filter(
                                PatchStatus.component_name == package_name,
                                PatchStatus.patch_type == "system"
                            ).first()
                            
                            if existing:
                                existing.available_version = available_version
                                existing.patch_available = "true"
                                existing.is_security_patch = "true" if is_security else "false"
                                existing.last_checked = datetime.utcnow()
                                existing.status = "update_available"
                                patches.append(existing)
                            else:
                                self.db.add(patch)
                                patches.append(patch)
        except FileNotFoundError:
            print("apt not available (not a Debian/Ubuntu system)")
        except Exception as e:
            print(f"System patch check failed: {e}")
        
        self.db.commit()
        return patches
    
    def _is_security_patch(self, package_name: str) -> bool:
        """Determine if patch is a security update."""
        # This would check package metadata or security advisories
        # For now, assume all updates could be security-related
        security_keywords = ["security", "cve", "vulnerability", "exploit"]
        package_lower = package_name.lower()
        return any(keyword in package_lower for keyword in security_keywords)
    
    def check_python_packages(self) -> List[PatchStatus]:
        """Check for Python package updates."""
        patches = []
        
        try:
            result = subprocess.run(
                ["pip", "list", "--outdated", "--format", "json"],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                for package in data:
                    patch = PatchStatus(
                        patch_type="python",
                        component_name=package["name"],
                        current_version=package["version"],
                        available_version=package.get("latest_version", package["version"]),
                        is_security_patch="false",  # Would need to check against CVE database
                        patch_available="true",
                        last_checked=datetime.utcnow(),
                        status="update_available"
                    )
                    
                    # Check if already exists
                    existing = self.db.query(PatchStatus).filter(
                        PatchStatus.component_name == package["name"],
                        PatchStatus.patch_type == "python"
                    ).first()
                    
                    if existing:
                        existing.available_version = package.get("latest_version", package["version"])
                        existing.patch_available = "true"
                        existing.last_checked = datetime.utcnow()
                        patches.append(existing)
                    else:
                        self.db.add(patch)
                        patches.append(patch)
        except Exception as e:
            print(f"Python package check failed: {e}")
        
        self.db.commit()
        return patches
    
    def get_security_patches(self) -> List[PatchStatus]:
        """Get all available security patches."""
        return self.db.query(PatchStatus).filter(
            PatchStatus.is_security_patch == "true",
            PatchStatus.patch_available == "true"
        ).all()
    
    def mark_patch_applied(self, patch_id: int, applied_by: str):
        """Mark patch as applied."""
        patch = self.db.query(PatchStatus).filter(PatchStatus.id == patch_id).first()
        if patch:
            patch.status = "update_applied"
            patch.last_applied = datetime.utcnow()
            patch.applied_by = applied_by
            patch.current_version = patch.available_version
            patch.patch_available = "false"
            self.db.commit()
