"""
AML Analysis Agent - Comprehensive AML compliance analysis with graph-based pattern detection.
"""

import logging
import tempfile
from pathlib import Path
from typing import Dict, List, Any, Optional

from ..base_agent import BaseAgent
from services.excel_loader import ExcelLoader
from services.graph_analysis_service import GraphAnalysisService
from services.aml_context_rules import AMLContextRulesEngine
from services.pdf_report_generator import PDFReportGenerator
from tools.analyzers.graph_pattern_detector import GraphPatternDetector

logger = logging.getLogger(__name__)


class AMLAnalysisAgent(BaseAgent):
    """
    Comprehensive AML Analysis Agent.
    
    Performs:
    1. Excel data loading (accounts + transactions)
    2. Graph construction and analysis
    3. AML pattern detection
    4. AML context rule application
    5. PDF report generation with visualizations
    """
    
    def __init__(
        self,
        agent_id: str = "aml_analysis",
        llm_service=None,
        fan_threshold: int = 3,
        **kwargs
    ):
        super().__init__(
            agent_id=agent_id,
            name="AML Analysis Agent",
            description="Comprehensive AML compliance analysis with graph-based pattern detection",
            llm_service=llm_service,
            **kwargs
        )
        
        self.excel_loader = ExcelLoader()
        self.graph_service = GraphAnalysisService(fan_threshold=fan_threshold)
        self.aml_rules = AMLContextRulesEngine()
        self.pdf_generator = PDFReportGenerator(llm_service=llm_service)
        self.pattern_detector = GraphPatternDetector(fan_threshold=fan_threshold)
    
    def get_required_inputs(self) -> List[str]:
        """Return list of required input field names."""
        return ["excel_file_path"]  # Or "excel_file_bytes" for Streamlit
    
    def get_output_schema(self) -> Dict[str, Any]:
        """Return schema for output data."""
        return {
            "pdf_report_path": str,
            "patterns_detected": List[Dict[str, Any]],
            "risk_assessment": Dict[str, Any],
            "pattern_explanations": List[Dict[str, Any]],
            "summary": str,
        }
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process AML analysis request.
        
        Args:
            input_data: Contains 'excel_file_path' or 'excel_file_bytes' (for Streamlit)
            
        Returns:
            Analysis results with PDF report path
        """
        logger.info("Starting AML analysis...")
        
        # Step 1: Load Excel data
        excel_file_path = input_data.get("excel_file_path")
        excel_file_bytes = input_data.get("excel_file_bytes")
        filename = input_data.get("filename", "upload.xlsx")
        
        if excel_file_bytes:
            # Streamlit upload
            logger.info("Loading Excel data from bytes...")
            data = self.excel_loader.load_from_bytes(excel_file_bytes, filename)
        elif excel_file_path:
            # File path
            logger.info(f"Loading Excel data from file: {excel_file_path}")
            data = self.excel_loader.load_from_file(excel_file_path)
        else:
            raise ValueError("Either 'excel_file_path' or 'excel_file_bytes' must be provided")
        
        accounts = data.get("accounts", [])
        transactions = data.get("transactions", [])
        
        logger.info(f"Loaded {len(accounts)} accounts and {len(transactions)} transactions")
        
        if not transactions:
            return {
                "pdf_report_path": None,
                "patterns_detected": [],
                "risk_assessment": {
                    "overall_risk": "low",
                    "summary": "No transactions found in uploaded data.",
                    "recommendation": "Please verify the Excel file contains transaction data."
                },
                "pattern_explanations": [],
                "summary": "No transactions to analyze.",
                "error": "No transactions found in Excel file"
            }
        
        # Step 2: Detect patterns using graph analysis
        logger.info("Detecting AML patterns...")
        patterns = self.pattern_detector.detect_all_patterns(transactions)
        logger.info(f"Detected {len(patterns)} patterns")
        
        # Step 3: Apply AML context rules
        logger.info("Applying AML context rules...")
        pattern_explanations = []
        for pattern in patterns:
            explanation = self.aml_rules.explain_pattern(pattern)
            pattern_explanations.append(explanation)
        
        # Step 4: Assess overall risk
        risk_assessment = self.aml_rules.assess_risk(patterns)
        
        # Step 5: Generate PDF report
        logger.info("Generating PDF report...")
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "aml_analysis_report.pdf"
            
            # Convert patterns to dict format
            patterns_dict = []
            for pattern in patterns:
                patterns_dict.append({
                    "pattern_type": pattern.pattern_type,
                    "severity": pattern.severity,
                    "description": pattern.description,
                    "accounts_involved": pattern.accounts_involved,
                    "transactions_involved": pattern.transactions_involved,
                    "total_amount": pattern.total_amount,
                    "confidence": pattern.confidence,
                    "metadata": pattern.metadata
                })
            
            pdf_path = self.pdf_generator.generate_report(
                output_path=str(output_path),
                accounts=accounts,
                transactions=transactions,
                patterns=patterns_dict,
                risk_assessment=risk_assessment,
                pattern_explanations=pattern_explanations,
                temp_dir=temp_dir
            )
            
            # Read PDF bytes for return
            pdf_bytes = None
            if Path(pdf_path).exists():
                with open(pdf_path, 'rb') as f:
                    pdf_bytes = f.read()
            
            # Step 6: Apply guardrails and create summary
            summary = self._create_summary_with_guardrails(
                patterns_dict, risk_assessment, pattern_explanations
            )
            
            logger.info("AML analysis completed")
            
            return {
                "pdf_report_path": pdf_path,
                "pdf_bytes": pdf_bytes,  # For Streamlit download
                "patterns_detected": patterns_dict,
                "risk_assessment": risk_assessment,
                "pattern_explanations": pattern_explanations,
                "summary": summary,
                "metadata": {
                    "accounts_analyzed": len(accounts),
                    "transactions_analyzed": len(transactions),
                    "patterns_found": len(patterns_dict)
                }
            }
    
    def _create_summary_with_guardrails(
        self,
        patterns: List[Dict[str, Any]],
        risk_assessment: Dict[str, Any],
        explanations: List[Dict[str, Any]]
    ) -> str:
        """
        Create summary with guardrails applied.
        
        Guardrails:
        - No invented rules
        - No claims of criminal intent
        - If unclear → request missing data
        - If no match → output "No known AML pattern detected."
        """
        if not patterns:
            return "No known AML pattern detected in the transaction data."
        
        summary_parts = []
        
        # Overall risk
        summary_parts.append(f"Analysis Summary:")
        summary_parts.append(f"Overall Risk Level: {risk_assessment.get('overall_risk', 'unknown').upper()}")
        summary_parts.append(f"")
        
        # Pattern count
        summary_parts.append(f"Detected {len(patterns)} AML patterns:")
        high_count = risk_assessment.get('high_risk_patterns', 0)
        medium_count = risk_assessment.get('medium_risk_patterns', 0)
        low_count = risk_assessment.get('low_risk_patterns', 0)
        
        if high_count > 0:
            summary_parts.append(f"- {high_count} high-risk patterns")
        if medium_count > 0:
            summary_parts.append(f"- {medium_count} medium-risk patterns")
        if low_count > 0:
            summary_parts.append(f"- {low_count} low-risk patterns")
        
        summary_parts.append(f"")
        
        # Pattern types (without claiming criminal intent)
        pattern_types = {}
        for pattern in patterns:
            ptype = pattern.get("pattern_type", "unknown")
            pattern_types[ptype] = pattern_types.get(ptype, 0) + 1
        
        summary_parts.append("Pattern Types Detected:")
        for ptype, count in sorted(pattern_types.items(), key=lambda x: x[1], reverse=True):
            summary_parts.append(f"- {ptype.replace('_', ' ').title()}: {count} instances")
        
        summary_parts.append(f"")
        
        # Recommendation (from risk assessment, no invented rules)
        summary_parts.append("Recommendation:")
        summary_parts.append(risk_assessment.get("recommendation", "Continue normal monitoring."))
        
        summary_parts.append(f"")
        summary_parts.append("Note: This analysis is based on established AML typologies as defined by FINMA regulations. ")
        summary_parts.append("Patterns detected do not constitute proof of criminal activity and require further investigation.")
        
        return "\n".join(summary_parts)

