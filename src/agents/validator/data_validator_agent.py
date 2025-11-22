"""
Data Validator Agent - Validates data completeness and quality.
"""

import logging
from typing import Any, Dict, List

from ..base_agent import BaseAgent
from ...tools.validators.cross_reference_checker import CrossReferenceCheckerTool
from ...tools.validators.logic_validator import LogicValidatorTool


logger = logging.getLogger(__name__)


class DataValidatorAgent(BaseAgent):
    """
    Validates data completeness, consistency, and quality.
    
    Checks:
    - Data completeness
    - Schema compliance
    - Data quality metrics
    - Missing data indicators
    """

    def __init__(self, agent_id: str = "data_validator", **kwargs):
        tools = [
            CrossReferenceCheckerTool(),
            LogicValidatorTool(),
        ]
        
        super().__init__(
            agent_id=agent_id,
            name="Data Validator Agent",
            description="Validates data completeness and quality",
            tools=tools,
            **kwargs
        )

    def get_required_inputs(self) -> List[str]:
        return ["parsed_data"]

    def get_output_schema(self) -> Dict[str, Any]:
        return {
            "validation_report": {
                "is_valid": bool,
                "quality_score": float,
                "completeness_score": float,
                "issues": List[Dict[str, Any]],
                "missing_fields": List[str],
            }
        }

    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate parsed data.
        
        Args:
            input_data: Contains 'parsed_data' from parser agent
            
        Returns:
            Validation report
        """
        parsed_data = input_data["parsed_data"]
        transactions = parsed_data.get("transactions", [])
        csv_data = parsed_data.get("csv_data", [])
        notes = parsed_data.get("notes", [])

        logger.info(f"Validating data: {len(transactions)} transactions, {len(csv_data)} CSV records, {len(notes)} notes")

        issues = []
        missing_fields = []

        # Validate transactions
        if transactions:
            tx_issues, tx_missing = self._validate_transactions(transactions)
            issues.extend(tx_issues)
            missing_fields.extend(tx_missing)

        # Validate CSV data
        if csv_data:
            csv_issues, csv_missing = self._validate_csv_data(csv_data)
            issues.extend(csv_issues)
            missing_fields.extend(csv_missing)

        # Calculate scores
        completeness_score = self._calculate_completeness(transactions, csv_data, notes, missing_fields)
        quality_score = self._calculate_quality_score(issues, completeness_score)

        is_valid = quality_score >= 0.7 and len(issues) < 10

        return {
            "validation_report": {
                "is_valid": is_valid,
                "quality_score": round(quality_score, 2),
                "completeness_score": round(completeness_score, 2),
                "issues": issues,
                "missing_fields": list(set(missing_fields)),
            }
        }

    def _validate_transactions(self, transactions: List[Dict[str, Any]]) -> tuple[List[Dict], List[str]]:
        """Validate transaction data."""
        issues = []
        missing_fields = []
        
        required_fields = ["transaction_id", "date", "amount", "from_account", "to_account"]
        
        for idx, tx in enumerate(transactions):
            for field in required_fields:
                if not tx.get(field):
                    missing_fields.append(f"transactions[{idx}].{field}")
                    issues.append({
                        "type": "missing_field",
                        "severity": "medium",
                        "field": f"transactions[{idx}].{field}",
                        "description": f"Transaction {idx} missing required field: {field}",
                    })
            
            # Validate amount
            amount = tx.get("amount")
            if amount is None:
                issues.append({
                    "type": "invalid_amount",
                    "severity": "high",
                    "field": f"transactions[{idx}].amount",
                    "description": f"Transaction {idx} has invalid or missing amount",
                })
            elif not isinstance(amount, (int, float)):
                issues.append({
                    "type": "invalid_amount_type",
                    "severity": "medium",
                    "field": f"transactions[{idx}].amount",
                    "description": f"Transaction {idx} amount is not numeric: {amount}",
                })

        return issues, missing_fields

    def _validate_csv_data(self, csv_data: List[Dict]) -> tuple[List[Dict], List[str]]:
        """Validate CSV data."""
        issues = []
        missing_fields = []
        
        if not csv_data:
            return issues, missing_fields

        # Check for empty records
        for idx, record in enumerate(csv_data):
            if not record or len(record) == 0:
                issues.append({
                    "type": "empty_record",
                    "severity": "low",
                    "field": f"csv_data[{idx}]",
                    "description": f"CSV record {idx} is empty",
                })

        return issues, missing_fields

    def _calculate_completeness(
        self, transactions: List, csv_data: List, notes: List, missing_fields: List
    ) -> float:
        """Calculate data completeness score."""
        total_expected = 0
        total_present = 0

        # Transactions
        if transactions:
            required_per_tx = 5  # transaction_id, date, amount, from_account, to_account
            total_expected += len(transactions) * required_per_tx
            total_present += len(transactions) * required_per_tx - len([f for f in missing_fields if "transactions" in f])

        # CSV data
        if csv_data:
            total_expected += len(csv_data)
            total_present += len(csv_data) - len([f for f in missing_fields if "csv_data" in f])

        # Notes
        if notes:
            total_expected += len(notes)
            total_present += len(notes)

        if total_expected == 0:
            return 0.0

        return total_present / total_expected

    def _calculate_quality_score(self, issues: List[Dict], completeness_score: float) -> float:
        """Calculate overall quality score."""
        # Base score from completeness
        score = completeness_score * 0.7

        # Deduct for issues
        high_severity = sum(1 for i in issues if i.get("severity") == "high")
        medium_severity = sum(1 for i in issues if i.get("severity") == "medium")
        low_severity = sum(1 for i in issues if i.get("severity") == "low")

        score -= (high_severity * 0.1 + medium_severity * 0.05 + low_severity * 0.02)
        score = max(0.0, min(1.0, score))

        return score

