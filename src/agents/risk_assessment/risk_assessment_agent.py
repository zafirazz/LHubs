"""
Risk Assessment Agent - Calculates comprehensive risk scores.
"""

import logging
from typing import Any, Dict, List
from datetime import datetime

from ..base_agent import BaseAgent
from ...tools.analyzers.risk_scorer import RiskScorerTool
from ...tools.analyzers.pattern_matcher import PatternMatcherTool


logger = logging.getLogger(__name__)


class RiskAssessmentAgent(BaseAgent):
    """
    Calculates risk scores based on multiple factors.
    
    Considers:
    - Transaction patterns
    - Client profile
    - Historical behavior
    - Regulatory rules
    """

    def __init__(self, agent_id: str = "risk_assessment", **kwargs):
        tools = [
            RiskScorerTool(),
            PatternMatcherTool(),
        ]
        
        super().__init__(
            agent_id=agent_id,
            name="Risk Assessment Agent",
            description="Calculates comprehensive risk scores for AML casefiles",
            tools=tools,
            **kwargs
        )

    def get_required_inputs(self) -> List[str]:
        return ["parsed_data"]

    def get_output_schema(self) -> Dict[str, Any]:
        return {
            "risk_score": float,  # 0-100
            "risk_breakdown": {
                "transaction_risk": float,
                "profile_risk": float,
                "pattern_risk": float,
                "velocity_risk": float,
            },
            "risk_factors": List[Dict[str, Any]],
            "confidence_level": float,  # 0-1
            "recommendations": List[str],
        }

    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate risk score.
        
        Args:
            input_data: Contains 'parsed_data' from parser agent
            
        Returns:
            Risk assessment results
        """
        parsed_data = input_data["parsed_data"]
        transactions = parsed_data.get("transactions", [])
        csv_data = parsed_data.get("csv_data", [])
        notes = parsed_data.get("notes", [])

        logger.info(f"Assessing risk for {len(transactions)} transactions")

        # Calculate individual risk components
        transaction_risk = self._assess_transaction_risk(transactions)
        profile_risk = self._assess_profile_risk(csv_data, notes)
        pattern_risk = self._assess_pattern_risk(transactions)
        velocity_risk = self._assess_velocity_risk(transactions)

        # Weighted overall risk score
        risk_score = (
            transaction_risk * 0.35 +
            profile_risk * 0.25 +
            pattern_risk * 0.25 +
            velocity_risk * 0.15
        )

        # Identify risk factors
        risk_factors = self._identify_risk_factors(
            transactions, csv_data, transaction_risk, profile_risk, pattern_risk, velocity_risk
        )

        # Calculate confidence
        confidence_level = self._calculate_confidence(parsed_data, len(transactions))

        # Generate recommendations
        recommendations = self._generate_recommendations(risk_score, risk_factors)

        return {
            "risk_score": round(risk_score, 2),
            "risk_breakdown": {
                "transaction_risk": round(transaction_risk, 2),
                "profile_risk": round(profile_risk, 2),
                "pattern_risk": round(pattern_risk, 2),
                "velocity_risk": round(velocity_risk, 2),
            },
            "risk_factors": risk_factors,
            "confidence_level": round(confidence_level, 2),
            "recommendations": recommendations,
        }

    def _assess_transaction_risk(self, transactions: List[Dict[str, Any]]) -> float:
        """Assess risk based on transaction characteristics."""
        if not transactions:
            return 0.0

        risk_score = 0.0
        total_amount = sum(abs(tx.get("amount", 0)) for tx in transactions)
        avg_amount = total_amount / len(transactions) if transactions else 0

        # Large amounts
        if avg_amount > 100000:
            risk_score += 30
        elif avg_amount > 50000:
            risk_score += 15

        # High-value transactions
        large_txs = [tx for tx in transactions if abs(tx.get("amount", 0)) > 10000]
        if len(large_txs) > len(transactions) * 0.3:
            risk_score += 20

        # Unusual transaction types
        unusual_types = ["cash", "wire", "cryptocurrency"]
        unusual_count = sum(1 for tx in transactions if tx.get("type", "").lower() in unusual_types)
        if unusual_count > len(transactions) * 0.2:
            risk_score += 15

        return min(risk_score, 100.0)

    def _assess_profile_risk(self, csv_data: List[Dict], notes: List[str]) -> float:
        """Assess risk based on client profile."""
        risk_score = 0.0

        # Check for high-risk indicators in profile
        profile_text = " ".join(str(data) for data in csv_data) + " " + " ".join(notes)
        profile_lower = profile_text.lower()

        high_risk_keywords = ["sanction", "pep", "shell", "offshore", "tax haven"]
        for keyword in high_risk_keywords:
            if keyword in profile_lower:
                risk_score += 20

        # Missing information increases risk
        if not csv_data and not notes:
            risk_score += 30

        return min(risk_score, 100.0)

    def _assess_pattern_risk(self, transactions: List[Dict[str, Any]]) -> float:
        """Assess risk based on transaction patterns."""
        if len(transactions) < 2:
            return 0.0

        risk_score = 0.0

        # Structuring pattern (transactions just under reporting threshold)
        amounts = [abs(tx.get("amount", 0)) for tx in transactions]
        threshold = 10000
        just_under = sum(1 for amt in amounts if threshold * 0.9 <= amt < threshold)
        if just_under > len(transactions) * 0.3:
            risk_score += 40

        # Rapid transactions
        if len(transactions) > 50:
            risk_score += 20

        # Circular transactions (same accounts)
        account_pairs = [(tx.get("from_account"), tx.get("to_account")) for tx in transactions]
        unique_pairs = len(set(account_pairs))
        if len(transactions) > 10 and unique_pairs < len(transactions) * 0.3:
            risk_score += 25

        return min(risk_score, 100.0)

    def _assess_velocity_risk(self, transactions: List[Dict[str, Any]]) -> float:
        """Assess risk based on transaction velocity."""
        if not transactions:
            return 0.0

        risk_score = 0.0

        # Parse dates and calculate velocity
        try:
            dates = [tx.get("date") for tx in transactions if tx.get("date")]
            if len(dates) > 1:
                # High frequency
                if len(transactions) > 100:
                    risk_score += 30
                elif len(transactions) > 50:
                    risk_score += 15
        except:
            pass

        return min(risk_score, 100.0)

    def _identify_risk_factors(
        self,
        transactions: List[Dict],
        csv_data: List[Dict],
        tx_risk: float,
        profile_risk: float,
        pattern_risk: float,
        velocity_risk: float,
    ) -> List[Dict[str, Any]]:
        """Identify specific risk factors."""
        factors = []

        if tx_risk > 50:
            factors.append({
                "factor": "High transaction risk",
                "severity": "high",
                "description": "Transactions show high-risk characteristics",
                "evidence": f"{len(transactions)} transactions analyzed",
            })

        if profile_risk > 50:
            factors.append({
                "factor": "High profile risk",
                "severity": "high",
                "description": "Client profile indicates elevated risk",
                "evidence": "Profile data analysis",
            })

        if pattern_risk > 50:
            factors.append({
                "factor": "Suspicious patterns detected",
                "severity": "medium",
                "description": "Transaction patterns suggest structuring or unusual activity",
                "evidence": f"Pattern analysis of {len(transactions)} transactions",
            })

        if velocity_risk > 50:
            factors.append({
                "factor": "High transaction velocity",
                "severity": "medium",
                "description": "Unusually high frequency of transactions",
                "evidence": f"{len(transactions)} transactions in period",
            })

        return factors

    def _calculate_confidence(self, parsed_data: Dict, transaction_count: int) -> float:
        """Calculate confidence level in assessment."""
        confidence = 0.5  # Base confidence

        # More data = higher confidence
        if transaction_count > 100:
            confidence += 0.3
        elif transaction_count > 50:
            confidence += 0.2
        elif transaction_count > 10:
            confidence += 0.1

        # Complete data = higher confidence
        if parsed_data.get("csv_data") and parsed_data.get("notes"):
            confidence += 0.2

        return min(confidence, 1.0)

    def _generate_recommendations(self, risk_score: float, risk_factors: List[Dict]) -> List[str]:
        """Generate recommendations based on risk assessment."""
        recommendations = []

        if risk_score > 70:
            recommendations.append("Immediate review required - High risk case")
            recommendations.append("Consider enhanced due diligence")
        elif risk_score > 50:
            recommendations.append("Detailed review recommended")
            recommendations.append("Monitor for additional suspicious activity")
        elif risk_score > 30:
            recommendations.append("Standard review process")
        else:
            recommendations.append("Low risk - Routine monitoring")

        if any(f["severity"] == "high" for f in risk_factors):
            recommendations.append("High severity risk factors identified - prioritize review")

        return recommendations

