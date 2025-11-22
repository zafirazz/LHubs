"""
CSV Parser Tool - Parses CSV files with robust error handling.
"""

import csv
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, ClassVar

import pandas as pd

from langchain.tools import BaseTool
from pydantic import BaseModel, Field


logger = logging.getLogger(__name__)


class CSVParserInput(BaseModel):
    """Input schema for CSV parser."""
    file_path: str = Field(description="Path to the CSV file")
    delimiter: Optional[str] = Field(default=",", description="CSV delimiter")
    encoding: Optional[str] = Field(default="utf-8", description="File encoding")
    skip_rows: Optional[int] = Field(default=0, description="Number of rows to skip")


class CSVParserTool(BaseTool):
    """Tool for parsing CSV files."""

    name: ClassVar[str] = "csv_parser"
    description: ClassVar[str] = """
    Parses CSV files and returns structured data.
    Handles various CSV formats, encodings, and delimiters.
    Returns data as a list of dictionaries.
    """
    args_schema: ClassVar[type[BaseModel]] = CSVParserInput

    def _run(self, file_path: str, delimiter: str = ",", encoding: str = "utf-8", skip_rows: int = 0) -> Dict[str, Any]:
        """Parse CSV file."""
        try:
            file_path_obj = Path(file_path)
            if not file_path_obj.exists():
                raise FileNotFoundError(f"CSV file not found: {file_path}")

            # Try pandas first (more robust)
            try:
                df = pd.read_csv(
                    file_path,
                    delimiter=delimiter,
                    encoding=encoding,
                    skiprows=skip_rows,
                    on_bad_lines="skip",
                    engine="python",
                )
                data = df.to_dict("records")
                
                return {
                    "success": True,
                    "data": data,
                    "row_count": len(data),
                    "column_count": len(df.columns),
                    "columns": list(df.columns),
                }
            except Exception as e:
                logger.warning(f"Pandas parsing failed, trying standard library: {e}")
                
                # Fallback to standard library
                with open(file_path, "r", encoding=encoding) as f:
                    reader = csv.DictReader(f, delimiter=delimiter)
                    data = list(reader)
                    
                    return {
                        "success": True,
                        "data": data,
                        "row_count": len(data),
                        "column_count": len(data[0].keys()) if data else 0,
                        "columns": list(data[0].keys()) if data else [],
                    }

        except Exception as e:
            logger.error(f"Error parsing CSV: {e}")
            return {
                "success": False,
                "error": str(e),
                "data": [],
            }

    async def _arun(self, file_path: str, delimiter: str = ",", encoding: str = "utf-8", skip_rows: int = 0) -> Dict[str, Any]:
        """Async version of CSV parsing."""
        return self._run(file_path, delimiter, encoding, skip_rows)

