"""
Red Flag Detection Agent - Identifies suspicious patterns and AML red flags.
"""

import json
import logging
import re
from typing import Any, Dict, List

from ..base_agent import BaseAgent
from ...tools.analyzers.pattern_matcher import PatternMatcherTool
from ...tools.analyzers.rule_engine import RuleEngineTool


logger = logging.getLogger(__name__)


class RedFlagDetectionAgent(BaseAgent):
    """
    Detects AML red flags and suspicious patterns.
    
    Identifies:
    - Regulatory rule violations
    - Known suspicious patterns
    - Anomalous behaviors
    - Evidence linking
    """

    def __init__(self, agent_id: str = "redflag_detection", llm_service=None, **kwargs):
        tools = [
            PatternMatcherTool(),
            RuleEngineTool(),
        ]
        
        super().__init__(
            agent_id=agent_id,
            name="Red Flag Detection Agent",
            description="Identifies AML red flags and suspicious patterns",
            tools=tools,
            llm_service=llm_service,
            **kwargs
        )

        # Red flag patterns (in production, load from database/config)
        self.red_flag_patterns = [
            {
                "name": "Structuring",
                "pattern": "multiple_transactions_just_under_threshold",
                "threshold": 10000,
                "severity": "high",
            },
            {
                "name": "Rapid Movement",
                "pattern": "high_velocity_transactions",
                "threshold": 50,
                "severity": "medium",
            },
            {
                "name": "Circular Transactions",
                "pattern": "circular_flow",
                "severity": "high",
            },
            {
                "name": "Large Cash Transactions",
                "pattern": "large_cash_amounts",
                "threshold": 10000,
                "severity": "medium",
            },
        ]

    def get_required_inputs(self) -> List[str]:
        return ["parsed_data"]

    def get_output_schema(self) -> Dict[str, Any]:
        return {
            "red_flags": List[Dict[str, Any]],
            "total_count": int,
            "high_severity_count": int,
            "evidence_links": List[Dict[str, Any]],
        }

    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Detect red flags in the data.
        
        Args:
            input_data: Contains 'parsed_data'
            
        Returns:
            Red flag detection results
        """
        parsed_data = input_data["parsed_data"]
        transactions = parsed_data.get("transactions", [])
        csv_data = parsed_data.get("csv_data", [])
        notes = parsed_data.get("notes", [])

        logger.info(f"Detecting red flags in {len(transactions)} transactions")

        red_flags = []
        evidence_links = []

        # Use LLM for intelligent pattern detection if available
        if self.llm_service:
            try:
                llm_flags = self._detect_red_flags_with_llm(transactions, csv_data, notes)
                red_flags.extend(llm_flags)
            except Exception as e:
                logger.warning(f"LLM red flag detection failed: {e}. Falling back to rule-based detection.")

        # Check each red flag pattern (rule-based fallback or supplement)
        for pattern in self.red_flag_patterns:
            flags = self._check_pattern(transactions, pattern)
            red_flags.extend(flags)

        # Additional checks
        flags, evidence = self._check_regulatory_violations(transactions, csv_data)
        red_flags.extend(flags)
        evidence_links.extend(evidence)

        flags, evidence = self._check_anomalous_behavior(transactions)
        red_flags.extend(flags)
        evidence_links.extend(evidence)

        # Count by severity
        high_severity_count = sum(1 for f in red_flags if f.get("severity") == "high")

        return {
            "red_flags": red_flags,
            "total_count": len(red_flags),
            "high_severity_count": high_severity_count,
            "evidence_links": evidence_links,
        }

    def _check_pattern(self, transactions: List[Dict[str, Any]], pattern: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check for specific red flag pattern."""
        flags = []
        pattern_name = pattern["pattern"]

        if pattern_name == "multiple_transactions_just_under_threshold":
            threshold = pattern.get("threshold", 10000)
            just_under = [
                tx for tx in transactions
                if threshold * 0.9 <= abs(tx.get("amount", 0)) < threshold
            ]
            if len(just_under) >= 3:
                flags.append({
                    "flag_type": pattern["name"],
                    "pattern": pattern_name,
                    "severity": pattern["severity"],
                    "description": f"Multiple transactions just under reporting threshold ({threshold})",
                    "count": len(just_under),
                    "evidence": [tx.get("transaction_id") for tx in just_under[:5]],
                })

        elif pattern_name == "high_velocity_transactions":
            threshold = pattern.get("threshold", 50)
            if len(transactions) > threshold:
                flags.append({
                    "flag_type": pattern["name"],
                    "pattern": pattern_name,
                    "severity": pattern["severity"],
                    "description": f"Unusually high number of transactions ({len(transactions)})",
                    "count": len(transactions),
                    "evidence": [tx.get("transaction_id") for tx in transactions[:10]],
                })

        elif pattern_name == "circular_flow":
            # Check for circular transactions (A->B->A or similar)
            account_graph = {}
            for tx in transactions:
                from_acc = tx.get("from_account")
                to_acc = tx.get("to_account")
                if from_acc and to_acc:
                    if from_acc not in account_graph:
                        account_graph[from_acc] = []
                    account_graph[from_acc].append(to_acc)

            # Detect cycles
            cycles = self._detect_cycles(account_graph)
            if cycles:
                flags.append({
                    "flag_type": pattern["name"],
                    "pattern": pattern_name,
                    "severity": pattern["severity"],
                    "description": "Circular transaction flow detected",
                    "count": len(cycles),
                    "evidence": cycles[:5],
                })

        elif pattern_name == "large_cash_amounts":
            threshold = pattern.get("threshold", 10000)
            large_cash = [
                tx for tx in transactions
                if tx.get("type", "").lower() == "cash" and abs(tx.get("amount", 0)) >= threshold
            ]
            if large_cash:
                flags.append({
                    "flag_type": pattern["name"],
                    "pattern": pattern_name,
                    "severity": pattern["severity"],
                    "description": f"Large cash transactions detected (>= {threshold})",
                    "count": len(large_cash),
                    "evidence": [
                        {
                            "transaction_id": tx.get("transaction_id"),
                            "amount": tx.get("amount"),
                        }
                        for tx in large_cash[:5]
                    ],
                })

        return flags

    def _detect_cycles(self, graph: Dict[str, List[str]]) -> List[List[str]]:
        """Detect cycles in account graph."""
        cycles = []
        visited = set()

        def dfs(node: str, path: List[str]) -> None:
            if node in visited:
                if node in path:
                    # Found a cycle
                    cycle_start = path.index(node)
                    cycle = path[cycle_start:] + [node]
                    cycles.append(cycle)
                return

            visited.add(node)
            path.append(node)

            for neighbor in graph.get(node, []):
                dfs(neighbor, path.copy())

        for node in graph:
            if node not in visited:
                dfs(node, [])

        return cycles

    def _check_regulatory_violations(
        self, transactions: List[Dict], csv_data: List[Dict]
    ) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Check for regulatory rule violations."""
        flags = []
        evidence = []

        # Check for transactions over reporting threshold without proper documentation
        reporting_threshold = 10000
        large_transactions = [
            tx for tx in transactions
            if abs(tx.get("amount", 0)) >= reporting_threshold
        ]

        for tx in large_transactions:
            # Check if transaction has proper documentation
            if not tx.get("description") and not tx.get("metadata"):
                flags.append({
                    "flag_type": "Missing Documentation",
                    "pattern": "regulatory_violation",
                    "severity": "medium",
                    "description": f"Large transaction ({tx.get('amount')}) lacks proper documentation",
                    "transaction_id": tx.get("transaction_id"),
                    "evidence": [tx.get("transaction_id")],
                })
                evidence.append({
                    "type": "transaction",
                    "id": tx.get("transaction_id"),
                    "link": f"transaction_{tx.get('transaction_id')}",
                })

        return flags, evidence

    def _check_anomalous_behavior(self, transactions: List[Dict[str, Any]]) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Check for anomalous behaviors."""
        flags = []
        evidence = []

        if not transactions:
            return flags, evidence

        # Check for unusual timing patterns
        amounts = [abs(tx.get("amount", 0)) for tx in transactions]
        if amounts:
            avg_amount = sum(amounts) / len(amounts)
            std_amount = (sum((a - avg_amount) ** 2 for a in amounts) / len(amounts)) ** 0.5

            # Transactions significantly above average
            outliers = [
                tx for tx in transactions
                if abs(tx.get("amount", 0)) > avg_amount + 3 * std_amount
            ]

            if outliers:
                flags.append({
                    "flag_type": "Anomalous Transaction Amounts",
                    "pattern": "statistical_anomaly",
                    "severity": "medium",
                    "description": f"{len(outliers)} transactions significantly deviate from average",
                    "count": len(outliers),
                    "evidence": [tx.get("transaction_id") for tx in outliers[:5]],
                })

        return flags, evidence

    def _detect_red_flags_with_llm(
        self, transactions: List[Dict], csv_data: List[Dict], notes: List[str]
    ) -> List[Dict[str, Any]]:
        """Use LLM to detect red flags intelligently."""
        # Prepare transaction summary for LLM
        tx_summary = []
        for tx in transactions[:20]:  # Limit to first 20 for context
            tx_summary.append({
                "id": tx.get("transaction_id", "unknown"),
                "amount": tx.get("amount", 0),
                "date": tx.get("date", "unknown"),
                "type": tx.get("type", "unknown"),
                "from": tx.get("from_account", "unknown"),
                "to": tx.get("to_account", "unknown"),
            })
        
        # Prepare prompt
        prompt = f"""You are an AML (Anti-Money Laundering) expert analyzing transaction data for suspicious patterns and red flags.

Transaction Data (sample of {len(transactions)} total transactions):
{str(tx_summary[:10])}

Client Notes:
{chr(10).join(notes[:3]) if notes else "No notes available"}

Analyze this data for AML red flags such as:
- Structuring (transactions just under reporting thresholds)
- Unusual transaction patterns
- Rapid movement of funds
- Circular transactions
- Large cash transactions
- Suspicious counterparties
- Geographic red flags

Provide a JSON-formatted list of red flags found. Each red flag should have:
- "flag_type": type of red flag
- "severity": "high", "medium", or "low"
- "description": clear description of the issue
- "count": number of transactions involved
- "evidence": list of transaction IDs or indicators

Format your response as a JSON array. If no red flags, return empty array [].

Red Flags:"""

        try:
            llm_response = self.llm_service.generate(prompt, max_new_tokens=800, temperature=0.1)
            
            # Try to extract JSON from response
            import json
            import re
            
            # Look for JSON array in response
            json_match = re.search(r'\[.*\]', llm_response, re.DOTALL)
            if json_match:
                flags_data = json.loads(json_match.group())
                # Convert to our format
                red_flags = []
                for flag in flags_data:
                    red_flags.append({
                        "flag_type": flag.get("flag_type", "Unknown"),
                        "pattern": "llm_detected",
                        "severity": flag.get("severity", "medium"),
                        "description": flag.get("description", ""),
                        "count": flag.get("count", 0),
                        "evidence": flag.get("evidence", []),
                    })
                return red_flags
        except Exception as e:
            logger.warning(f"Failed to parse LLM red flag response: {e}")
        
        return []

