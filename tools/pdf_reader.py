"""PDF extraction tool using PyMuPDF (fitz) with metadata and layout preservation."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Any, List
import fitz  # PyMuPDF


class PDFReader:
    """Extracts text, metadata, page numbers, and detects scanned pages."""

    @staticmethod
    def extract_text_with_metadata(file_path: str | Path) -> Dict[str, Any]:
        """Reads a PDF document and returns extracted text, pages, and metadata.

        Args:
            file_path: Path to the PDF file.

        Returns:
            Dictionary containing full_text, pages, metadata, and ocr_required flag.
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"PDF file not found: {file_path}")

        doc = fitz.open(str(path))
        pages_content: List[Dict[str, Any]] = []
        full_text_list: List[str] = []
        low_text_page_count = 0

        for page_idx in range(len(doc)):
            page = doc[page_idx]
            page_text = page.get_text("text").strip()
            # If a page has very few characters, it might be a scanned image
            if len(page_text) < 40:
                low_text_page_count += 1

            pages_content.append({
                "page_number": page_idx + 1,
                "text": page_text,
                "character_count": len(page_text)
            })
            if page_text:
                full_text_list.append(f"--- [Page {page_idx + 1}] ---\n" + page_text)

        doc_metadata = doc.metadata or {}
        doc.close()

        ocr_required = (low_text_page_count > 0 and (low_text_page_count / max(1, len(pages_content))) > 0.5)

        return {
            "file_name": path.name,
            "total_pages": len(pages_content),
            "full_text": "\n\n".join(full_text_list),
            "pages": pages_content,
            "metadata": {
                "title": doc_metadata.get("title", ""),
                "author": doc_metadata.get("author", ""),
                "subject": doc_metadata.get("subject", ""),
                "creator": doc_metadata.get("creator", ""),
            },
            "ocr_required": ocr_required,
        }
