"""
Data Parser Agent - Extracts and normalizes data from various file formats.
"""

import csv
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

from ..base_agent import BaseAgent, AgentMessage, AgentStatus
from ...tools.parsers.csv_parser import CSVParserTool
from ...tools.parsers.text_extractor import TextExtractorTool
from ...tools.parsers.transaction_normalizer import TransactionNormalizerTool


logger = logging.getLogger(__name__)


class DataParserAgent(BaseAgent):
    """
    Parses client data from various file formats.
    
    Handles:
    - CSV files (client data, transactions)
    - Text files (notes)
    - PDF files (documents)
    - Excel files
    """

    def __init__(self, agent_id: str = "data_parser", **kwargs):
        tools = [
            CSVParserTool(),
            TextExtractorTool(),
            TransactionNormalizerTool(),
        ]
        
        super().__init__(
            agent_id=agent_id,
            name="Data Parser Agent",
            description="Extracts and normalizes data from uploaded files",
            tools=tools,
            **kwargs
        )

    def get_required_inputs(self) -> List[str]:
        return ["client_folder_path"]

    def get_output_schema(self) -> Dict[str, Any]:
        return {
            "parsed_data": {
                "csv_data": List[Dict[str, Any]],
                "notes": List[str],
                "transactions": List[Dict[str, Any]],
            },
            "metadata": {
                "files_processed": int,
                "parsing_errors": List[str],
                "data_quality_score": float,
            },
            "file_info": {
                "file_count": int,
                "file_types": List[str],
                "total_size_bytes": int,
            }
        }

    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse all files in the client folder.
        
        Args:
            input_data: Contains 'client_folder_path'
            
        Returns:
            Parsed and normalized data
        """
        client_folder_path = Path(input_data["client_folder_path"])
        
        if not client_folder_path.exists():
            raise ValueError(f"Client folder not found: {client_folder_path}")

        logger.info(f"Parsing client folder: {client_folder_path}")

        parsed_data = {
            "csv_data": [],
            "notes": [],
            "transactions": [],
        }
        
        metadata = {
            "files_processed": 0,
            "parsing_errors": [],
            "data_quality_score": 0.0,
        }
        
        file_info = {
            "file_count": 0,
            "file_types": [],
            "total_size_bytes": 0,
        }

        # Discover all files
        files = list(client_folder_path.rglob("*"))
        files = [f for f in files if f.is_file()]
        
        file_info["file_count"] = len(files)
        file_info["total_size_bytes"] = sum(f.stat().st_size for f in files)

        # Process each file
        for file_path in files:
            try:
                file_info["file_types"].append(file_path.suffix.lower())
                
                if file_path.suffix.lower() == ".csv":
                    result = self._parse_csv(file_path)
                    if "transactions" in result:
                        parsed_data["transactions"].extend(result["transactions"])
                    else:
                        parsed_data["csv_data"].extend(result.get("data", []))
                
                elif file_path.suffix.lower() in [".txt", ".md"]:
                    notes = self._extract_text(file_path)
                    parsed_data["notes"].extend(notes)
                
                elif file_path.suffix.lower() == ".json":
                    result = self._parse_json(file_path)
                    if "transactions" in result:
                        parsed_data["transactions"].extend(result["transactions"])
                    else:
                        parsed_data["csv_data"].extend(result.get("data", []))
                
                metadata["files_processed"] += 1
                
            except Exception as e:
                error_msg = f"Error parsing {file_path}: {str(e)}"
                logger.error(error_msg)
                metadata["parsing_errors"].append(error_msg)

        # Normalize transactions
        if parsed_data["transactions"]:
            parsed_data["transactions"] = self._normalize_transactions(parsed_data["transactions"])

        # Calculate data quality score
        metadata["data_quality_score"] = self._calculate_quality_score(parsed_data, metadata)

        return {
            "parsed_data": parsed_data,
            "metadata": metadata,
            "file_info": file_info,
        }

    def _parse_csv(self, file_path: Path) -> Dict[str, Any]:
        """Parse CSV file."""
        try:
            df = pd.read_csv(file_path)
            data = df.to_dict("records")
            
            # Check if this looks like transaction data
            transaction_indicators = ["amount", "date", "transaction", "type", "from", "to"]
            if any(col.lower() in transaction_indicators for col in df.columns):
                return {"transactions": data}
            
            return {"data": data}
        except Exception as e:
            logger.error(f"CSV parsing error: {e}")
            raise

    def _parse_json(self, file_path: Path) -> Dict[str, Any]:
        """Parse JSON file."""
        with open(file_path, "r") as f:
            data = json.load(f)
        
        if isinstance(data, list):
            # Check if transactions
            if data and isinstance(data[0], dict) and "amount" in data[0]:
                return {"transactions": data}
            return {"data": data}
        elif isinstance(data, dict):
            if "transactions" in data:
                return {"transactions": data["transactions"]}
            return {"data": [data]}
        
        return {"data": []}

    def _extract_text(self, file_path: Path) -> List[str]:
        """Extract text from file."""
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Split into paragraphs/sections
        notes = [note.strip() for note in content.split("\n\n") if note.strip()]
        return notes

    def _normalize_transactions(self, transactions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Normalize transaction data to standard format."""
        normalized = []
        
        for tx in transactions:
            normalized_tx = {
                "transaction_id": tx.get("id") or tx.get("transaction_id") or str(len(normalized)),
                "date": tx.get("date") or tx.get("transaction_date") or tx.get("timestamp"),
                "amount": float(tx.get("amount", 0)),
                "currency": tx.get("currency", "USD"),
                "type": tx.get("type") or tx.get("transaction_type", "unknown"),
                "from_account": tx.get("from") or tx.get("from_account") or tx.get("sender"),
                "to_account": tx.get("to") or tx.get("to_account") or tx.get("receiver"),
                "description": tx.get("description") or tx.get("note") or "",
                "metadata": {k: v for k, v in tx.items() if k not in [
                    "id", "transaction_id", "date", "transaction_date", "timestamp",
                    "amount", "currency", "type", "transaction_type",
                    "from", "from_account", "sender", "to", "to_account", "receiver",
                    "description", "note"
                ]},
            }
            normalized.append(normalized_tx)
        
        return normalized

    def _calculate_quality_score(self, parsed_data: Dict, metadata: Dict) -> float:
        """Calculate data quality score (0-1)."""
        total_files = metadata["files_processed"] + len(metadata["parsing_errors"])
        if total_files == 0:
            return 0.0
        
        error_rate = len(metadata["parsing_errors"]) / total_files
        completeness = (
            (1.0 if parsed_data["csv_data"] else 0.0) * 0.3 +
            (1.0 if parsed_data["notes"] else 0.0) * 0.2 +
            (1.0 if parsed_data["transactions"] else 0.0) * 0.5
        )
        
        quality_score = (1.0 - error_rate) * completeness
        return round(quality_score, 2)

