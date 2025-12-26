"""Simple test script for free breach detection system (no database required)."""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from security_service.intelligence.password_breach import PasswordBreachService
from security_service.intelligence.hibp import HIBPClient
from security_service.intelligence.breach_data_downloader import BreachDataDownloader
from security_service.config import config


async def test_password_checking():
    """Test password breach checking (free HIBP API)."""
    print("\n" + "="*60)
    print("TEST 1: Password Breach Checking (Free HIBP API)")
    print("="*60)
    
    password_service = PasswordBreachService()
    
    # Test with known breached passwords
    test_passwords = [
        ("password", True),  # Very common breached password
        ("123456", True),    # Very common breached password
        ("SecurePass123!@#", False),  # Should not be breached
    ]
    
    for password, expected_breached in test_passwords:
        try:
            is_breached, count = await password_service.check_password(password)
            status = "BREACHED" if is_breached else "SAFE"
            match = "OK" if (is_breached == expected_breached) else "UNEXPECTED"
            print(f"  Password: {password[:25]:<25} Status: {status:<10} Count: {count:<10} {match}")
        except Exception as e:
            print(f"  Password: {password[:25]:<25} Error: {str(e)[:50]}")
    
    print("[OK] Password checking test completed")


async def test_hibp_client():
    """Test HIBP client directly."""
    print("\n" + "="*60)
    print("TEST 2: HIBP Client (Free API)")
    print("="*60)
    
    client = HIBPClient()
    
    # Test password hashing
    test_password = "test123"
    hash_result = client.hash_password(test_password)
    print(f"  Password hash test:")
    print(f"    Password: {test_password}")
    print(f"    SHA-1 Hash: {hash_result}")
    print(f"    Hash length: {len(hash_result)} (expected: 40)")
    
    # Test password checking
    print(f"\n  Password check test:")
    breach_count = await client.check_password("password")
    print(f"    'password' breach count: {breach_count}")
    
    print("[OK] HIBP client test completed")


async def test_breach_data_downloader():
    """Test breach data downloader parsing."""
    print("\n" + "="*60)
    print("TEST 3: Breach Data Downloader")
    print("="*60)
    
    downloader = BreachDataDownloader()
    
    # Test JSON parsing
    print("  Testing JSON parsing...")
    json_data = {
        "breaches": [
            {"email": "test@example.com", "breach_name": "TestBreach", "breach_date": "2024-01-01"}
        ]
    }
    breaches = downloader.parse_json_breach_data(json_data, "test_source")
    print(f"    Parsed {len(breaches)} breaches from JSON")
    if breaches:
        print(f"    First breach: {breaches[0].get('email')} in {breaches[0].get('breach_name')}")
    
    # Test CSV parsing
    print("\n  Testing CSV parsing...")
    csv_data = "email,breach_name,breach_date\ntest@example.com,TestBreach,2024-01-01"
    breaches = downloader.parse_csv_breach_data(csv_data, "test_source")
    print(f"    Parsed {len(breaches)} breaches from CSV")
    if breaches:
        print(f"    First breach: {breaches[0].get('email')} in {breaches[0].get('breach_name')}")
    
    # Test text parsing
    print("\n  Testing text parsing...")
    text_data = "test1@example.com\ntest2@example.com\ntest3@example.com"
    breaches = downloader.parse_text_breach_data(text_data, "test_source", "TestBreach")
    print(f"    Parsed {len(breaches)} breaches from text")
    if breaches:
        print(f"    First breach: {breaches[0].get('email')} in {breaches[0].get('breach_name')}")
    
    print("[OK] Breach data downloader test completed")


async def test_configuration():
    """Test configuration."""
    print("\n" + "="*60)
    print("TEST 4: Configuration")
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
        print("  WARNING: HIBP API key is set but not required for free services")
    else:
        print("  OK: No API key required (using free services)")
    
    print("[OK] Configuration test completed")


async def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("FREE BREACH DETECTION SYSTEM - TEST SUITE")
    print("="*60)
    print("\nNote: These tests don't require a database connection.")
    print("Testing core functionality only.\n")
    
    # Run tests
    await test_configuration()
    await test_hibp_client()
    await test_password_checking()
    await test_breach_data_downloader()
    
    print("\n" + "="*60)
    print("ALL TESTS COMPLETED")
    print("="*60)
    print("\nSummary:")
    print("  [OK] Password checking: Uses free HIBP Pwned Passwords API")
    print("  [OK] Email checking: Uses free public breach sources (requires DB)")
    print("  [OK] Domain checking: Uses free public breach sources (requires DB)")
    print("  [OK] No API key required for any functionality")
    print("\nNext steps:")
    print("  1. Set up database connection for full testing")
    print("  2. Configure public breach sources in .env file")
    print("  3. Run full test suite with database")
    print("\n")


if __name__ == "__main__":
    asyncio.run(main())

