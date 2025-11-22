"""
Transaction Normalizer Tool - Normalizes transaction data to standard format.
"""

import logging
from typing import Any, Dict, List, ClassVar

from langchain.tools import BaseTool
from pydantic import BaseModel, Field


logger = logging.getLogger(__name__)


class TransactionNormalizerInput(BaseModel):
    """Input schema for transaction normalizer."""
    transactions: List[Dict[str, Any]] = Field(description="List of transaction dictionaries to normalize")


class TransactionNormalizerTool(BaseTool):
    """Tool for normalizing transaction data."""

    name: ClassVar[str] = "transaction_normalizer"
    description: ClassVar[str] = """
    Normalizes transaction data to a standard format.
    Handles various transaction data formats and maps them to a common schema.
    """
    args_schema: ClassVar[type[BaseModel]] = TransactionNormalizerInput

    def _run(self, transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Normalize transactions."""
        try:
            normalized = []
            
            for idx, tx in enumerate(transactions):
                normalized_tx = {
                    "transaction_id": tx.get("id") or tx.get("transaction_id") or tx.get("tx_id") or f"tx_{idx}",
                    "date": tx.get("date") or tx.get("transaction_date") or tx.get("timestamp") or tx.get("time"),
                    "amount": self._parse_amount(tx),
                    "currency": tx.get("currency") or tx.get("curr") or "USD",
                    "type": tx.get("type") or tx.get("transaction_type") or tx.get("tx_type") or "unknown",
                    "from_account": tx.get("from") or tx.get("from_account") or tx.get("sender") or tx.get("source"),
                    "to_account": tx.get("to") or tx.get("to_account") or tx.get("receiver") or tx.get("destination"),
                    "description": tx.get("description") or tx.get("note") or tx.get("memo") or tx.get("details") or "",
                    "metadata": {
                        k: v for k, v in tx.items()
                        if k not in [
                            "id", "transaction_id", "tx_id",
                            "date", "transaction_date", "timestamp", "time",
                            "amount", "currency", "curr",
                            "type", "transaction_type", "tx_type",
                            "from", "from_account", "sender", "source",
                            "to", "to_account", "receiver", "destination",
                            "description", "note", "memo", "details"
                        ]
                    },
                }
                normalized.append(normalized_tx)

            return {
                "success": True,
                "normalized_transactions": normalized,
                "count": len(normalized),
            }

        except Exception as e:
            logger.error(f"Error normalizing transactions: {e}")
            return {
                "success": False,
                "error": str(e),
                "normalized_transactions": [],
            }

    def _parse_amount(self, tx: Dict[str, Any]) -> float:
        """Parse amount from various formats."""
        amount = tx.get("amount") or tx.get("amt") or tx.get("value") or tx.get("sum") or 0
        
        if isinstance(amount, (int, float)):
            return float(amount)
        elif isinstance(amount, str):
            # Remove currency symbols and commas
            cleaned = amount.replace("$", "").replace(",", "").replace("€", "").replace("£", "").strip()
            try:
                return float(cleaned)
            except:
                return 0.0
        
        return 0.0

    async def _arun(self, transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Async version of transaction normalization."""
        return self._run(transactions)

