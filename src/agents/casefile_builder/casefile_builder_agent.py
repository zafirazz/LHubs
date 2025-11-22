"""
Casefile Builder Agent - Aggregates all findings into comprehensive casefile.
"""

import logging
from typing import Any, Dict, List
from datetime import datetime

from ..base_agent import BaseAgent
from ...tools.formatters.document_generator import DocumentGeneratorTool
from ...tools.formatters.template_engine import TemplateEngineTool


logger = logging.getLogger(__name__)


class CasefileBuilderAgent(BaseAgent):
    """
    Aggregates all agent outputs into a comprehensive casefile.
    
    Combines:
    - Risk assessment
    - Inconsistencies
    - Red flags
    - Original data
    - Evidence links
    """

    def __init__(self, agent_id: str = "casefile_builder", **kwargs):
        tools = [
            DocumentGeneratorTool(),
            TemplateEngineTool(),
        ]
        
        super().__init__(
            agent_id=agent_id,
            name="Casefile Builder Agent",
            description="Aggregates all findings into comprehensive casefile document",
            tools=tools,
            **kwargs
        )

    def get_required_inputs(self) -> List[str]:
        return ["parsed_data", "risk_assessment", "inconsistencies", "red_flags"]

    def get_output_schema(self) -> Dict[str, Any]:
        return {
            "casefile": {
                "summary": Dict[str, Any],
                "executive_summary": str,
                "detailed_findings": Dict[str, Any],
                "evidence_compilation": List[Dict[str, Any]],
                "metadata": Dict[str, Any],
            },
            "document_path": str,
        }

    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build comprehensive casefile from all agent outputs.
        
        Args:
            input_data: Contains outputs from all previous agents
            
        Returns:
            Complete casefile document
        """
        parsed_data = input_data["parsed_data"]
        risk_assessment = input_data.get("risk_assessment", {})
        inconsistencies = input_data.get("inconsistencies", {})
        red_flags = input_data.get("red_flags", {})

        logger.info("Building comprehensive casefile")

        # Build executive summary
        executive_summary = self._build_executive_summary(
            risk_assessment, inconsistencies, red_flags
        )

        # Build detailed findings
        detailed_findings = self._build_detailed_findings(
            parsed_data, risk_assessment, inconsistencies, red_flags
        )

        # Compile evidence
        evidence_compilation = self._compile_evidence(
            parsed_data, risk_assessment, inconsistencies, red_flags
        )

        # Build summary
        summary = {
            "client_id": input_data.get("client_id", "unknown"),
            "case_id": input_data.get("case_id", "unknown"),
            "generated_at": datetime.utcnow().isoformat(),
            "risk_score": risk_assessment.get("risk_score", 0),
            "total_red_flags": red_flags.get("total_count", 0),
            "total_inconsistencies": inconsistencies.get("total_count", 0),
            "sar_recommendation": input_data.get("sar_recommendation", "pending"),
        }

        # Metadata
        metadata = {
            "agents_executed": [
                "data_parser",
                "data_validator",
                "risk_assessment",
                "inconsistency_detection",
                "redflag_detection",
                "casefile_builder",
            ],
            "processing_time": input_data.get("processing_time", 0),
            "data_sources": len(parsed_data.get("csv_data", [])) + len(parsed_data.get("transactions", [])),
        }

        casefile = {
            "summary": summary,
            "executive_summary": executive_summary,
            "detailed_findings": detailed_findings,
            "evidence_compilation": evidence_compilation,
            "metadata": metadata,
        }

        return {
            "casefile": casefile,
            "document_path": "",  # Will be set when document is saved
        }

    def _build_executive_summary(
        self, risk_assessment: Dict, inconsistencies: Dict, red_flags: Dict
    ) -> str:
        """Build executive summary."""
        risk_score = risk_assessment.get("risk_score", 0)
        red_flag_count = red_flags.get("total_count", 0)
        inconsistency_count = inconsistencies.get("total_count", 0)

        summary = f"""
EXECUTIVE SUMMARY

Risk Assessment: {risk_score}/100
Red Flags Detected: {red_flag_count}
Data Inconsistencies: {inconsistency_count}

"""
        
        if risk_score > 70:
            summary += "This case presents HIGH RISK indicators requiring immediate attention.\n"
        elif risk_score > 50:
            summary += "This case presents MODERATE RISK indicators requiring detailed review.\n"
        else:
            summary += "This case presents LOW RISK indicators suitable for routine monitoring.\n"

        if red_flag_count > 0:
            high_severity = red_flags.get("high_severity_count", 0)
            summary += f"\n{high_severity} high-severity red flags have been identified.\n"

        if inconsistency_count > 0:
            critical = inconsistencies.get("severity_breakdown", {}).get("critical", 0)
            if critical > 0:
                summary += f"\n{critical} critical data inconsistencies detected.\n"

        return summary.strip()

    def _build_detailed_findings(
        self, parsed_data: Dict, risk_assessment: Dict, inconsistencies: Dict, red_flags: Dict
    ) -> Dict[str, Any]:
        """Build detailed findings section."""
        return {
            "risk_assessment": {
                "overall_score": risk_assessment.get("risk_score", 0),
                "breakdown": risk_assessment.get("risk_breakdown", {}),
                "risk_factors": risk_assessment.get("risk_factors", []),
                "recommendations": risk_assessment.get("recommendations", []),
            },
            "red_flags": {
                "total": red_flags.get("total_count", 0),
                "high_severity": red_flags.get("high_severity_count", 0),
                "flags": red_flags.get("red_flags", []),
            },
            "inconsistencies": {
                "total": inconsistencies.get("total_count", 0),
                "breakdown": inconsistencies.get("severity_breakdown", {}),
                "inconsistencies": inconsistencies.get("inconsistencies", []),
                "impact": inconsistencies.get("impact_assessment", ""),
            },
            "data_summary": {
                "transactions": len(parsed_data.get("transactions", [])),
                "csv_records": len(parsed_data.get("csv_data", [])),
                "notes": len(parsed_data.get("notes", [])),
            },
        }

    def _compile_evidence(
        self, parsed_data: Dict, risk_assessment: Dict, inconsistencies: Dict, red_flags: Dict
    ) -> List[Dict[str, Any]]:
        """Compile all evidence with links."""
        evidence = []

        # Evidence from red flags
        for flag in red_flags.get("red_flags", []):
            evidence.append({
                "type": "red_flag",
                "flag_type": flag.get("flag_type"),
                "severity": flag.get("severity"),
                "description": flag.get("description"),
                "evidence_ids": flag.get("evidence", []),
                "links": [f"redflag_{flag.get('flag_type', 'unknown')}"],
            })

        # Evidence from inconsistencies
        for inconsistency in inconsistencies.get("inconsistencies", []):
            evidence.append({
                "type": "inconsistency",
                "inconsistency_type": inconsistency.get("type"),
                "severity": inconsistency.get("severity"),
                "description": inconsistency.get("description"),
                "evidence": inconsistency.get("evidence", {}),
                "links": [f"inconsistency_{inconsistency.get('type', 'unknown')}"],
            })

        # Evidence from risk factors
        for factor in risk_assessment.get("risk_factors", []):
            evidence.append({
                "type": "risk_factor",
                "factor": factor.get("factor"),
                "severity": factor.get("severity"),
                "description": factor.get("description"),
                "evidence": factor.get("evidence", ""),
                "links": [f"risk_{factor.get('factor', 'unknown')}"],
            })

        return evidence

