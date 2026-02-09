"""Text extraction from PDF and images."""

import logging
from pathlib import Path
from typing import Optional
from PyPDF2 import PdfReader
from .llm_client import LLMClient

logger = logging.getLogger(__name__)


class TextExtractor:
    """Extract text from PDF files and images."""
    
    def __init__(self, vision_client: Optional[LLMClient] = None, ocr_prompt: str = ""):
        """
        Initialize text extractor.
        
        Args:
            vision_client: LLM client for OCR on images
            ocr_prompt: Prompt to use for OCR
        """
        self.vision_client = vision_client
        self.ocr_prompt = ocr_prompt or "Please transcribe all visible text in this image."
    
    def extract_from_pdf(self, pdf_path: Path) -> Optional[str]:
        """
        Extract text from PDF file.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Extracted text or None if extraction failed
        """
        try:
            logger.info(f"Extracting text from PDF: {pdf_path.name}")
            
            reader = PdfReader(str(pdf_path))
            text_parts = []
            
            for page_num, page in enumerate(reader.pages, 1):
                try:
                    text = page.extract_text()
                    if text:
                        text_parts.append(text)
                        logger.debug(f"Extracted {len(text)} characters from page {page_num}")
                except Exception as e:
                    logger.warning(f"Failed to extract text from page {page_num}: {e}")
            
            if not text_parts:
                logger.warning(f"No text extracted from PDF: {pdf_path.name}")
                return None
            
            full_text = "\n\n".join(text_parts)
            logger.info(f"Successfully extracted {len(full_text)} characters from PDF")
            return full_text
            
        except Exception as e:
            logger.error(f"PDF extraction failed for {pdf_path.name}: {e}")
            return None
    
    def extract_from_image(self, image_path: Path) -> Optional[str]:
        """
        Extract text from image using OCR (via LLM vision model).
        
        Args:
            image_path: Path to image file
            
        Returns:
            Extracted text or None if extraction failed
        """
        if not self.vision_client:
            logger.error("No vision client configured for OCR")
            return None
        
        try:
            logger.info(f"Performing OCR on image: {image_path.name}")
            
            # Use absolute path for the image
            abs_path = str(image_path.resolve())
            
            # Call LLM with vision capabilities
            text = self.vision_client.generate_text(
                prompt=self.ocr_prompt,
                image_path=abs_path
            )
            
            if text:
                logger.info(f"Successfully extracted {len(text)} characters from image")
            else:
                logger.warning(f"No text extracted from image: {image_path.name}")
            
            return text
            
        except Exception as e:
            logger.error(f"Image OCR failed for {image_path.name}: {e}")
            return None
    
    def extract_text(self, file_path: Path) -> Optional[str]:
        """
        Extract text from file (auto-detect type).
        
        Args:
            file_path: Path to file
            
        Returns:
            Extracted text or None if extraction failed
        """
        suffix = file_path.suffix.lower()
        
        if suffix == '.pdf':
            return self.extract_from_pdf(file_path)
        elif suffix in ['.jpg', '.jpeg', '.png']:
            return self.extract_from_image(file_path)
        else:
            logger.error(f"Unsupported file type: {suffix}")
            return None
