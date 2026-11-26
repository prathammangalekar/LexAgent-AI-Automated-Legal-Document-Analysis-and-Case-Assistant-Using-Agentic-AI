"""DOCX and Word document text extractor using python-docx."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Any, List
from docx import Document


class DocxReader:
    """Extracts structured text, headings, and tables from DOCX files."""

    @staticmethod
    def extract_text_with_metadata(file_path: str | Path) -> Dict[str, Any]:
        """Extracts text from DOCX files.

        Args:
            file_path: Path to .docx file.

        Returns:
            Dictionary with full_text, sections, paragraphs, and tables.
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"DOCX file not found: {file_path}")

        doc = Document(str(path))
        paragraphs_list: List[str] = []
        headings: List[str] = []

        for p in doc.paragraphs:
            text = p.text.strip()
            if text:
                paragraphs_list.append(text)
                if p.style and 'Heading' in p.style.name:
                    headings.append(text)

        # Extract table data
        table_texts: List[str] = []
        for table in doc.tables:
            for row in table.rows:
                row_text = " | ".join(cell.text.strip() for cell in row.cells if cell.text.strip())
                if row_text:
                    table_texts.append(row_text)

        full_text = "\n\n".join(paragraphs_list)
        if table_texts:
            full_text += "\n\n--- Tables ---\n" + "\n".join(table_texts)

        return {
            "file_name": path.name,
            "total_pages": 1,
            "full_text": full_text,
            "paragraphs_count": len(paragraphs_list),
            "headings": headings,
            "metadata": {
                "headings_found": len(headings),
                "tables_count": len(doc.tables)
            },
            "ocr_required": False
        }
