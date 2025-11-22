"""
Inconsistency Detection Agent - Identifies discrepancies and contradictions.
"""

import json
import logging
import re
from typing import Any, Dict, List

from ..base_agent import BaseAgent
from ...tools.validators.cross_reference_checker import CrossReferenceCheckerTool
from ...tools.validators.logic_validator import LogicValidatorTool


logger = logging.getLogger(__name__)


class InconsistencyDetectionAgent(BaseAgent):
    """
    Detects inconsistencies and contradictions in client data.
    
    Identifies:
    - Cross-source discrepancies
    - Temporal inconsistencies
    - Logical contradictions
    - Data conflicts
    """

    def __init__(self, agent_id: str = "inconsistency_detection", llm_service=None, **kwargs):
        tools = [
            CrossReferenceCheckerTool(),
            LogicValidatorTool(),
        ]
        
        super().__init__(
            agent_id=agent_id,
            name="Inconsistency Detection Agent",
            description="Identifies discrepancies and contradictions in client data",
            tools=tools,
            llm_service=llm_service,
            **kwargs
        )

    def get_required_inputs(self) -> List[str]:
        return ["parsed_data"]

    def get_output_schema(self) -> Dict[str, Any]:
        return {
            "inconsistencies": List[Dict[str, Any]],
            "total_count": int,
            "severity_breakdown": {
                "critical": int,
                "high": int,
                "medium": int,
                "low": int,
            },
            "impact_assessment": str,
        }

    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Detect inconsistencies in the data.
        
        Args:
            input_data: Contains 'parsed_data'
            
        Returns:
            Inconsistency detection results
        """
        parsed_data = input_data["parsed_data"]
        transactions = parsed_data.get("transactions", [])
        csv_data = parsed_data.get("csv_data", [])
        notes = parsed_data.get("notes", [])

        logger.info(f"Detecting inconsistencies across {len(transactions)} transactions and {len(csv_data)} CSV records")

        inconsistencies = []

        # Use LLM for intelligent inconsistency detection if available
        if self.llm_service:
            try:
                llm_inconsistencies = self._detect_inconsistencies_with_llm(transactions, csv_data, notes)
                inconsistencies.extend(llm_inconsistencies)
            except Exception as e:
                logger.warning(f"LLM inconsistency detection failed: {e}. Falling back to rule-based detection.")

        # Cross-reference checks
        inconsistencies.extend(self._check_cross_references(transactions, csv_data, notes))

        # Temporal consistency checks
        inconsistencies.extend(self._check_temporal_consistency(transactions))

        # Logical consistency checks
        inconsistencies.extend(self._check_logical_consistency(transactions, csv_data))

        # Data conflict checks
        inconsistencies.extend(self._check_data_conflicts(csv_data, notes))

        # Calculate severity breakdown
        severity_breakdown = {
            "critical": sum(1 for i in inconsistencies if i.get("severity") == "critical"),
            "high": sum(1 for i in inconsistencies if i.get("severity") == "high"),
            "medium": sum(1 for i in inconsistencies if i.get("severity") == "medium"),
            "low": sum(1 for i in inconsistencies if i.get("severity") == "low"),
        }

        # Impact assessment
        impact_assessment = self._assess_impact(inconsistencies)

        return {
            "inconsistencies": inconsistencies,
            "total_count": len(inconsistencies),
            "severity_breakdown": severity_breakdown,
            "impact_assessment": impact_assessment,
        }

    def _check_cross_references(
        self, transactions: List[Dict], csv_data: List[Dict], notes: List[str]
    ) -> List[Dict[str, Any]]:
        """Check for discrepancies across different data sources."""
        inconsistencies = []

        # Extract account information from different sources
        csv_accounts = set()
        for record in csv_data:
            for key, value in record.items():
                if "account" in key.lower() and value:
                    csv_accounts.add(str(value))

        tx_accounts = set()
        for tx in transactions:
            if tx.get("from_account"):
                tx_accounts.add(tx["from_account"])
            if tx.get("to_account"):
                tx_accounts.add(tx["to_account"])

        # Check if accounts in transactions match CSV data
        if csv_accounts and tx_accounts:
            missing_in_csv = tx_accounts - csv_accounts
            if missing_in_csv:
                inconsistencies.append({
                    "type": "cross_reference",
                    "severity": "medium",
                    "description": f"Accounts in transactions not found in CSV data: {list(missing_in_csv)[:5]}",
                    "evidence": {
                        "source": "transaction_accounts",
                        "missing": list(missing_in_csv)[:5],
                    },
                })

        # Check amount totals
        if transactions and csv_data:
            tx_total = sum(abs(tx.get("amount", 0)) for tx in transactions)
            
            # Try to find total in CSV
            csv_total = None
            for record in csv_data:
                for key, value in record.items():
                    if "total" in key.lower() or "balance" in key.lower():
                        try:
                            csv_total = float(value)
                            break
                        except:
                            pass

            if csv_total is not None and abs(tx_total - csv_total) > tx_total * 0.1:
                inconsistencies.append({
                    "type": "amount_mismatch",
                    "severity": "high",
                    "description": f"Transaction total ({tx_total}) differs significantly from CSV total ({csv_total})",
                    "evidence": {
                        "transaction_total": tx_total,
                        "csv_total": csv_total,
                        "difference": abs(tx_total - csv_total),
                    },
                })

        return inconsistencies

    def _check_temporal_consistency(self, transactions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Check for temporal inconsistencies."""
        inconsistencies = []

        if not transactions:
            return inconsistencies

        # Sort transactions by date if possible
        dated_transactions = []
        for tx in transactions:
            date = tx.get("date")
            if date:
                try:
                    # Try to parse date (simplified - in production use proper date parsing)
                    dated_transactions.append((date, tx))
                except:
                    pass

        if len(dated_transactions) < 2:
            return inconsistencies

        # Check for future-dated transactions
        # (In production, compare against actual current date)
        for date, tx in dated_transactions:
            # Simplified check - in production use proper date comparison
            inconsistencies.append({
                "type": "temporal",
                "severity": "low",
                "description": "Temporal consistency check (placeholder - implement proper date validation)",
                "evidence": {
                    "transaction_id": tx.get("transaction_id"),
                    "date": date,
                },
            })

        return inconsistencies

    def _check_logical_consistency(
        self, transactions: List[Dict], csv_data: List[Dict]
    ) -> List[Dict[str, Any]]:
        """Check for logical contradictions."""
        inconsistencies = []

        # Check for negative balances that shouldn't exist
        account_balances = {}
        for tx in transactions:
            from_acc = tx.get("from_account")
            to_acc = tx.get("to_account")
            amount = tx.get("amount", 0)

            if from_acc:
                account_balances[from_acc] = account_balances.get(from_acc, 0) - amount
            if to_acc:
                account_balances[to_acc] = account_balances.get(to_acc, 0) + amount

        # Check for logical issues
        for account, balance in account_balances.items():
            if balance < -1000000:  # Unrealistic negative balance
                inconsistencies.append({
                    "type": "logical",
                    "severity": "high",
                    "description": f"Account {account} has unrealistic negative balance: {balance}",
                    "evidence": {
                        "account": account,
                        "calculated_balance": balance,
                    },
                })

        return inconsistencies

    def _check_data_conflicts(self, csv_data: List[Dict], notes: List[str]) -> List[Dict[str, Any]]:
        """Check for conflicts between CSV data and notes."""
        inconsistencies = []

        # Extract key information from notes
        notes_text = " ".join(notes).lower()

        # Check for conflicting information
        # (Simplified - in production use NLP to extract structured info from notes)
        for record in csv_data:
            for key, value in record.items():
                if value and isinstance(value, (int, float)):
                    # Check if notes mention different values
                    # This is a placeholder - implement proper NLP extraction
                    pass

        return inconsistencies

    def _assess_impact(self, inconsistencies: List[Dict[str, Any]]) -> str:
        """Assess overall impact of inconsistencies."""
        if not inconsistencies:
            return "No inconsistencies detected. Data appears consistent."

        critical_count = sum(1 for i in inconsistencies if i.get("severity") == "critical")
        high_count = sum(1 for i in inconsistencies if i.get("severity") == "high")

        if critical_count > 0:
            return f"Critical inconsistencies detected ({critical_count}). Data integrity compromised. Manual review required."
        elif high_count > 3:
            return f"Multiple high-severity inconsistencies ({high_count}). Significant data quality issues. Review recommended."
        elif high_count > 0:
            return f"High-severity inconsistencies detected ({high_count}). Data quality concerns identified."
        else:
            return "Minor inconsistencies detected. Data quality is generally acceptable."

    def _detect_inconsistencies_with_llm(
        self, transactions: List[Dict], csv_data: List[Dict], notes: List[str]
    ) -> List[Dict[str, Any]]:
        """Use LLM to detect inconsistencies intelligently."""
        # Prepare data summary
        tx_summary = []
        for tx in transactions[:15]:  # Limit for context
            tx_summary.append({
                "id": tx.get("transaction_id", "unknown"),
                "amount": tx.get("amount", 0),
                "date": tx.get("date", "unknown"),
                "from": tx.get("from_account", "unknown"),
                "to": tx.get("to_account", "unknown"),
            })
        
        csv_summary = str(csv_data[:5]) if csv_data else "No CSV data"
        notes_text = "\n".join(notes[:3]) if notes else "No notes"
        
        prompt = f"""You are a data quality expert analyzing financial data for inconsistencies and discrepancies.

Transaction Data (sample):
{str(tx_summary[:10])}

CSV Data (sample):
{csv_summary}

Client Notes:
{notes_text}

Analyze this data for inconsistencies such as:
- Mismatched account information across sources
- Amount discrepancies
- Date inconsistencies
- Missing or conflicting data
- Logical contradictions

Provide a JSON-formatted list of inconsistencies. Each should have:
- "type": type of inconsistency
- "severity": "critical", "high", "medium", or "low"
- "description": clear description
- "evidence": object with relevant data points

Format as JSON array. If none found, return [].

Inconsistencies:"""

        try:
            llm_response = self.llm_service.generate(prompt, max_new_tokens=600, temperature=0.1)
            
            import json
            import re
            
            json_match = re.search(r'\[.*\]', llm_response, re.DOTALL)
            if json_match:
                inconsistencies_data = json.loads(json_match.group())
                inconsistencies = []
                for inc in inconsistencies_data:
                    inconsistencies.append({
                        "type": inc.get("type", "unknown"),
                        "severity": inc.get("severity", "medium"),
                        "description": inc.get("description", ""),
                        "evidence": inc.get("evidence", {}),
                    })
                return inconsistencies
        except Exception as e:
            logger.warning(f"Failed to parse LLM inconsistency response: {e}")
        
        return []

