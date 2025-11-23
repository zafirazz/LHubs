"""
AML Context Rules - Explains detected patterns using AML regulatory context.
"""

import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class AMLContextRule:
    """AML context rule for pattern explanation."""
    pattern_type: str
    risk_level: str  # "high", "medium", "low"
    regulatory_basis: str
    explanation: str
    compliance_implications: List[str]
    recommended_actions: List[str]


class AMLContextRulesEngine:
    """
    Provides AML regulatory context for detected patterns.
    
    Uses established AML rules and regulations to explain patterns
    without inventing new rules or claiming criminal intent.
    """
    
    def __init__(self):
        self.rules = self._initialize_rules()
    
    def _initialize_rules(self) -> Dict[str, AMLContextRule]:
        """Initialize AML context rules based on established regulations."""
        rules = {}
        
        # Fan-out pattern
        rules["fan_out"] = AMLContextRule(
            pattern_type="fan_out",
            risk_level="high",
            regulatory_basis="FINMA Circular 2017/1 - Structuring and Smurfing",
            explanation="Fan-out patterns involve one account sending funds to multiple recipients. This structure can indicate structuring (breaking large amounts into smaller transactions) or smurfing (distributing funds to avoid detection thresholds).",
            compliance_implications=[
                "May indicate structuring to avoid reporting thresholds (typically 10,000 CHF)",
                "Could be used to obscure the origin of funds",
                "Requires enhanced due diligence on source account",
                "May trigger STR (Suspicious Transaction Report) filing requirements"
            ],
            recommended_actions=[
                "Review source account KYC documentation",
                "Verify legitimate business purpose for multiple recipients",
                "Check if transactions are just below reporting thresholds",
                "Consider filing STR if no legitimate explanation"
            ]
        )
        
        # Fan-in pattern
        rules["fan_in"] = AMLContextRule(
            pattern_type="fan_in",
            risk_level="high",
            regulatory_basis="FINMA Circular 2017/1 - Money Collection",
            explanation="Fan-in patterns involve multiple accounts sending funds to one destination. This can indicate money collection, funnel accounts, or layering operations where funds from various sources are consolidated.",
            compliance_implications=[
                "Destination account may be a funnel account",
                "Could indicate layering (second stage of money laundering)",
                "Requires investigation of all source accounts",
                "May indicate coordination between multiple parties"
            ],
            recommended_actions=[
                "Enhanced due diligence on destination account",
                "Review KYC for all source accounts",
                "Verify legitimate business relationships",
                "Monitor for additional suspicious activity"
            ]
        )
        
        # Gather-scatter pattern
        rules["gather_scatter"] = AMLContextRule(
            pattern_type="gather_scatter",
            risk_level="high",
            regulatory_basis="FINMA Circular 2017/1 - Layering and Integration",
            explanation="Gather-scatter patterns involve funds being collected from multiple sources and then distributed to multiple destinations. This is a classic layering technique used to obscure the origin of funds.",
            compliance_implications=[
                "Indicates sophisticated laundering operation",
                "Hub account acts as mixing point",
                "Obscures audit trail",
                "High priority for investigation"
            ],
            recommended_actions=[
                "Immediate STR filing recommended",
                "Freeze hub account pending investigation",
                "Trace all incoming and outgoing funds",
                "Coordinate with law enforcement if confirmed"
            ]
        )
        
        # Scatter-gather pattern
        rules["scatter_gather"] = AMLContextRule(
            pattern_type="scatter_gather",
            risk_level="high",
            regulatory_basis="FINMA Circular 2017/1 - Complex Layering",
            explanation="Scatter-gather patterns involve funds being distributed first, then collected. This reverse layering technique is used to create complex transaction paths that are difficult to trace.",
            compliance_implications=[
                "Indicates sophisticated laundering operation",
                "Creates complex transaction web",
                "Designed to confuse audit trail",
                "High priority for investigation"
            ],
            recommended_actions=[
                "Immediate STR filing recommended",
                "Investigate all intermediate accounts",
                "Trace complete transaction chain",
                "Consider coordination with other financial institutions"
            ]
        )
        
        # Simple cycle pattern
        rules["simple_cycle"] = AMLContextRule(
            pattern_type="simple_cycle",
            risk_level="medium",
            regulatory_basis="FINMA Circular 2017/1 - Circular Transactions",
            explanation="Circular transaction patterns involve funds returning to the origin through a circuitous path. This can indicate round-tripping, false transaction history, or attempts to create artificial transaction volume.",
            compliance_implications=[
                "May indicate round-tripping for tax evasion",
                "Could create false transaction history",
                "May be used to inflate transaction volumes",
                "Requires investigation of circular flow purpose"
            ],
            recommended_actions=[
                "Investigate business purpose of circular flow",
                "Verify if transactions serve legitimate purpose",
                "Check for tax evasion indicators",
                "Consider STR if no legitimate explanation"
            ]
        )
        
        # Bipartite pattern
        rules["bipartite"] = AMLContextRule(
            pattern_type="bipartite",
            risk_level="medium",
            regulatory_basis="FINMA Circular 2017/1 - Structured Transactions",
            explanation="Bipartite patterns show two distinct groups with transactions only between groups. This structure can indicate organized money movement between two parties, potentially for layering or integration purposes.",
            compliance_implications=[
                "May indicate coordinated activity between groups",
                "Could be part of larger laundering scheme",
                "Requires investigation of both groups",
                "May indicate business relationship abuse"
            ],
            recommended_actions=[
                "Investigate relationships between groups",
                "Verify legitimate business purpose",
                "Review KYC for all accounts in both groups",
                "Monitor for additional suspicious patterns"
            ]
        )
        
        # Layered/stack pattern
        rules["layered"] = AMLContextRule(
            pattern_type="layered",
            risk_level="high",
            regulatory_basis="FINMA Circular 2017/1 - Multi-Stage Laundering",
            explanation="Layered structures involve multiple stages of money movement (source → intermediate → sink). This is a classic multi-stage laundering operation designed to obscure the origin and destination of funds.",
            compliance_implications=[
                "Indicates sophisticated laundering operation",
                "Multiple stages obscure audit trail",
                "High priority for investigation",
                "May be part of larger criminal network"
            ],
            recommended_actions=[
                "Immediate STR filing recommended",
                "Investigate all layers of the structure",
                "Trace funds from source to final destination",
                "Coordinate with law enforcement"
            ]
        )
        
        # Random/complex graph pattern
        rules["random_graph"] = AMLContextRule(
            pattern_type="random_graph",
            risk_level="medium",
            regulatory_basis="FINMA Circular 2017/1 - Complex Transaction Networks",
            explanation="Complex transaction networks with high connectivity and no clear pattern can indicate sophisticated laundering operations designed to confuse analysis. The complexity itself may be a red flag.",
            compliance_implications=[
                "Complexity may be intentional to obscure patterns",
                "Requires sophisticated analysis",
                "May indicate large-scale operation",
                "Difficult to trace without advanced tools"
            ],
            recommended_actions=[
                "Use advanced graph analysis tools",
                "Investigate high-connectivity accounts",
                "Look for sub-patterns within complexity",
                "Consider STR if suspicious activity confirmed"
            ]
        )
        
        return rules
    
    def get_rule(self, pattern_type: str) -> Optional[AMLContextRule]:
        """Get AML context rule for a pattern type."""
        return self.rules.get(pattern_type)
    
    def explain_pattern(self, pattern) -> Dict[str, Any]:
        """
        Explain a detected pattern using AML context rules.
        
        Args:
            pattern: Detected pattern (PatternMatch object or dictionary)
            
        Returns:
            Explanation with regulatory context
        """
        # Handle both PatternMatch objects and dictionaries
        if hasattr(pattern, 'pattern_type'):
            # PatternMatch object
            pattern_type = pattern.pattern_type
            accounts_involved = pattern.accounts_involved if hasattr(pattern, 'accounts_involved') else []
            transactions_involved = pattern.transactions_involved if hasattr(pattern, 'transactions_involved') else []
            total_amount = pattern.total_amount if hasattr(pattern, 'total_amount') else 0
            confidence = pattern.confidence if hasattr(pattern, 'confidence') else 0
            severity = pattern.severity if hasattr(pattern, 'severity') else "low"
        else:
            # Dictionary
            pattern_type = pattern.get("pattern_type", "unknown")
            accounts_involved = pattern.get("accounts_involved", [])
            transactions_involved = pattern.get("transactions_involved", [])
            total_amount = pattern.get("total_amount", 0)
            confidence = pattern.get("confidence", 0)
            severity = pattern.get("severity", "low")
        
        rule = self.get_rule(pattern_type)
        
        if not rule:
            return {
                "pattern_type": pattern_type,
                "explanation": "No known AML pattern detected. This pattern type does not match established AML typologies.",
                "risk_level": "unknown",
                "compliance_implications": [],
                "recommended_actions": []
            }
        
        return {
            "pattern_type": pattern_type,
            "risk_level": rule.risk_level,
            "regulatory_basis": rule.regulatory_basis,
            "explanation": rule.explanation,
            "pattern_details": {
                "accounts_involved": len(accounts_involved),
                "transactions_involved": len(transactions_involved),
                "total_amount": total_amount,
                "confidence": confidence
            },
            "compliance_implications": rule.compliance_implications,
            "recommended_actions": rule.recommended_actions,
            "severity": severity
        }
    
    def assess_risk(self, patterns: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Assess overall compliance risk based on detected patterns.
        
        Args:
            patterns: List of detected patterns
            
        Returns:
            Risk assessment summary
        """
        if not patterns:
            return {
                "overall_risk": "low",
                "summary": "No known AML patterns detected in the transaction data.",
                "pattern_count": 0,
                "high_risk_patterns": 0,
                "recommendation": "Continue normal monitoring."
            }
        
        # Handle both PatternMatch objects and dicts
        def get_severity(p):
            return p.severity if hasattr(p, 'severity') else p.get("severity", "low")
        
        high_risk_count = sum(1 for p in patterns if get_severity(p) == "high")
        medium_risk_count = sum(1 for p in patterns if get_severity(p) == "medium")
        low_risk_count = sum(1 for p in patterns if get_severity(p) == "low")
        
        # Determine overall risk
        if high_risk_count >= 3:
            overall_risk = "critical"
            recommendation = "Immediate STR filing recommended. Freeze accounts pending investigation."
        elif high_risk_count >= 1:
            overall_risk = "high"
            recommendation = "Enhanced due diligence required. Consider STR filing."
        elif medium_risk_count >= 5:
            overall_risk = "medium-high"
            recommendation = "Enhanced monitoring required. Review all patterns."
        elif medium_risk_count >= 1:
            overall_risk = "medium"
            recommendation = "Additional review recommended. Monitor for additional activity."
        else:
            overall_risk = "low"
            recommendation = "Continue normal monitoring. Patterns detected but risk is low."
        
        return {
            "overall_risk": overall_risk,
            "summary": f"Detected {len(patterns)} AML patterns: {high_risk_count} high-risk, {medium_risk_count} medium-risk, {low_risk_count} low-risk.",
            "pattern_count": len(patterns),
            "high_risk_patterns": high_risk_count,
            "medium_risk_patterns": medium_risk_count,
            "low_risk_patterns": low_risk_count,
            "recommendation": recommendation
        }

