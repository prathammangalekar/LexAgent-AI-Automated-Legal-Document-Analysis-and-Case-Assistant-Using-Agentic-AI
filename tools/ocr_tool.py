"""OCR extraction tool for scanned legal documents and images."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, Any

logger = logging.getLogger(__name__)


class OCRTool:
    """Performs Optical Character Recognition on scanned PDFs and images."""

    @staticmethod
    def is_tesseract_available() -> bool:
        """Check if pytesseract and the tesseract binary are available."""
        try:
            import pytesseract
            # Test if tesseract is callable
            pytesseract.get_tesseract_version()
            return True
        except Exception:
            return False

    @classmethod
    def extract_from_image_or_pdf(cls, file_path: str | Path) -> Dict[str, Any]:
        """Extracts text from scanned files using OCR or fallback.

        Args:
            file_path: Path to scanned image or PDF.

        Returns:
            Dictionary containing extracted text, OCR engine used, and confidence.
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        if cls.is_tesseract_available():
            try:
                import pytesseract
                from PIL import Image
                import fitz

                if path.suffix.lower() == ".pdf":
                    doc = fitz.open(str(path))
                    text_parts = []
                    for page_num in range(len(doc)):
                        page = doc[page_num]
                        pix = page.get_pixmap()
                        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                        txt = pytesseract.image_to_string(img)
                        text_parts.append(f"--- [OCR Page {page_num + 1}] ---\n" + txt)
                    doc.close()
                    return {
                        "text": "\n\n".join(text_parts),
                        "ocr_applied": True,
                        "engine": "Tesseract OCR",
                        "status": "success"
                    }
                else:
                    img = Image.open(str(path))
                    txt = pytesseract.image_to_string(img)
                    return {
                        "text": txt,
                        "ocr_applied": True,
                        "engine": "Tesseract OCR",
                        "status": "success"
                    }
            except Exception as e:
                logger.warning(f"OCR execution encountered an error: {e}")

        # Fallback when Tesseract is not installed on host machine
        return {
            "text": f"[OCR Note: Scanned document '{path.name}' detected. Optical Character Recognition engine ready for integration with Tesseract/Google Vision.]",
            "ocr_applied": False,
            "engine": "Fallback-Text-Buffer",
            "status": "fallback"
        }
