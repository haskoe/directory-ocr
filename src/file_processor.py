"""File processor orchestrating the two-step processing pipeline."""

import json
import logging
import shutil
from pathlib import Path
from typing import Optional
from .text_extractor import TextExtractor
from .llm_client import LLMClient
from .config import Config

logger = logging.getLogger(__name__)


class FileProcessor:
    """Orchestrator for the two-step file processing pipeline."""
    
    def __init__(self, config: Config):
        """
        Initialize file processor.
        
        Args:
            config: Configuration object
        """
        self.config = config
        
        # Initialize LLM clients
        vision_endpoint = config.llm.get('vision_endpoint', 'http://localhost:8080')
        text_endpoint = config.llm.get('text_endpoint', 'http://localhost:8081')
        timeout = config.llm.get('timeout', 120)
        
        self.vision_client = LLMClient(vision_endpoint, timeout)
        self.text_client = LLMClient(text_endpoint, timeout)
        
        # Initialize text extractor
        self.text_extractor = TextExtractor(
            vision_client=self.vision_client,
            ocr_prompt=config.ocr_prompt
        )
        
        # Get folder paths
        self.output_dir = config.get_folder_path('output')
        self.processed_dir = config.get_folder_path('processed')
        self.errors_dir = config.get_folder_path('errors')
        
        # Ensure directories exist
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        self.errors_dir.mkdir(parents=True, exist_ok=True)
    
    def process_file(self, file_path: Path) -> bool:
        """
        Process a file through the two-step pipeline.
        
        Step 1: Extract text and save as .txt
        Step 2: Extract structured data and save as .json
        
        Args:
            file_path: Path to the file to process
            
        Returns:
            True if processing succeeded, False otherwise
        """
        logger.info(f"Processing file: {file_path.name}")
        
        try:
            # Step 1: Text extraction
            text = self._step1_extract_text(file_path)
            if not text:
                logger.error(f"Text extraction failed for {file_path.name}")
                self._move_to_errors(file_path)
                return False
            
            # Save text to output
            txt_path = self._save_text(file_path.stem, text)
            if not txt_path:
                logger.error(f"Failed to save text for {file_path.name}")
                self._move_to_errors(file_path)
                return False
            
            logger.info(f"Step 1 complete: {txt_path.name}")
            
            # Step 2: Data structuring
            json_data = self._step2_extract_json(text)
            if not json_data:
                logger.warning(f"JSON extraction failed for {file_path.name}")
                # We still consider this a success if we got the text
                # Move to processed, but note the JSON extraction failure
            else:
                # Save JSON to output
                json_path = self._save_json(file_path.stem, json_data)
                if json_path:
                    logger.info(f"Step 2 complete: {json_path.name}")
            
            # Move source file to processed
            self._move_to_processed(file_path)
            logger.info(f"Successfully processed: {file_path.name}")
            return True
            
        except Exception as e:
            logger.error(f"Processing failed for {file_path.name}: {e}", exc_info=True)
            self._move_to_errors(file_path)
            return False
    
    def _step1_extract_text(self, file_path: Path) -> Optional[str]:
        """
        Step 1: Extract text from file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Extracted text or None if extraction failed
        """
        return self.text_extractor.extract_text(file_path)
    
    def _step2_extract_json(self, text: str) -> Optional[dict]:
        """
        Step 2: Extract structured data from text.
        
        Args:
            text: The text to analyze
            
        Returns:
            Parsed JSON object or None if extraction failed
        """
        prompt_template = self.config.extraction_prompt
        return self.text_client.extract_json(text, prompt_template)
    
    def _save_text(self, base_name: str, text: str) -> Optional[Path]:
        """
        Save extracted text to output folder.
        
        Args:
            base_name: Base name for the output file (without extension)
            text: Text content to save
            
        Returns:
            Path to saved file or None if save failed
        """
        try:
            output_path = self.output_dir / f"{base_name}.txt"
            output_path.write_text(text, encoding='utf-8')
            logger.debug(f"Saved text to {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"Failed to save text: {e}")
            return None
    
    def _save_json(self, base_name: str, data: dict) -> Optional[Path]:
        """
        Save structured data to output folder.
        
        Args:
            base_name: Base name for the output file (without extension)
            data: JSON data to save
            
        Returns:
            Path to saved file or None if save failed
        """
        try:
            output_path = self.output_dir / f"{base_name}.json"
            output_path.write_text(
                json.dumps(data, indent=2, ensure_ascii=False),
                encoding='utf-8'
            )
            logger.debug(f"Saved JSON to {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"Failed to save JSON: {e}")
            return None
    
    def _move_to_processed(self, file_path: Path) -> None:
        """
        Move file to processed folder.
        
        Args:
            file_path: Path to the file to move
        """
        try:
            destination = self.processed_dir / file_path.name
            shutil.move(str(file_path), str(destination))
            logger.debug(f"Moved {file_path.name} to processed")
        except Exception as e:
            logger.error(f"Failed to move file to processed: {e}")
    
    def _move_to_errors(self, file_path: Path) -> None:
        """
        Move file to errors folder.
        
        Args:
            file_path: Path to the file to move
        """
        try:
            destination = self.errors_dir / file_path.name
            shutil.move(str(file_path), str(destination))
            logger.debug(f"Moved {file_path.name} to errors")
        except Exception as e:
            logger.error(f"Failed to move file to errors: {e}")
