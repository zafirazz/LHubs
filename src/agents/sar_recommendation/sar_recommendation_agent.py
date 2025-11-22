"""
SAR Recommendation Agent - Generates final SAR filing recommendation.
"""

import logging
from typing import Any, Dict, List

from ..base_agent import BaseAgent
from ...tools.analyzers.decision_engine import DecisionEngineTool
from ...tools.analyzers.regulatory_checker import RegulatoryCheckerTool


logger = logging.getLogger(__name__)


class SARRecommendationAgent(BaseAgent):
    """
    Generates final SAR (Suspicious Activity Report) filing recommendation.
    
    Considers:
    - All evidence and findings
    - Regulatory thresholds
    - Filing criteria
    - Confidence levels
    """

    def __init__(self, agent_id: str = "sar_recommendation", llm_service=None, **kwargs):
        tools = [
            DecisionEngineTool(),
            RegulatoryCheckerTool(),
        ]
        
        super().__init__(
            agent_id=agent_id,
            name="SAR Recommendation Agent",
            description="Generates final SAR filing recommendation based on all findings",
            tools=tools,
            llm_service=llm_service,
            **kwargs
        )

        # Regulatory thresholds (in production, load from config/DB)
        self.regulatory_thresholds = {
            "mandatory_filing_risk_score": 70,
            "mandatory_filing_red_flags": 3,
            "mandatory_filing_critical_inconsistencies": 2,
        }

    def get_required_inputs(self) -> List[str]:
        return ["casefile"]

    def get_output_schema(self) -> Dict[str, Any]:
        return {
            "recommendation": str,  # "yes", "no", "maybe"
            "confidence": float,  # 0-1
            "rationale": str,
            "filing_priority": str,  # "immediate", "high", "medium", "low"
            "regulatory_justification": Dict[str, Any],
        }

    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate SAR recommendation.
        
        Args:
            input_data: Contains 'casefile' from casefile builder
            
        Returns:
            SAR recommendation with rationale
        """
        casefile = input_data["casefile"]
        summary = casefile.get("summary", {})
        detailed_findings = casefile.get("detailed_findings", {})

        logger.info("Generating SAR recommendation")

        risk_score = summary.get("risk_score", 0)
        red_flag_count = summary.get("total_red_flags", 0)
        inconsistency_count = summary.get("total_inconsistencies", 0)

        # Check regulatory criteria
        regulatory_check = self._check_regulatory_criteria(
            risk_score, red_flag_count, inconsistency_count, detailed_findings
        )

        # Make recommendation
        recommendation, confidence = self._make_recommendation(
            risk_score, red_flag_count, inconsistency_count, regulatory_check
        )

        # Generate rationale
        rationale = self._generate_rationale(
            recommendation, risk_score, red_flag_count, inconsistency_count, regulatory_check
        )

        # Determine filing priority
        filing_priority = self._determine_priority(
            recommendation, risk_score, red_flag_count
        )

        return {
            "recommendation": recommendation,
            "confidence": confidence,
            "rationale": rationale,
            "filing_priority": filing_priority,
            "regulatory_justification": regulatory_check,
        }

    def _check_regulatory_criteria(
        self, risk_score: float, red_flag_count: int, inconsistency_count: int, detailed_findings: Dict
    ) -> Dict[str, Any]:
        """Check if case meets regulatory filing criteria."""
        criteria_met = []
        criteria_not_met = []

        # Risk score threshold
        if risk_score >= self.regulatory_thresholds["mandatory_filing_risk_score"]:
            criteria_met.append({
                "criterion": "Risk Score Threshold",
                "value": risk_score,
                "threshold": self.regulatory_thresholds["mandatory_filing_risk_score"],
                "met": True,
            })
        else:
            criteria_not_met.append({
                "criterion": "Risk Score Threshold",
                "value": risk_score,
                "threshold": self.regulatory_thresholds["mandatory_filing_risk_score"],
                "met": False,
            })

        # Red flag threshold
        if red_flag_count >= self.regulatory_thresholds["mandatory_filing_red_flags"]:
            criteria_met.append({
                "criterion": "Red Flag Count",
                "value": red_flag_count,
                "threshold": self.regulatory_thresholds["mandatory_filing_red_flags"],
                "met": True,
            })
        else:
            criteria_not_met.append({
                "criterion": "Red Flag Count",
                "value": red_flag_count,
                "threshold": self.regulatory_thresholds["mandatory_filing_red_flags"],
                "met": False,
            })

        # Critical inconsistencies
        critical_inconsistencies = detailed_findings.get("inconsistencies", {}).get(
            "breakdown", {}
        ).get("critical", 0)
        
        if critical_inconsistencies >= self.regulatory_thresholds["mandatory_filing_critical_inconsistencies"]:
            criteria_met.append({
                "criterion": "Critical Inconsistencies",
                "value": critical_inconsistencies,
                "threshold": self.regulatory_thresholds["mandatory_filing_critical_inconsistencies"],
                "met": True,
            })
        else:
            criteria_not_met.append({
                "criterion": "Critical Inconsistencies",
                "value": critical_inconsistencies,
                "threshold": self.regulatory_thresholds["mandatory_filing_critical_inconsistencies"],
                "met": False,
            })

        return {
            "criteria_met": criteria_met,
            "criteria_not_met": criteria_not_met,
            "mandatory_filing": len(criteria_met) >= 2,  # At least 2 criteria must be met
        }

    def _make_recommendation(
        self, risk_score: float, red_flag_count: int, inconsistency_count: int, regulatory_check: Dict
    ) -> tuple[str, float]:
        """Make SAR filing recommendation."""
        mandatory_filing = regulatory_check.get("mandatory_filing", False)
        criteria_met_count = len(regulatory_check.get("criteria_met", []))

        if mandatory_filing or criteria_met_count >= 2:
            return "yes", 0.9
        elif criteria_met_count == 1:
            if risk_score > 60 or red_flag_count >= 2:
                return "yes", 0.7
            else:
                return "maybe", 0.5
        elif risk_score > 50 or red_flag_count >= 1:
            return "maybe", 0.6
        else:
            return "no", 0.8

    def _generate_rationale(
        self, recommendation: str, risk_score: float, red_flag_count: int,
        inconsistency_count: int, regulatory_check: Dict
    ) -> str:
        """Generate detailed rationale for recommendation."""
        # Use LLM for intelligent rationale if available
        if self.llm_service:
            try:
                criteria_met = regulatory_check.get("criteria_met", [])
                criteria_not_met = regulatory_check.get("criteria_not_met", [])
                
                prompt = f"""You are an AML compliance expert providing a SAR (Suspicious Activity Report) filing recommendation.

Case Details:
- Risk Score: {risk_score}/100
- Red Flags Detected: {red_flag_count}
- Data Inconsistencies: {inconsistency_count}

Regulatory Criteria Met: {len(criteria_met)}
Regulatory Criteria Not Met: {len(criteria_not_met)}

Recommendation: {recommendation.upper()}

Create a professional, detailed rationale (2-3 paragraphs) explaining:
1. Why this recommendation was made
2. Key evidence supporting the decision
3. Regulatory justification
4. Next steps or considerations

Use professional AML compliance language. Be specific and cite the risk factors.

Rationale:"""

                llm_rationale = self.llm_service.generate(prompt, max_new_tokens=500, temperature=0.2)
                if llm_rationale and len(llm_rationale.strip()) > 100:
                    return f"SAR Filing Recommendation: {recommendation.upper()}\n\n{llm_rationale.strip()}"
            except Exception as e:
                logger.warning(f"LLM rationale generation failed: {e}. Falling back to template.")

        # Fallback to template-based rationale
        rationale = f"SAR Filing Recommendation: {recommendation.upper()}\n\n"
        
        rationale += f"Risk Score: {risk_score}/100\n"
        rationale += f"Red Flags Detected: {red_flag_count}\n"
        rationale += f"Inconsistencies: {inconsistency_count}\n\n"

        if recommendation == "yes":
            rationale += "RECOMMENDATION: FILE SAR\n\n"
            rationale += "Justification:\n"
            criteria_met = regulatory_check.get("criteria_met", [])
            for criterion in criteria_met:
                rationale += f"- {criterion['criterion']}: {criterion['value']} (threshold: {criterion['threshold']})\n"
            
            if risk_score > 70:
                rationale += f"- High risk score ({risk_score}) indicates significant AML concerns\n"
            if red_flag_count >= 3:
                rationale += f"- Multiple red flags ({red_flag_count}) suggest suspicious activity patterns\n"

        elif recommendation == "maybe":
            rationale += "RECOMMENDATION: REVIEW AND CONSIDER FILING\n\n"
            rationale += "Justification:\n"
            rationale += "- Some risk indicators present but below mandatory filing thresholds\n"
            rationale += "- Additional investigation may be warranted\n"
            rationale += "- Monitor for additional suspicious activity\n"

        else:
            rationale += "RECOMMENDATION: DO NOT FILE SAR\n\n"
            rationale += "Justification:\n"
            rationale += "- Risk indicators are below filing thresholds\n"
            rationale += "- No mandatory filing criteria met\n"
            rationale += "- Continue routine monitoring\n"

        return rationale

    def _determine_priority(
        self, recommendation: str, risk_score: float, red_flag_count: int
    ) -> str:
        """Determine filing priority."""
        if recommendation != "yes":
            return "low"

        if risk_score > 80 or red_flag_count >= 5:
            return "immediate"
        elif risk_score > 70 or red_flag_count >= 3:
            return "high"
        else:
            return "medium"

