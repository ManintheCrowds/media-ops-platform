#!/usr/bin/env python3
"""Migration script to encrypt existing plain-text service authentication tokens."""

import sys
import os
import argparse

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models import Service
from app.config import settings
from app.auth.encryption import encrypt_token, is_encrypted, EncryptionError
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def migrate_tokens(dry_run: bool = False):
    """
    Migrate plain-text tokens to encrypted format.
    
    Args:
        dry_run: If True, only report what would be changed without making changes
    """
    engine = create_engine(settings.database_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    db = SessionLocal()
    
    try:
        # Query all services with non-null auth_token
        services = db.query(Service).filter(Service._auth_token_encrypted.isnot(None)).all()
        
        if not services:
            print("No services with auth tokens found.")
            return 0
        
        print(f"Found {len(services)} service(s) with auth tokens")
        print("-" * 60)
        
        migrated = 0
        already_encrypted = 0
        errors = 0
        
        for service in services:
            token_value = service._auth_token_encrypted
            
            # Check if already encrypted
            if is_encrypted(token_value):
                print(f"✓ Service '{service.name}' (ID: {service.id}): Already encrypted")
                already_encrypted += 1
                continue
            
            # Token is plain text, needs encryption
            print(f"→ Service '{service.name}' (ID: {service.id}): Plain-text token found")
            
            if dry_run:
                print(f"  [DRY RUN] Would encrypt token for service '{service.name}'")
                migrated += 1
                continue
            
            try:
                # Encrypt the token
                encrypted_token = encrypt_token(token_value, settings.secret_key)
                
                # Update the service directly in the database
                # We update _auth_token_encrypted to bypass the setter
                service._auth_token_encrypted = encrypted_token
                db.add(service)
                
                print(f"  ✓ Encrypted token for service '{service.name}'")
                migrated += 1
                
            except EncryptionError as e:
                print(f"  ✗ Failed to encrypt token for service '{service.name}': {e}")
                errors += 1
            except Exception as e:
                print(f"  ✗ Unexpected error for service '{service.name}': {e}")
                errors += 1
        
        if not dry_run and migrated > 0:
            db.commit()
            print("-" * 60)
            print(f"✅ Successfully migrated {migrated} token(s)")
        elif dry_run:
            print("-" * 60)
            print(f"📋 [DRY RUN] Would migrate {migrated} token(s)")
        
        if already_encrypted > 0:
            print(f"ℹ️  {already_encrypted} token(s) already encrypted")
        
        if errors > 0:
            print(f"⚠️  {errors} error(s) encountered")
            return 1
        
        return 0
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error during migration: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        db.close()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Migrate plain-text service authentication tokens to encrypted format"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be changed without making changes"
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("Service Token Encryption Migration")
    print("=" * 60)
    
    if args.dry_run:
        print("🔍 Running in DRY RUN mode - no changes will be made")
        print()
    
    return migrate_tokens(dry_run=args.dry_run)


if __name__ == "__main__":
    sys.exit(main())


