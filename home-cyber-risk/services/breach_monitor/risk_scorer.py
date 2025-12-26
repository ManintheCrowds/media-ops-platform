"""Risk scoring system for breach prioritization."""

import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from dateutil import parser as date_parser

logger = logging.getLogger(__name__)


class RiskScorer:
    """Calculates risk scores and priorities for breaches."""
    
    # Data class weights (higher = more critical)
    DATA_CLASS_WEIGHTS = {
        "passwords": 10,
        "password": 10,
        "passwords in plaintext": 10,
        "credit cards": 9,
        "credit card data": 9,
        "ssn": 9,
        "social security numbers": 9,
        "bank account numbers": 9,
        "email addresses": 5,
        "email": 5,
        "usernames": 3,
        "username": 3,
        "ip addresses": 2,
        "ip address": 2,
        "names": 2,
        "phone numbers": 2,
        "phone": 2,
        "dates of birth": 1,
        "dob": 1
    }
    
    # Priority thresholds
    CRITICAL_THRESHOLD = 80
    HIGH_THRESHOLD = 60
    MEDIUM_THRESHOLD = 40
    
    def calculate_risk_score(self, breach: Dict[str, Any]) -> int:
        """
        Calculate risk score for a breach.
        
        Args:
            breach: Normalized breach dictionary
        
        Returns:
            Risk score (0-100)
        """
        score = 0
        
        # Data classes weight
        data_classes = breach.get("data_classes", [])
        if isinstance(data_classes, str):
            data_classes = [c.strip() for c in data_classes.split(',')]
        
        max_data_class_score = 0
        for data_class in data_classes:
            data_class_lower = data_class.lower()
            for key, weight in self.DATA_CLASS_WEIGHTS.items():
                if key in data_class_lower:
                    max_data_class_score = max(max_data_class_score, weight)
                    break
        
        score += max_data_class_score * 5  # Scale to 0-50
        
        # Recency factor (recent breaches = higher score)
        breach_date = breach.get("breach_date")
        if breach_date:
            try:
                if isinstance(breach_date, str):
                    breach_date = date_parser.parse(breach_date)
                
                days_ago = (datetime.now(timezone.utc) - breach_date.replace(tzinfo=timezone.utc)).days
                
                if days_ago < 30:
                    score += 30  # Very recent
                elif days_ago < 90:
                    score += 20  # Recent
                elif days_ago < 365:
                    score += 10  # Within year
                else:
                    score += 5  # Older
            except Exception as e:
                logger.debug(f"Could not parse breach date for scoring: {e}")
        else:
            # No date = assume recent for safety
            score += 15
        
        # Verification status (verified = higher confidence)
        is_verified = breach.get("is_verified", True)
        if is_verified:
            score += 10
        else:
            score += 5
        
        # Pwn count factor (widespread = higher exposure)
        pwn_count = breach.get("pwn_count")
        if pwn_count:
            if pwn_count > 1000000:
                score += 10  # Very widespread
            elif pwn_count > 100000:
                score += 7
            elif pwn_count > 10000:
                score += 5
            else:
                score += 2
        
        # Cap at 100
        return min(score, 100)
    
    def classify_priority(self, score: int) -> str:
        """
        Classify breach priority based on risk score.
        
        Args:
            score: Risk score (0-100)
        
        Returns:
            Priority level: Critical, High, Medium, or Low
        """
        if score >= self.CRITICAL_THRESHOLD:
            return "Critical"
        elif score >= self.HIGH_THRESHOLD:
            return "High"
        elif score >= self.MEDIUM_THRESHOLD:
            return "Medium"
        else:
            return "Low"
    
    def assess_impact(self, breach: Dict[str, Any]) -> Dict[str, Any]:
        """
        Assess the impact of a breach.
        
        Args:
            breach: Normalized breach dictionary
        
        Returns:
            Dictionary with impact assessment
        """
        data_classes = breach.get("data_classes", [])
        if isinstance(data_classes, str):
            data_classes = [c.strip() for c in data_classes.split(',')]
        
        impact = {
            "severity": "Low",
            "requires_password_change": False,
            "requires_2fa": False,
            "requires_monitoring": False,
            "exposed_data_types": []
        }
        
        # Check for critical data types
        data_classes_lower = [dc.lower() for dc in data_classes]
        
        if any("password" in dc for dc in data_classes_lower):
            impact["severity"] = "High"
            impact["requires_password_change"] = True
            impact["requires_2fa"] = True
            impact["exposed_data_types"].append("Passwords")
        
        if any("credit" in dc or "card" in dc for dc in data_classes_lower):
            impact["severity"] = "High"
            impact["requires_monitoring"] = True
            impact["exposed_data_types"].append("Payment Information")
        
        if any("ssn" in dc or "social" in dc for dc in data_classes_lower):
            impact["severity"] = "Critical"
            impact["requires_monitoring"] = True
            impact["exposed_data_types"].append("Identity Information")
        
        if any("email" in dc for dc in data_classes_lower):
            impact["exposed_data_types"].append("Email Address")
            if impact["severity"] == "Low":
                impact["severity"] = "Medium"
        
        if any("username" in dc for dc in data_classes_lower):
            impact["exposed_data_types"].append("Username")
        
        return impact
    
    def score_breach(self, breach: Dict[str, Any]) -> Dict[str, Any]:
        """
        Complete risk scoring for a breach.
        
        Args:
            breach: Normalized breach dictionary
        
        Returns:
            Breach dictionary with added risk_score and priority fields
        """
        risk_score = self.calculate_risk_score(breach)
        priority = self.classify_priority(risk_score)
        impact = self.assess_impact(breach)
        
        # Add to breach
        breach["risk_score"] = risk_score
        breach["priority"] = priority
        breach["impact"] = impact
        
        return breach

