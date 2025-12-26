#!/usr/bin/env python3
"""
Example script for using the breach intake and reporting system.

Usage:
    python breach_check_example.py
"""

import asyncio
import httpx
import sys
from pathlib import Path

# Add security-service to path
sys.path.insert(0, str(Path(__file__).parent.parent / "security-service"))


async def check_single_email(email: str, api_url: str = "http://localhost:8001"):
    """Check a single email for breaches."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{api_url}/api/security/breaches/intake",
            json={
                "emails": [email]
            }
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error: {response.status_code} - {response.text}")
            return None


async def check_password(password: str, api_url: str = "http://localhost:8001"):
    """Check a password for breaches."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{api_url}/api/security/breaches/intake",
            json={
                "passwords": [password]
            }
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error: {response.status_code} - {response.text}")
            return None


async def comprehensive_report(
    emails: list = None,
    passwords: list = None,
    domains: list = None,
    api_url: str = "http://localhost:8001"
):
    """Generate comprehensive breach report."""
    data = {}
    if emails:
        data["emails"] = emails
    if passwords:
        data["passwords"] = passwords
    if domains:
        data["domains"] = domains
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{api_url}/api/security/breaches/comprehensive-report",
            json=data
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error: {response.status_code} - {response.text}")
            return None


async def main():
    """Example usage."""
    print("=" * 60)
    print("Breach Intake and Reporting System - Example")
    print("=" * 60)
    
    # Example 1: Check single email
    print("\n1. Checking email for breaches...")
    email_result = await check_single_email("test@example.com")
    if email_result:
        summary = email_result.get("summary", {})
        print(f"   Emails checked: {summary.get('emails_checked', 0)}")
        print(f"   Emails breached: {summary.get('emails_breached', 0)}")
        print(f"   Risk score: {email_result.get('risk_score', 0)}")
    
    # Example 2: Check password
    print("\n2. Checking password for breaches...")
    password_result = await check_password("password123")
    if password_result:
        summary = password_result.get("summary", {})
        print(f"   Passwords checked: {summary.get('passwords_checked', 0)}")
        print(f"   Passwords breached: {summary.get('passwords_breached', 0)}")
        if summary.get('passwords_breached', 0) > 0:
            print("   ⚠️  WARNING: Password found in breach database!")
    
    # Example 3: Comprehensive report
    print("\n3. Generating comprehensive report...")
    report = await comprehensive_report(
        emails=["test@example.com"],
        passwords=["password123"],
        domains=["example.com"]
    )
    
    if report:
        exec_summary = report.get("executive_summary", {})
        print(f"   Overall Risk Score: {exec_summary.get('overall_risk_score', 0)}")
        print(f"   Risk Level: {exec_summary.get('risk_level', 'UNKNOWN')}")
        print(f"   Total Breaches: {exec_summary.get('total_breaches_detected', 0)}")
        
        # Show recommendations
        recommendations = report.get("recommendations", [])
        if recommendations:
            print("\n   Top Recommendations:")
            for i, rec in enumerate(recommendations[:5], 1):
                print(f"   {i}. {rec}")
        
        # Show action plan
        action_plan = report.get("action_plan", {})
        immediate_actions = action_plan.get("immediate_actions", [])
        if immediate_actions:
            print("\n   Immediate Actions Required:")
            for action in immediate_actions:
                print(f"   - {action.get('action')} ({action.get('priority')})")
    
    print("\n" + "=" * 60)
    print("Example completed!")
    print("=" * 60)
    print("\nTo use with your own data:")
    print("1. Update the email/password/domain values in this script")
    print("2. Ensure your .env file has breach detection enabled (no API key required)")
    print("3. Run: python breach_check_example.py")


if __name__ == "__main__":
    asyncio.run(main())

