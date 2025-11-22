"""
Text Extractor Tool - Extracts text from various file formats.
"""

import logging
from pathlib import Path
from typing import Any, Dict, ClassVar

from langchain.tools import BaseTool
from pydantic import BaseModel, Field


logger = logging.getLogger(__name__)


class TextExtractorInput(BaseModel):
    """Input schema for text extractor."""
    file_path: str = Field(description="Path to the text file")
    encoding: str = Field(default="utf-8", description="File encoding")


class TextExtractorTool(BaseTool):
    """Tool for extracting text from files."""

    name: ClassVar[str] = "text_extractor"
    description: ClassVar[str] = """
    Extracts text content from text files (.txt, .md, etc.).
    Returns the text content as a string.
    """
    args_schema: ClassVar[type[BaseModel]] = TextExtractorInput

    def _run(self, file_path: str, encoding: str = "utf-8") -> Dict[str, Any]:
        """Extract text from file."""
        try:
            file_path_obj = Path(file_path)
            if not file_path_obj.exists():
                raise FileNotFoundError(f"File not found: {file_path}")

            with open(file_path, "r", encoding=encoding) as f:
                content = f.read()

            return {
                "success": True,
                "content": content,
                "length": len(content),
                "file_path": str(file_path),
            }

        except UnicodeDecodeError:
            # Try different encodings
            for enc in ["latin-1", "cp1252", "iso-8859-1"]:
                try:
                    with open(file_path, "r", encoding=enc) as f:
                        content = f.read()
                    return {
                        "success": True,
                        "content": content,
                        "length": len(content),
                        "file_path": str(file_path),
                        "encoding_used": enc,
                    }
                except:
                    continue

            return {
                "success": False,
                "error": "Could not decode file with any encoding",
                "content": "",
            }

        except Exception as e:
            logger.error(f"Error extracting text: {e}")
            return {
                "success": False,
                "error": str(e),
                "content": "",
            }

    async def _arun(self, file_path: str, encoding: str = "utf-8") -> Dict[str, Any]:
        """Async version of text extraction."""
        return self._run(file_path, encoding)

