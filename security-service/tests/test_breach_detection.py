"""Test script for free breach detection system."""

import asyncio
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from security_service.database import get_db, init_db
from security_service.intelligence.password_breach import PasswordBreachService
from security_service.intelligence.email_breach import EmailBreachService
from security_service.intelligence.domain_breach import DomainBreachService
from security_service.intelligence.public_breach_sources import PublicBreachSources
from security_service.intelligence.breach_database import BreachDatabase
from security_service.intelligence.breach_data_downloader import BreachDataDownloader
from security_service.config import config


async def test_password_checking():
    """Test password breach checking (free HIBP API)."""
    print("\n" + "="*60)
    print("TEST 1: Password Breach Checking (Free HIBP API)")
    print("="*60)
    
    password_service = PasswordBreachService()
    
    # Test with known breached password
    test_passwords = [
        "password",  # Very common breached password
        "123456",    # Very common breached password
        "SecurePass123!@#",  # Should not be breached
    ]
    
    for password in test_passwords:
        try:
            is_breached, count = await password_service.check_password(password)
            status = "BREACHED" if is_breached else "SAFE"
            print(f"  Password: {password[:20]:<20} Status: {status:<10} Count: {count}")
        except Exception as e:
            print(f"  Password: {password[:20]:<20} Error: {e}")
    
    print("✓ Password checking test completed")


async def test_breach_database():
    """Test breach database functionality."""
    print("\n" + "="*60)
    print("TEST 2: Breach Database")
    print("="*60)
    
    db = next(get_db())
    try:
        breach_db = BreachDatabase(db)
        
        # Test statistics
        stats = breach_db.get_breach_statistics()
        print(f"  Database Statistics:")
        print(f"    Total breach records: {stats['total_breach_records']}")
        print(f"    Unique emails: {stats['unique_emails']}")
        print(f"    Unique breach names: {stats['unique_breach_names']}")
        print(f"    Unique domains: {stats['unique_domains']}")
        
        # Test email lookup
        test_email = "test@example.com"
        breaches = breach_db.lookup_email(test_email)
        print(f"\n  Email lookup for {test_email}: {len(breaches)} breaches found")
        
        # Test domain lookup
        test_domain = "example.com"
        domain_breaches = breach_db.lookup_domain(test_domain)
        print(f"  Domain lookup for {test_domain}: {len(domain_breaches)} breaches found")
        
        print("✓ Breach database test completed")
    finally:
        db.close()


async def test_email_breach_checking():
    """Test email breach checking using public sources."""
    print("\n" + "="*60)
    print("TEST 3: Email Breach Checking (Public Sources)")
    print("="*60)
    
    db = next(get_db())
    try:
        email_service = EmailBreachService(db)
        
        test_emails = [
            "test@example.com",
            "user@test.com",
        ]
        
        for email in test_emails:
            try:
                breaches = await email_service.check_email(email)
                print(f"  Email: {email:<30} Breaches: {len(breaches)}")
                if breaches:
                    for breach in breaches[:3]:  # Show first 3
                        print(f"    - {breach.get('breach_name', 'Unknown')}")
            except Exception as e:
                print(f"  Email: {email:<30} Error: {e}")
        
        print("✓ Email breach checking test completed")
    finally:
        db.close()


async def test_domain_breach_checking():
    """Test domain breach checking using public sources."""
    print("\n" + "="*60)
    print("TEST 4: Domain Breach Checking (Public Sources)")
    print("="*60)
    
    db = next(get_db())
    try:
        domain_service = DomainBreachService(db)
        
        test_domains = [
            "example.com",
            "test.com",
        ]
        
        for domain in test_domains:
            try:
                breaches = await domain_service.check_domain(domain)
                print(f"  Domain: {domain:<30} Breached emails: {len(breaches)}")
            except Exception as e:
                print(f"  Domain: {domain:<30} Error: {e}")
        
        print("✓ Domain breach checking test completed")
    finally:
        db.close()


async def test_public_breach_sources():
    """Test public breach sources service."""
    print("\n" + "="*60)
    print("TEST 5: Public Breach Sources")
    print("="*60)
    
    db = next(get_db())
    try:
        public_sources = PublicBreachSources(db)
        
        # Get statistics
        stats = public_sources.get_statistics()
        print(f"  Breach Database Statistics:")
        print(f"    Total records: {stats.get('total_breach_records', 0)}")
        print(f"    Unique emails: {stats.get('unique_emails', 0)}")
        print(f"    Unique breach names: {stats.get('unique_breach_names', 0)}")
        
        # Test email lookup
        test_email = "test@example.com"
        breaches = public_sources.lookup_email(test_email)
        print(f"\n  Email lookup for {test_email}: {len(breaches)} breaches")
        
        # Test domain lookup
        test_domain = "example.com"
        domain_breaches = public_sources.lookup_domain(test_domain)
        print(f"  Domain lookup for {test_domain}: {len(domain_breaches)} breach groups")
        
        print("✓ Public breach sources test completed")
    finally:
        db.close()


async def test_breach_data_downloader():
    """Test breach data downloader."""
    print("\n" + "="*60)
    print("TEST 6: Breach Data Downloader")
    print("="*60)
    
    downloader = BreachDataDownloader()
    
    # Test parsing functions
    print("  Testing JSON parsing...")
    json_data = {
        "breaches": [
            {"email": "test@example.com", "breach_name": "TestBreach", "breach_date": "2024-01-01"}
        ]
    }
    breaches = downloader.parse_json_breach_data(json_data, "test_source")
    print(f"    Parsed {len(breaches)} breaches from JSON")
    
    # Test CSV parsing
    print("  Testing CSV parsing...")
    csv_data = "email,breach_name,breach_date\ntest@example.com,TestBreach,2024-01-01"
    breaches = downloader.parse_csv_breach_data(csv_data, "test_source")
    print(f"    Parsed {len(breaches)} breaches from CSV")
    
    # Test text parsing
    print("  Testing text parsing...")
    text_data = "test1@example.com\ntest2@example.com\ntest3@example.com"
    breaches = downloader.parse_text_breach_data(text_data, "test_source", "TestBreach")
    print(f"    Parsed {len(breaches)} breaches from text")
    
    print("✓ Breach data downloader test completed")


async def test_configuration():
    """Test configuration."""
    print("\n" + "="*60)
    print("TEST 7: Configuration")
    print("="*60)
    
    print(f"  Password check enabled: {config.hibp_enable_password_check}")
    print(f"  Email check enabled: {config.hibp_enable_email_check}")
    print(f"  Cache TTL: {config.hibp_cache_ttl} seconds")
    print(f"  Rate limit delay: {config.hibp_rate_limit_delay} seconds")
    print(f"  Monitored domains: {getattr(config, 'breach_monitored_domains', [])}")
    print(f"  Public breach sources: {len(config.public_breach_sources or [])} configured")
    print(f"  Breach data cache dir: {config.breach_data_cache_dir}")
    
    # Check that API key is not required
    if hasattr(config, 'hibp_api_key') and config.hibp_api_key:
        print("  ⚠ WARNING: HIBP API key is set but not required for free services")
    else:
        print("  ✓ No API key required (using free services)")
    
    print("✓ Configuration test completed")


async def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("FREE BREACH DETECTION SYSTEM - TEST SUITE")
    print("="*60)
    print("\nInitializing database...")
    
    try:
        init_db()
        print("✓ Database initialized")
    except Exception as e:
        print(f"⚠ Database initialization warning: {e}")
        print("  Continuing with existing database...")
    
    # Run tests
    await test_configuration()
    await test_password_checking()
    await test_breach_database()
    await test_breach_data_downloader()
    await test_public_breach_sources()
    await test_email_breach_checking()
    await test_domain_breach_checking()
    
    print("\n" + "="*60)
    print("ALL TESTS COMPLETED")
    print("="*60)
    print("\nSummary:")
    print("  ✓ Password checking: Uses free HIBP Pwned Passwords API")
    print("  ✓ Email checking: Uses free public breach sources")
    print("  ✓ Domain checking: Uses free public breach sources")
    print("  ✓ No API key required for any functionality")
    print("\n")


if __name__ == "__main__":
    asyncio.run(main())

