"""Demo script showing how to use the free breach detection system."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from security_service.intelligence.password_breach import PasswordBreachService
from security_service.config import config


async def demo_password_checking():
    """Demonstrate password breach checking."""
    print("\n" + "="*70)
    print("DEMO: Password Breach Checking (Free HIBP Pwned Passwords API)")
    print("="*70)
    
    service = PasswordBreachService()
    
    print("\nChecking common passwords against breach database...")
    print("-" * 70)
    
    passwords_to_check = [
        "password",
        "123456",
        "qwerty",
        "admin",
        "letmein",
    ]
    
    for password in passwords_to_check:
        is_breached, count = await service.check_password(password)
        if is_breached:
            print(f"  '{password}': BREACHED ({count:,} occurrences) - DO NOT USE!")
        else:
            print(f"  '{password}': Safe")
    
    print("\n" + "-" * 70)
    print("Note: This uses the FREE HIBP Pwned Passwords API")
    print("      No API key required!")
    print("="*70)


async def demo_password_validation():
    """Demonstrate password validation."""
    print("\n" + "="*70)
    print("DEMO: Password Validation")
    print("="*70)
    
    service = PasswordBreachService()
    
    test_passwords = [
        "password123",
        "MySecurePass2024!",
    ]
    
    for password in test_passwords:
        is_valid, error_msg = await service.validate_password(password)
        print(f"\nPassword: {password}")
        if is_valid:
            print("  Result: VALID - Safe to use")
        else:
            print(f"  Result: INVALID - {error_msg}")
    
    print("\n" + "="*70)


async def main():
    """Run demos."""
    print("\n" + "="*70)
    print("FREE BREACH DETECTION SYSTEM - DEMO")
    print("="*70)
    print("\nThis demo shows the free breach detection capabilities:")
    print("  - Password checking using HIBP Pwned Passwords API (FREE)")
    print("  - No API key required")
    print("  - Real-time breach detection")
    
    await demo_password_checking()
    await demo_password_validation()
    
    print("\n" + "="*70)
    print("DEMO COMPLETE")
    print("="*70)
    print("\nTo use email/domain checking:")
    print("  1. Set up database connection")
    print("  2. Configure public breach sources in .env")
    print("  3. Use EmailBreachService and DomainBreachService")
    print("\n")


if __name__ == "__main__":
    asyncio.run(main())

