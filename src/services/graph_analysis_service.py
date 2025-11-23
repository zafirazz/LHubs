"""
Graph Analysis Service - Pre-computes graph pattern detection results.
Integrates with ContextService to provide graph-based AML pattern detection.
"""

import logging
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd

from tools.analyzers.graph_pattern_detector import GraphPatternDetector, PatternMatch

logger = logging.getLogger(__name__)


class GraphAnalysisService:
    """
    Service for graph-based AML pattern detection.
    
    Pre-computes pattern detection results from transaction data
    and provides them to the compliance agent.
    """
    
    def __init__(
        self,
        data_dir: str = "/workspace/data",
        patterns_file: str = "./data/graph_patterns.json",
        fan_threshold: int = 3,  # Lowered from 5 for better detection
        amount_threshold: float = 10000.0,
    ):
        self.data_dir = Path(data_dir)
        self.patterns_file = Path(patterns_file)
        self.detector = GraphPatternDetector(
            fan_threshold=fan_threshold,
            amount_threshold=amount_threshold
        )
        self._patterns: Optional[List[Dict[str, Any]]] = None
    
    def load_transactions(self) -> List[Dict[str, Any]]:
        """Load transactions from CSV file."""
        transactions_file = self.data_dir / "transactions.csv"
        
        if not transactions_file.exists():
            logger.warning(f"Transactions file not found: {transactions_file}")
            return []
        
        try:
            # Read transactions (sample for performance)
            # Limit to 20k transactions for faster pattern detection
            df = pd.read_csv(transactions_file, nrows=20000)
            logger.info(f"Loaded {len(df)} transactions for graph analysis")
            
            # Normalize to standard format
            # CSV format: Each row is either debit or credit, need to reconstruct transfers
            transactions = []
            for _, row in df.iterrows():
                transaction_id = str(row.get("Transaction ID", row.get("Transaction_ID", "")))
                account_id = str(row.get("Account ID", "")).strip()
                debit_credit = str(row.get("Debit/Credit", "")).lower().strip()
                amount = float(row.get("Amount", 0))
                currency = str(row.get("Currency", "CHF"))
                date = str(row.get("Date", row.get("Transaction_Date", "")))
                transfer_type = str(row.get("Transfer_Type", ""))
                
                # Handle NaN values properly
                counterparty_account = row.get("counterparty_Account_ID", "")
                if pd.isna(counterparty_account):
                    counterparty_account = ""
                else:
                    counterparty_account = str(counterparty_account).strip()
                
                ext_counterparty = row.get("ext_counterparty_Account_ID", "")
                if pd.isna(ext_counterparty):
                    ext_counterparty = ""
                else:
                    ext_counterparty = str(ext_counterparty).strip()
                
                # Skip if no account ID
                if not account_id or account_id == "nan":
                    continue
                
                # Determine from_account and to_account based on debit/credit
                if debit_credit == "debit":
                    # Money going out from this account
                    from_account = account_id
                    # Use counterparty if available, otherwise external counterparty
                    to_account = counterparty_account if counterparty_account else ext_counterparty
                elif debit_credit == "credit":
                    # Money coming into this account
                    to_account = account_id
                    # Use counterparty if available, otherwise external counterparty
                    from_account = counterparty_account if counterparty_account else ext_counterparty
                else:
                    # Unknown direction, skip
                    continue
                
                # Skip if we don't have both accounts or if they're the same
                if not from_account or not to_account or from_account == "nan" or to_account == "nan":
                    continue
                if from_account == to_account:
                    continue
                
                tx = {
                    "transaction_id": transaction_id,
                    "from_account": from_account,
                    "to_account": to_account,
                    "amount": amount,
                    "currency": currency,
                    "date": date,
                    "type": transfer_type,
                    "description": f"{transfer_type} transaction",
                }
                transactions.append(tx)
            
            return transactions
            
        except Exception as e:
            logger.error(f"Error loading transactions: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def detect_patterns(self, force_recompute: bool = False) -> List[Dict[str, Any]]:
        """
        Detect graph patterns in transaction data.
        
        Args:
            force_recompute: If True, recompute even if cached patterns exist
            
        Returns:
            List of detected patterns as dictionaries
        """
        # Load cached patterns if available
        if not force_recompute and self.patterns_file.exists():
            try:
                with open(self.patterns_file, 'r', encoding='utf-8') as f:
                    patterns = json.load(f)
                logger.info(f"Loaded {len(patterns)} cached graph patterns")
                self._patterns = patterns
                return patterns
            except Exception as e:
                logger.warning(f"Error loading cached patterns: {e}, recomputing...")
        
        # Load transactions and detect patterns
        logger.info("Detecting graph patterns in transaction data...")
        transactions = self.load_transactions()
        
        if not transactions:
            logger.warning("No transactions available for pattern detection")
            return []
        
        # Run pattern detection
        logger.info(f"Running pattern detection on {len(transactions)} transactions...")
        pattern_matches = self.detector.detect_all_patterns(transactions)
        logger.info(f"Pattern detection completed: {len(pattern_matches)} patterns found")
        
        # Convert to dictionaries for JSON serialization
        patterns = []
        for match in pattern_matches:
            patterns.append({
                "pattern_type": match.pattern_type,
                "severity": match.severity,
                "description": match.description,
                "accounts_involved": match.accounts_involved,
                "transactions_involved": match.transactions_involved[:20],  # Limit for storage
                "total_amount": match.total_amount,
                "time_window_days": match.time_window_days,
                "confidence": match.confidence,
                "metadata": match.metadata
            })
        
        # Cache results
        self._patterns = patterns
        self.save_patterns(patterns)
        
        logger.info(f"Detected {len(patterns)} graph patterns")
        return patterns
    
    def save_patterns(self, patterns: List[Dict[str, Any]]):
        """Save detected patterns to JSON file."""
        self.patterns_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(self.patterns_file, 'w', encoding='utf-8') as f:
            json.dump(patterns, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved {len(patterns)} patterns to {self.patterns_file}")
    
    def get_patterns_for_query(self, query: str) -> List[Dict[str, Any]]:
        """
        Get relevant patterns for a query.
        
        Args:
            query: Compliance query
            
        Returns:
            List of relevant patterns
        """
        if self._patterns is None:
            self.detect_patterns()
        
        if not self._patterns:
            return []
        
        query_lower = query.lower()
        
        # Filter patterns based on query keywords
        relevant_patterns = []
        
        # Keywords that indicate pattern interest
        pattern_keywords = {
            "fan": ["fan", "multiple", "many accounts"],
            "cycle": ["cycle", "circular", "round", "loop"],
            "layered": ["layer", "stack", "multi", "tier"],
            "bipartite": ["bipartite", "two groups", "groups"],
            "scatter": ["scatter", "gather", "distribute"],
            "complex": ["complex", "random", "interconnected"]
        }
        
        for pattern in self._patterns:
            pattern_type = pattern.get("pattern_type", "")
            severity = pattern.get("severity", "low")
            
            # Always include high severity patterns
            if severity == "high":
                relevant_patterns.append(pattern)
                continue
            
            # Check if query mentions pattern-related terms
            for keyword_group, keywords in pattern_keywords.items():
                if keyword_group in pattern_type:
                    if any(kw in query_lower for kw in keywords):
                        relevant_patterns.append(pattern)
                        break
        
        # If no specific match, return top patterns by severity
        if not relevant_patterns:
            relevant_patterns = sorted(
                self._patterns,
                key=lambda p: ({"high": 0, "medium": 1, "low": 2}[p.get("severity", "low")], -p.get("confidence", 0))
            )[:5]  # Top 5
        
        return relevant_patterns
    
    def format_patterns_for_prompt(self, patterns: List[Dict[str, Any]]) -> str:
        """Format patterns for inclusion in LLM prompt."""
        if not patterns:
            return "No graph-based laundering patterns detected in the transaction data."
        
        formatted = []
        formatted.append("GRAPH-BASED AML PATTERN DETECTION RESULTS:")
        formatted.append("=" * 70)
        
        for i, pattern in enumerate(patterns, 1):
            formatted.append(f"\n[Pattern {i}]")
            formatted.append(f"Type: {pattern.get('pattern_type', 'unknown').upper().replace('_', '-')}")
            formatted.append(f"Severity: {pattern.get('severity', 'unknown').upper()}")
            formatted.append(f"Confidence: {pattern.get('confidence', 0):.1%}")
            formatted.append(f"Description: {pattern.get('description', 'N/A')}")
            formatted.append(f"Accounts Involved: {len(pattern.get('accounts_involved', []))} accounts")
            formatted.append(f"Total Amount: {pattern.get('total_amount', 0):,.2f} CHF")
            formatted.append(f"Transactions: {len(pattern.get('transactions_involved', []))} transactions")
            
            metadata = pattern.get('metadata', {})
            if metadata:
                formatted.append(f"Details: {json.dumps(metadata, indent=2)}")
        
        return "\n".join(formatted)


if __name__ == "__main__":
    """Run pattern detection and save results."""
    import sys
    from pathlib import Path
    
    # Add src to path for imports
    project_root = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(project_root / "src"))
    
    logging.basicConfig(level=logging.INFO)
    
    data_dir = "/workspace/data"
    if len(sys.argv) > 1:
        data_dir = sys.argv[1]
    
    service = GraphAnalysisService(data_dir=data_dir)
    patterns = service.detect_patterns(force_recompute=True)
    
    print(f"\n✓ Detected {len(patterns)} graph patterns")
    print(f"✓ Saved to: {service.patterns_file}")
    
    # Print summary
    by_type = {}
    by_severity = {"high": 0, "medium": 0, "low": 0}
    
    for pattern in patterns:
        ptype = pattern.get("pattern_type", "unknown")
        by_type[ptype] = by_type.get(ptype, 0) + 1
        severity = pattern.get("severity", "low")
        by_severity[severity] = by_severity.get(severity, 0) + 1
    
    print("\nPattern Summary:")
    print(f"  By Type: {by_type}")
    print(f"  By Severity: {by_severity}")

