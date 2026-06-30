#!/usr/bin/env python3
"""Test script to verify VirusTotal API integration."""

import os
import sys
import asyncio
import httpx
from pathlib import Path

repo_root = Path(__file__).resolve().parent.parent
env_path = repo_root / ".env"
if env_path.is_file():
    try:
        from dotenv import load_dotenv

        load_dotenv(env_path)
    except ImportError:
        pass

if not os.getenv("SECURITY_DATABASE_URL") and os.getenv("DATABASE_URL", "").find("@postgres") >= 0:
    print(
        "[HINT] Host-side DB tests need SECURITY_DATABASE_URL with @localhost:5432 "
        "(see docs/portfolio/OPERATOR_SECURITY_GATES.md)"
    )

# Add security-service to path
sys.path.insert(0, str(repo_root / "security-service"))

from security_service.config import config
from security_service.intelligence.ip_reputation import IPReputationService
from security_service.database import get_db, init_db


async def test_virustotal_api_key():
    """Test VirusTotal API key directly."""
    api_key = config.virustotal_api_key
    
    if not api_key:
        print("[FAIL] SECURITY_VIRUSTOTAL_API_KEY is not set in environment")
        return False
    
    print("[OK] SECURITY_VIRUSTOTAL_API_KEY is set")
    
    # Test with a known IP
    test_ip = "8.8.8.8"
    url = "https://www.virustotal.com/vtapi/v2/ip-address/report"
    params = {
        "apikey": api_key,
        "ip": test_ip
    }
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("response_code") == 1:
                    print("[OK] VirusTotal API key is VALID")
                    print(f"   Test IP: {test_ip}")
                    print(f"   Detected URLs: {len(data.get('detected_urls', []))}")
                    return True
                elif data.get("response_code") == 0:
                    print("[WARN] API key is valid but IP not found in database")
                    return True
                else:
                    print(f"[FAIL] API error: {data.get('verbose_msg', 'Unknown error')}")
                    return False
            elif response.status_code == 403:
                print("[FAIL] API key is INVALID or rate limit exceeded")
                return False
            else:
                print(f"[FAIL] HTTP Error: {response.status_code}")
                print(f"   Response: {response.text[:200]}")
                return False
    except Exception as e:
        print(f"[FAIL] Error testing API: {e}")
        return False


async def test_ip_reputation_service():
    """Test the IPReputationService integration."""
    print("\n" + "="*60)
    print("Testing IPReputationService Integration")
    print("="*60)
    
    # Initialize database
    try:
        init_db()
        db = next(get_db())
    except Exception as e:
        print(f"[WARN] Database not available: {e}")
        print("   Skipping database integration test")
        return True
    
    try:
        service = IPReputationService(db)
        
        # Test with a known IP
        test_ip = "8.8.8.8"
        print(f"\nTesting IP reputation check for: {test_ip}")
        
        result = await service.check_ip_reputation(test_ip)
        
        if result:
            print("[OK] IP Reputation Service working")
            print(f"   IP: {result.ip_address}")
            print(f"   Reputation Score: {result.reputation_score}/100")
            print(f"   Confidence: {result.confidence_level}")
            print(f"   Source: {result.source}")
            print(f"   Is Malicious: {result.is_malicious}")
            return True
        else:
            print("[FAIL] IP Reputation Service returned no result")
            return False
    except Exception as e:
        print(f"[FAIL] Error testing IP Reputation Service: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


async def main():
    """Run all tests."""
    print("="*60)
    print("VirusTotal Integration Test")
    print("="*60)
    
    # Test 1: Direct API key test
    print("\n1. Testing VirusTotal API Key Directly")
    print("-" * 60)
    api_test_passed = await test_virustotal_api_key()
    
    # Test 2: IP Reputation Service
    if api_test_passed:
        service_test_passed = await test_ip_reputation_service()
        
        if service_test_passed:
            print("\n" + "="*60)
            print("[OK] All tests passed! VirusTotal integration is working.")
            print("="*60)
            return 0
        else:
            print("\n" + "="*60)
            print("[WARN] API key works but service integration has issues")
            print("="*60)
            return 1
    else:
        print("\n" + "="*60)
        print("[FAIL] API key test failed. Please check your configuration.")
        print("="*60)
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

