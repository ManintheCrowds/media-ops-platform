"""Comprehensive breach reporting and analysis service."""

import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from ..models.breaches import UserBreach, DomainBreach, BreachHistory
from ..models.security_events import SecurityEvent, EventType

logger = logging.getLogger(__name__)


class ComprehensiveBreachReporter:
    """Service for generating comprehensive breach analysis reports."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def generate_report(self, intake_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate comprehensive breach analysis report.
        
        Args:
            intake_results: Results from BreachIntakeService
        
        Returns:
            Comprehensive report with actionable insights
        """
        report = {
            "report_id": f"BR-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "executive_summary": self._generate_executive_summary(intake_results),
            "detailed_findings": self._analyze_findings(intake_results),
            "risk_assessment": self._assess_risks(intake_results),
            "action_plan": self._create_action_plan(intake_results),
            "trend_analysis": self._analyze_trends(intake_results),
            "compliance_impact": self._assess_compliance_impact(intake_results),
            "recommendations": self._generate_detailed_recommendations(intake_results),
            "raw_data": intake_results  # Include original intake results
        }
        
        return report
    
    def _generate_executive_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate executive summary of findings."""
        summary = results.get("summary", {})
        risk_score = results.get("risk_score", 0)
        
        return {
            "overall_risk_score": risk_score,
            "risk_level": (
                "CRITICAL" if risk_score >= 75 else
                "HIGH" if risk_score >= 50 else
                "MEDIUM" if risk_score >= 25 else
                "LOW"
            ),
            "key_findings": [
                f"{summary.get('emails_breached', 0)} of {summary.get('emails_checked', 0)} email(s) found in breaches",
                f"{summary.get('passwords_breached', 0)} of {summary.get('passwords_checked', 0)} password(s) found in breach database",
                f"{summary.get('domains_breached', 0)} of {summary.get('domains_checked', 0)} domain(s) affected by breaches"
            ],
            "immediate_actions_required": risk_score >= 50,
            "total_items_checked": (
                summary.get('emails_checked', 0) +
                summary.get('passwords_checked', 0) +
                summary.get('domains_checked', 0)
            ),
            "total_breaches_detected": (
                summary.get('emails_breached', 0) +
                summary.get('passwords_breached', 0) +
                summary.get('domains_breached', 0)
            )
        }
    
    def _analyze_findings(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Detailed analysis of breach findings."""
        findings = {
            "email_analysis": self._analyze_emails(results.get("email_results", [])),
            "password_analysis": self._analyze_passwords(results.get("password_results", [])),
            "domain_analysis": self._analyze_domains(results.get("domain_results", []))
        }
        
        return findings
    
    def _analyze_emails(self, email_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze email breach findings."""
        if not email_results:
            return {"status": "no_emails_checked"}
        
        breached_emails = [r for r in email_results if r.get("is_breached")]
        critical_emails = [r for r in breached_emails if r.get("risk_level") == "critical"]
        
        # Aggregate breach names
        all_breach_names = set()
        data_classes_exposed = set()
        
        for result in breached_emails:
            all_breach_names.update(result.get("breach_names", []))
            data_classes_exposed.update(result.get("data_classes_exposed", []))
        
        return {
            "total_checked": len(email_results),
            "total_breached": len(breached_emails),
            "breach_rate": len(breached_emails) / len(email_results) if email_results else 0,
            "critical_risk_count": len(critical_emails),
            "unique_breaches": list(all_breach_names),
            "data_classes_exposed": list(data_classes_exposed),
            "most_common_breaches": self._get_most_common_breaches(email_results),
            "breached_emails": [
                {
                    "email": r.get("email"),
                    "breach_count": r.get("breach_count"),
                    "risk_level": r.get("risk_level"),
                    "breach_names": r.get("breach_names", [])
                }
                for r in breached_emails
            ]
        }
    
    def _analyze_passwords(self, password_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze password breach findings."""
        if not password_results:
            return {"status": "no_passwords_checked"}
        
        breached_passwords = [r for r in password_results if r.get("is_breached")]
        
        total_breach_count = sum(r.get("breach_count", 0) for r in breached_passwords)
        avg_breach_count = (
            total_breach_count / len(breached_passwords)
            if breached_passwords else 0
        )
        
        return {
            "total_checked": len(password_results),
            "total_breached": len(breached_passwords),
            "breach_rate": len(breached_passwords) / len(password_results) if password_results else 0,
            "total_breach_occurrences": total_breach_count,
            "average_breach_count": avg_breach_count,
            "max_breach_count": max(
                (r.get("breach_count", 0) for r in breached_passwords),
                default=0
            ),
            "critical_risk": len(breached_passwords) > 0
        }
    
    def _analyze_domains(self, domain_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze domain breach findings."""
        if not domain_results:
            return {"status": "no_domains_checked"}
        
        breached_domains = [r for r in domain_results if r.get("is_breached")]
        total_affected_emails = sum(r.get("affected_emails", 0) for r in breached_domains)
        
        return {
            "total_checked": len(domain_results),
            "total_breached": len(breached_domains),
            "breach_rate": len(breached_domains) / len(domain_results) if domain_results else 0,
            "total_affected_emails": total_affected_emails,
            "breached_domains": [
                {
                    "domain": r.get("domain"),
                    "breach_count": r.get("breach_count"),
                    "affected_emails": r.get("affected_emails"),
                    "risk_level": r.get("risk_level"),
                    "breach_names": r.get("breach_names", [])
                }
                for r in breached_domains
            ]
        }
    
    def _get_most_common_breaches(self, email_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Get most common breaches across all emails."""
        breach_counts = {}
        
        for result in email_results:
            for breach_name in result.get("breach_names", []):
                breach_counts[breach_name] = breach_counts.get(breach_name, 0) + 1
        
        sorted_breaches = sorted(
            breach_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]  # Top 10
        
        return [
            {"breach_name": name, "occurrence_count": count}
            for name, count in sorted_breaches
        ]
    
    def _assess_risks(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Comprehensive risk assessment."""
        risk_score = results.get("risk_score", 0)
        
        risks = {
            "overall_risk_score": risk_score,
            "risk_level": (
                "CRITICAL" if risk_score >= 75 else
                "HIGH" if risk_score >= 50 else
                "MEDIUM" if risk_score >= 25 else
                "LOW"
            ),
            "risk_factors": [],
            "impact_assessment": {}
        }
        
        # Password risks
        password_results = results.get("password_results", [])
        breached_passwords = [r for r in password_results if r.get("is_breached")]
        if breached_passwords:
            risks["risk_factors"].append({
                "factor": "Compromised Passwords",
                "severity": "CRITICAL",
                "description": f"{len(breached_passwords)} password(s) found in breach database",
                "impact": "Immediate account compromise risk"
            })
        
        # Email risks
        email_results = results.get("email_results", [])
        critical_emails = [r for r in email_results if r.get("risk_level") == "critical"]
        if critical_emails:
            risks["risk_factors"].append({
                "factor": "Critical Email Breaches",
                "severity": "CRITICAL",
                "description": f"{len(critical_emails)} email(s) with password exposure",
                "impact": "High risk of credential compromise"
            })
        
        # Domain risks
        domain_results = results.get("domain_results", [])
        breached_domains = [r for r in domain_results if r.get("is_breached")]
        if breached_domains:
            total_affected = sum(r.get("affected_emails", 0) for r in breached_domains)
            risks["risk_factors"].append({
                "factor": "Domain Breaches",
                "severity": "HIGH" if total_affected > 10 else "MEDIUM",
                "description": f"{len(breached_domains)} domain(s) affected, {total_affected} email(s) compromised",
                "impact": "Organizational security risk"
            })
        
        # Impact assessment
        risks["impact_assessment"] = {
            "financial_risk": "HIGH" if risk_score >= 75 else "MEDIUM" if risk_score >= 50 else "LOW",
            "reputation_risk": "HIGH" if risk_score >= 50 else "MEDIUM" if risk_score >= 25 else "LOW",
            "operational_risk": "HIGH" if risk_score >= 50 else "MEDIUM" if risk_score >= 25 else "LOW",
            "compliance_risk": "HIGH" if risk_score >= 50 else "MEDIUM" if risk_score >= 25 else "LOW"
        }
        
        return risks
    
    def _create_action_plan(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Create prioritized action plan."""
        risk_score = results.get("risk_score", 0)
        
        actions = {
            "immediate_actions": [],
            "short_term_actions": [],
            "long_term_actions": []
        }
        
        # Immediate actions (critical risk)
        if risk_score >= 75:
            actions["immediate_actions"].extend([
                {
                    "action": "Force password reset for all breached accounts",
                    "priority": "CRITICAL",
                    "timeline": "Within 24 hours",
                    "owner": "Security Team"
                },
                {
                    "action": "Enable enhanced monitoring for affected accounts",
                    "priority": "CRITICAL",
                    "timeline": "Immediately",
                    "owner": "Security Team"
                },
                {
                    "action": "Notify affected users of breach exposure",
                    "priority": "HIGH",
                    "timeline": "Within 48 hours",
                    "owner": "Communications Team"
                }
            ])
        
        # Password-specific actions
        password_results = results.get("password_results", [])
        if any(r.get("is_breached") for r in password_results):
            actions["immediate_actions"].append({
                "action": "Block and replace all breached passwords",
                "priority": "CRITICAL",
                "timeline": "Immediately",
                "owner": "IT Operations"
            })
        
        # Email-specific actions
        email_results = results.get("email_results", [])
        breached_emails = [r for r in email_results if r.get("is_breached")]
        if breached_emails:
            actions["short_term_actions"].append({
                "action": f"Review security posture for {len(breached_emails)} affected email(s)",
                "priority": "HIGH",
                "timeline": "Within 1 week",
                "owner": "Security Team"
            })
        
        # Domain-specific actions
        domain_results = results.get("domain_results", [])
        if any(r.get("is_breached") for r in domain_results):
            actions["short_term_actions"].append({
                "action": "Conduct organization-wide security review",
                "priority": "HIGH",
                "timeline": "Within 2 weeks",
                "owner": "Security Team"
            })
        
        # Long-term actions
        actions["long_term_actions"].extend([
            {
                "action": "Implement password breach checking in registration flow",
                "priority": "MEDIUM",
                "timeline": "Within 1 month",
                "owner": "Development Team"
            },
            {
                "action": "Establish regular breach monitoring schedule",
                "priority": "MEDIUM",
                "timeline": "Within 1 month",
                "owner": "Security Team"
            },
            {
                "action": "Enhance security awareness training",
                "priority": "MEDIUM",
                "timeline": "Within 3 months",
                "owner": "HR/Security Team"
            }
        ])
        
        return actions
    
    def _analyze_trends(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze trends from historical data."""
        # Get historical breach data
        thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
        
        recent_breaches = self.db.query(UserBreach).filter(
            UserBreach.detected_at >= thirty_days_ago
        ).count()
        
        total_breaches = self.db.query(UserBreach).count()
        
        return {
            "historical_context": {
                "total_breaches_in_system": total_breaches,
                "breaches_last_30_days": recent_breaches,
                "trend": "increasing" if recent_breaches > total_breaches / 2 else "stable"
            },
            "comparison": {
                "current_intake_breaches": results.get("summary", {}).get("emails_breached", 0),
                "historical_average": total_breaches / 30 if total_breaches > 0 else 0
            }
        }
    
    def _assess_compliance_impact(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Assess compliance and regulatory impact."""
        risk_score = results.get("risk_score", 0)
        summary = results.get("summary", {})
        
        compliance_impact = {
            "gdpr_impact": {},
            "ccpa_impact": {},
            "hipaa_impact": {},
            "pci_dss_impact": {}
        }
        
        # GDPR impact
        if summary.get("emails_breached", 0) > 0:
            compliance_impact["gdpr_impact"] = {
                "breach_notification_required": True,
                "timeline": "72 hours",
                "affected_data_subjects": summary.get("emails_breached", 0),
                "data_categories": self._get_data_categories(results)
            }
        
        # CCPA impact
        if risk_score >= 50:
            compliance_impact["ccpa_impact"] = {
                "consumer_notification_required": True,
                "affected_consumers": summary.get("emails_breached", 0)
            }
        
        # HIPAA impact (if health data exposed)
        email_results = results.get("email_results", [])
        health_data_exposed = any(
            "Medical records" in r.get("data_classes_exposed", []) or
            "Health information" in r.get("data_classes_exposed", [])
            for r in email_results
        )
        
        if health_data_exposed:
            compliance_impact["hipaa_impact"] = {
                "breach_notification_required": True,
                "timeline": "60 days",
                "severity": "HIGH"
            }
        
        # PCI DSS impact (if payment data exposed)
        payment_data_exposed = any(
            "Credit cards" in r.get("data_classes_exposed", []) or
            "Payment data" in r.get("data_classes_exposed", [])
            for r in email_results
        )
        
        if payment_data_exposed:
            compliance_impact["pci_dss_impact"] = {
                "compliance_violation": True,
                "severity": "CRITICAL",
                "required_actions": [
                    "Immediate notification to payment processor",
                    "Security assessment required",
                    "Remediation plan must be submitted"
                ]
            }
        
        return compliance_impact
    
    def _get_data_categories(self, results: Dict[str, Any]) -> List[str]:
        """Get all data categories exposed."""
        categories = set()
        
        for email_result in results.get("email_results", []):
            categories.update(email_result.get("data_classes_exposed", []))
        
        return list(categories)
    
    def _generate_detailed_recommendations(self, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate detailed, prioritized recommendations."""
        recommendations = []
        risk_score = results.get("risk_score", 0)
        summary = results.get("summary", {})
        
        # Critical recommendations
        if risk_score >= 75:
            recommendations.append({
                "priority": "CRITICAL",
                "category": "Immediate Response",
                "recommendation": "Implement emergency response plan",
                "rationale": "Risk score indicates critical security exposure",
                "estimated_effort": "High",
                "timeline": "24-48 hours"
            })
        
        # Password recommendations
        if summary.get("passwords_breached", 0) > 0:
            recommendations.append({
                "priority": "CRITICAL",
                "category": "Password Security",
                "recommendation": "Immediately invalidate and reset all breached passwords",
                "rationale": f"{summary['passwords_breached']} password(s) found in breach database",
                "estimated_effort": "Medium",
                "timeline": "Immediately"
            })
            
            recommendations.append({
                "priority": "HIGH",
                "category": "Password Policy",
                "recommendation": "Enforce password breach checking in registration",
                "rationale": "Prevent future use of compromised passwords",
                "estimated_effort": "Low",
                "timeline": "1 week"
            })
        
        # Email recommendations
        if summary.get("emails_breached", 0) > 0:
            recommendations.append({
                "priority": "HIGH",
                "category": "User Notification",
                "recommendation": f"Notify {summary['emails_breached']} affected user(s)",
                "rationale": "Users need to be aware of breach exposure",
                "estimated_effort": "Low",
                "timeline": "48 hours"
            })
            
            recommendations.append({
                "priority": "MEDIUM",
                "category": "Monitoring",
                "recommendation": "Implement continuous breach monitoring",
                "rationale": "Proactive detection of new breaches",
                "estimated_effort": "Medium",
                "timeline": "2 weeks"
            })
        
        # Domain recommendations
        if summary.get("domains_breached", 0) > 0:
            recommendations.append({
                "priority": "HIGH",
                "category": "Organizational Security",
                "recommendation": "Conduct comprehensive security audit",
                "rationale": "Domain breaches indicate organizational risk",
                "estimated_effort": "High",
                "timeline": "1 month"
            })
        
        # General recommendations
        recommendations.extend([
            {
                "priority": "MEDIUM",
                "category": "Security Controls",
                "recommendation": "Enable multi-factor authentication (MFA)",
                "rationale": "Additional security layer for compromised accounts",
                "estimated_effort": "Medium",
                "timeline": "2 weeks"
            },
            {
                "priority": "MEDIUM",
                "category": "Training",
                "recommendation": "Conduct security awareness training",
                "rationale": "Educate users on password security and breach risks",
                "estimated_effort": "Medium",
                "timeline": "1 month"
            }
        ])
        
        return recommendations

