"""Secure breach data intake service."""

import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, validator
import hashlib

from ..intelligence.email_breach import EmailBreachService
from ..intelligence.password_breach import PasswordBreachService
from ..intelligence.domain_breach import DomainBreachService
from ..models.breaches import UserBreach
from ..models.security_events import SecurityEvent, EventType, EventSeverity

logger = logging.getLogger(__name__)


class BreachIntakeRequest(BaseModel):
    """Request model for breach data intake."""
    emails: List[EmailStr] = []
    passwords: List[str] = []  # Will be hashed immediately
    domains: List[str] = []
    user_ids: Optional[Dict[str, int]] = None  # Optional mapping of email to user_id
    metadata: Optional[Dict[str, Any]] = None
    
    @validator('passwords')
    def validate_passwords(cls, v):
        """Validate password list is not too large."""
        if len(v) > 100:
            raise ValueError("Maximum 100 passwords per request")
        return v


class BreachIntakeService:
    """Service for securely intaking and processing breach data."""
    
    def __init__(self, db: Session):
        self.db = db
        self.email_service = EmailBreachService(db)
        self.password_service = PasswordBreachService()
        self.domain_service = DomainBreachService(db)
    
    async def process_intake(
        self,
        request: BreachIntakeRequest,
        source: str = "api",
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Process intake request and run breach checks.
        
        Args:
            request: Intake request with emails, passwords, domains
            source: Source of the intake (api, manual, import, etc.)
            user_id: Optional user ID making the request
        
        Returns:
            Comprehensive report with breach findings and recommendations
        """
        # Validate at least one field has data
        if not request.emails and not request.passwords and not request.domains:
            raise ValueError("At least one of emails, passwords, or domains must be provided")
        
        results = {
            "processed_at": datetime.now(timezone.utc).isoformat(),
            "source": source,
            "summary": {
                "emails_checked": 0,
                "emails_breached": 0,
                "passwords_checked": 0,
                "passwords_breached": 0,
                "domains_checked": 0,
                "domains_breached": 0
            },
            "email_results": [],
            "password_results": [],
            "domain_results": [],
            "recommendations": [],
            "risk_score": 0
        }
        
        # Process emails
        if request.emails:
            email_results = await self._process_emails(
                request.emails,
                request.user_ids or {}
            )
            results["email_results"] = email_results
            results["summary"]["emails_checked"] = len(request.emails)
            results["summary"]["emails_breached"] = sum(
                1 for r in email_results if r["breach_count"] > 0
            )
        
        # Process passwords (hashed immediately, never stored)
        if request.passwords:
            password_results = await self._process_passwords(request.passwords)
            results["password_results"] = password_results
            results["summary"]["passwords_checked"] = len(request.passwords)
            results["summary"]["passwords_breached"] = sum(
                1 for r in password_results if r["is_breached"]
            )
        
        # Process domains
        if request.domains:
            domain_results = await self._process_domains(request.domains)
            results["domain_results"] = domain_results
            results["summary"]["domains_checked"] = len(request.domains)
            results["summary"]["domains_breached"] = sum(
                1 for r in domain_results if r["breach_count"] > 0
            )
        
        # Calculate risk score
        results["risk_score"] = self._calculate_risk_score(results)
        
        # Generate recommendations
        results["recommendations"] = self._generate_recommendations(results)
        
        # Log security event
        self._log_intake_event(request, results, source, user_id)
        
        return results
    
    async def _process_emails(
        self,
        emails: List[str],
        user_ids: Dict[str, int]
    ) -> List[Dict[str, Any]]:
        """Process email breach checks."""
        results = []
        
        for email in emails:
            try:
                user_id = user_ids.get(email)
                breaches = await self.email_service.check_email(
                    email,
                    user_id=user_id,
                    force_refresh=False,
                    truncate_response=False
                )
                
                breach_count = len(breaches)
                breach_names = [b.get("breach_name", "Unknown") for b in breaches]
                
                # Get data classes exposed
                data_classes = set()
                for breach in breaches:
                    if isinstance(breach, dict):
                        classes = breach.get("data_classes", [])
                        if isinstance(classes, list):
                            data_classes.update(classes)
                
                results.append({
                    "email": email,
                    "breach_count": breach_count,
                    "breach_names": breach_names,
                    "data_classes_exposed": list(data_classes),
                    "is_breached": breach_count > 0,
                    "risk_level": self._assess_email_risk(breach_count, data_classes)
                })
                
            except Exception as e:
                logger.error(f"Error processing email {email}: {e}")
                results.append({
                    "email": email,
                    "error": str(e),
                    "is_breached": False
                })
        
        return results
    
    async def _process_passwords(self, passwords: List[str]) -> List[Dict[str, Any]]:
        """Process password breach checks (passwords are hashed, never stored)."""
        results = []
        
        for password in passwords:
            try:
                # Hash password for logging (never store plain text)
                password_hash = hashlib.sha256(password.encode()).hexdigest()[:16]
                
                is_breached, breach_count = await self.password_service.check_password(password)
                
                results.append({
                    "password_hash_prefix": password_hash,  # Only prefix for identification
                    "is_breached": is_breached,
                    "breach_count": breach_count,
                    "risk_level": "critical" if is_breached else "low"
                })
                
            except Exception as e:
                logger.error(f"Error processing password: {e}")
                results.append({
                    "error": str(e),
                    "is_breached": False
                })
        
        return results
    
    async def _process_domains(self, domains: List[str]) -> List[Dict[str, Any]]:
        """Process domain breach checks."""
        results = []
        
        for domain in domains:
            try:
                breached_emails = await self.domain_service.check_domain(
                    domain,
                    force_refresh=False
                )
                
                breach_count = len(breached_emails)
                
                # Get unique breach names
                breach_names = set()
                for email_data in breached_emails:
                    if isinstance(email_data, dict):
                        breaches = email_data.get("Breaches", [])
                        for breach in breaches:
                            if isinstance(breach, dict):
                                breach_names.add(breach.get("Name", ""))
                
                results.append({
                    "domain": domain,
                    "breach_count": breach_count,
                    "breach_names": list(breach_names),
                    "affected_emails": breach_count,
                    "is_breached": breach_count > 0,
                    "risk_level": self._assess_domain_risk(breach_count)
                })
                
            except Exception as e:
                logger.error(f"Error processing domain {domain}: {e}")
                results.append({
                    "domain": domain,
                    "error": str(e),
                    "is_breached": False
                })
        
        return results
    
    def _assess_email_risk(self, breach_count: int, data_classes: set) -> str:
        """Assess risk level for email breach."""
        if breach_count == 0:
            return "low"
        
        # High risk if passwords exposed
        if "Passwords" in data_classes or "Password hashes" in data_classes:
            return "critical"
        
        # Medium-high if sensitive data exposed
        sensitive_classes = {"Credit cards", "Bank account numbers", "Social security numbers"}
        if any(cls in data_classes for cls in sensitive_classes):
            return "high"
        
        # Medium if multiple breaches
        if breach_count > 3:
            return "high"
        
        return "medium"
    
    def _assess_domain_risk(self, affected_emails: int) -> str:
        """Assess risk level for domain breach."""
        if affected_emails == 0:
            return "low"
        elif affected_emails > 50:
            return "critical"
        elif affected_emails > 10:
            return "high"
        else:
            return "medium"
    
    def _calculate_risk_score(self, results: Dict[str, Any]) -> int:
        """Calculate overall risk score (0-100)."""
        score = 0
        
        # Email breaches contribute to score
        for email_result in results.get("email_results", []):
            if email_result.get("is_breached"):
                breach_count = email_result.get("breach_count", 0)
                risk_level = email_result.get("risk_level", "low")
                
                if risk_level == "critical":
                    score += 30 * breach_count
                elif risk_level == "high":
                    score += 20 * breach_count
                elif risk_level == "medium":
                    score += 10 * breach_count
                else:
                    score += 5 * breach_count
        
        # Password breaches contribute heavily
        for password_result in results.get("password_results", []):
            if password_result.get("is_breached"):
                breach_count = password_result.get("breach_count", 0)
                score += 25 * min(breach_count, 10)  # Cap at 10x multiplier
        
        # Domain breaches contribute significantly
        for domain_result in results.get("domain_results", []):
            if domain_result.get("is_breached"):
                affected = domain_result.get("affected_emails", 0)
                score += min(affected * 2, 50)  # Cap at 50 points
        
        return min(score, 100)  # Cap at 100
    
    def _generate_recommendations(self, results: Dict[str, Any]) -> List[str]:
        """Generate actionable recommendations based on findings."""
        recommendations = []
        summary = results.get("summary", {})
        
        # Password recommendations
        if summary.get("passwords_breached", 0) > 0:
            recommendations.append(
                f"URGENT: {summary['passwords_breached']} password(s) found in breach database. "
                "Immediately change these passwords and use unique, strong passwords."
            )
        
        # Email recommendations
        emails_breached = summary.get("emails_breached", 0)
        if emails_breached > 0:
            recommendations.append(
                f"{emails_breached} email address(es) found in data breach(es). "
                "Notify affected users and require password changes."
            )
            
            # Check for high-risk data exposure
            for email_result in results.get("email_results", []):
                if email_result.get("risk_level") == "critical":
                    recommendations.append(
                        f"CRITICAL: Email {email_result.get('email')} exposed passwords in breach. "
                        "Immediate password reset required."
                    )
        
        # Domain recommendations
        if summary.get("domains_breached", 0) > 0:
            recommendations.append(
                f"{summary['domains_breached']} domain(s) affected by breaches. "
                "Conduct organization-wide security review and notify all affected users."
            )
        
        # Risk score recommendations
        risk_score = results.get("risk_score", 0)
        if risk_score >= 75:
            recommendations.append(
                "HIGH RISK: Overall risk score is critical. Implement immediate security measures "
                "including mandatory password resets and enhanced monitoring."
            )
        elif risk_score >= 50:
            recommendations.append(
                "MEDIUM-HIGH RISK: Review security posture and implement additional controls."
            )
        
        # General recommendations
        if not recommendations:
            recommendations.append("No breaches detected. Continue monitoring and maintain security best practices.")
        else:
            recommendations.append(
                "Enable two-factor authentication (2FA) for all affected accounts."
            )
            recommendations.append(
                "Review and update security policies based on breach findings."
            )
        
        return recommendations
    
    def _log_intake_event(
        self,
        request: BreachIntakeRequest,
        results: Dict[str, Any],
        source: str,
        user_id: Optional[int]
    ) -> None:
        """Log security event for intake processing."""
        try:
            risk_score = results.get("risk_score", 0)
            severity = (
                EventSeverity.CRITICAL if risk_score >= 75 else
                EventSeverity.HIGH if risk_score >= 50 else
                EventSeverity.MEDIUM if risk_score >= 25 else
                EventSeverity.LOW
            )
            
            event = SecurityEvent(
                event_type=EventType.ANOMALY_DETECTED,
                severity=severity.value,
                user_id=user_id,
                description=f"Breach intake processed: {results['summary']}",
                event_metadata={
                    "source": source,
                    "risk_score": risk_score,
                    "summary": results["summary"],
                    "email_count": len(request.emails),
                    "password_count": len(request.passwords),
                    "domain_count": len(request.domains)
                }
            )
            
            self.db.add(event)
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Failed to log intake event: {e}")
            self.db.rollback()

