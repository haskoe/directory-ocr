"""File processor orchestrating the two-step processing pipeline."""

import csv
import json
import logging
import shutil
from pathlib import Path
from typing import Optional, List, Tuple
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
        self.incoming_dir = config.get_folder_path('incoming')
        self.extracted_dir = config.get_folder_path('extracted')
        self.processed_dir = config.get_folder_path('processed')
        self.matches_dir = config.get_folder_path('matches')
        self.errors_dir = config.get_folder_path('errors')
        self.output_dir = config.get_folder_path('output')
        
        # Ensure directories exist
        self.incoming_dir.mkdir(parents=True, exist_ok=True)
        self.extracted_dir.mkdir(parents=True, exist_ok=True)
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        self.matches_dir.mkdir(parents=True, exist_ok=True)
        self.errors_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Get supported extensions
        processing = config.processing
        self.supported_extensions = set(
            processing.get('image_extensions', []) + 
            processing.get('pdf_extensions', [])
        )
    
    def process_step1(self) -> int:
        """
        Step 1: Process all files in incoming folder.
        
        Extract text from images/PDFs and save to extracted folder.
        Move source files to processed or errors.
        
        Returns:
            Number of files successfully processed
        """
        files = [f for f in self.incoming_dir.iterdir() 
                if f.is_file() and f.suffix.lower() in self.supported_extensions]
        
        if not files:
            return 0
        
        logger.info(f"Step 1: Processing {len(files)} file(s) from incoming")
        
        processed_count = 0
        for file_path in files:
            try:
                logger.info(f"Processing: {file_path.name}")
                
                # Extract text
                text = self.text_extractor.extract_text(file_path)
                if not text:
                    logger.error(f"Text extraction failed for {file_path.name}")
                    self._move_to_errors(file_path)
                    continue
                
                # Save text to extracted folder
                txt_path = self.extracted_dir / f"{file_path.stem}.txt"
                txt_path.write_text(text, encoding='utf-8')
                logger.info(f"Saved extracted text: {txt_path.name}")
                
                # Move source to processed
                self._move_to_processed(file_path)
                processed_count += 1
                
            except Exception as e:
                logger.error(f"Processing failed for {file_path.name}: {e}", exc_info=True)
                self._move_to_errors(file_path)
        
        logger.info(f"Step 1 complete: {processed_count}/{len(files)} files processed successfully")
        return processed_count
    
    def process_step2(self) -> None:
        """
        Step 2: Match files in extracted folder with matchwith.csv.
        
        If match found: move text file and matched CSV row to matches folder.
        If no match: keep text file in extracted folder.
        """
        # Check if match file exists
        match_file = self.config.match_file_path
        if not match_file.exists():
            logger.debug(f"No match file found: {match_file}")
            return
        
        # Get all text files in extracted folder
        txt_files = list(self.extracted_dir.glob("*.txt"))
        if not txt_files:
            logger.debug("No files in extracted folder to match")
            return
        
        logger.info(f"Step 2: Matching {len(txt_files)} file(s) with {match_file.name}")
        
        # Load CSV data
        csv_rows = self._load_csv(match_file)
        if not csv_rows:
            logger.error("Failed to load CSV data")
            return
        
        # Process each extracted text file
        for txt_file in txt_files:
            try:
                self._match_and_move(txt_file, csv_rows, match_file)
            except Exception as e:
                logger.error(f"Matching failed for {txt_file.name}: {e}", exc_info=True)
        
        logger.info("Step 2 complete")
    
    def _match_and_move(self, txt_file: Path, csv_rows: List[List[str]], csv_file: Path) -> None:
        """
        Match a text file with CSV data and move if match found.
        
        Args:
            txt_file: Path to text file to match
            csv_rows: List of CSV rows
            csv_file: Path to CSV file
        """
        # Read text content
        text = txt_file.read_text(encoding='utf-8')
        
        # Prepare CSV data as string for LLM
        csv_str = "\n".join([",".join(row) for row in csv_rows])
        
        # Build prompt
        prompt_template = self.config.extraction_prompt
        prompt = prompt_template.format(text=text, match_data=csv_str)
        
        # Call LLM to find match
        response = self.text_client.generate_text(prompt, temperature=0.0)
        if not response:
            logger.warning(f"No LLM response for {txt_file.name}")
            return
        
        # Parse JSON response
        match_result = self._parse_json_response(response)
        if not match_result:
            logger.warning(f"Failed to parse match result for {txt_file.name}")
            return
        
        # Check confidence threshold
        confidence = match_result.get('confidence', 0.0)
        row_number = match_result.get('row_number')
        
        logger.info(f"Match result for {txt_file.name}: confidence={confidence:.2f}, row={row_number}")
        
        if confidence >= 0.6 and row_number is not None:
            # Match found - move text file and CSV row to matches
            self._move_match(txt_file, match_result, csv_rows)
        else:
            # No match - keep file in extracted
            logger.info(f"No match found for {txt_file.name} (confidence={confidence:.2f})")
    
    def _move_match(self, txt_file: Path, match_result: dict, csv_rows: List[List[str]]) -> None:
        """
        Move matched text file and CSV row to matches folder.
        
        Args:
            txt_file: Text file to move
            match_result: Match result dictionary with date and description fields
            csv_rows: All CSV rows (including header)
        """
        try:
            # Move text file
            dest_txt = self.matches_dir / txt_file.name
            shutil.move(str(txt_file), str(dest_txt))
            logger.info(f"Moved {txt_file.name} to matches")
            
            # Save match result as JSON
            json_path = self.matches_dir / f"{txt_file.stem}_match.json"
            json_path.write_text(json.dumps(match_result, indent=2, ensure_ascii=False), encoding='utf-8')
            logger.info(f"Saved match result: {json_path.name}")
            
            # Find matched CSV row by comparing date and description
            matched_date = match_result.get('date', '').strip().strip('"')
            matched_desc = match_result.get('description', '').strip().strip('"').lower()
            
            matched_row = None
            for row in csv_rows:
                if len(row) >= 3:
                    # CSV structure: date, date, description, amount, total
                    row_date = row[0].strip().strip('"')
                    row_desc = row[1].strip().strip('"').lower() if len(row) > 1 else ''
                    
                    # Match on date (column 0) and description (column 2)
                    if len(row) > 2:
                        row_desc = row[2].strip().strip('"').lower()
                        
                        if row_date == matched_date and matched_desc in row_desc:
                            matched_row = row
                            logger.info(f"Found matching CSV row: date={row_date}, desc={row[2][:50]}...")
                            break
            
            # Save matched CSV row
            if matched_row:
                csv_path = self.matches_dir / f"{txt_file.stem}_matched_row.txt"
                csv_path.write_text(";".join(matched_row), encoding='utf-8')
                logger.info(f"Saved matched row: {csv_path.name}")
            else:
                logger.warning(f"Could not find matching CSV row for date={matched_date}, desc={matched_desc[:50]}...")
            
        except Exception as e:
            logger.error(f"Failed to move match for {txt_file.name}: {e}")
    
    def _load_csv(self, csv_file: Path) -> Optional[List[List[str]]]:
        """
        Load CSV file.
        
        Args:
            csv_file: Path to CSV file
            
        Returns:
            List of rows (each row is a list of strings) or None if failed
        """
        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.reader(f, delimiter=';')
                rows = list(reader)
            logger.debug(f"Loaded {len(rows)} rows from {csv_file.name}")
            return rows
        except Exception as e:
            logger.error(f"Failed to load CSV: {e}")
            return None
    
    def _parse_json_response(self, response: str) -> Optional[dict]:
        """
        Parse JSON from LLM response.
        
        Args:
            response: LLM response string
            
        Returns:
            Parsed JSON dict or None if parsing failed
        """
        try:
            # Clean up response
            response = response.strip()
            if response.startswith("```json"):
                response = response[7:]
            if response.startswith("```"):
                response = response[3:]
            if response.endswith("```"):
                response = response[:-3]
            response = response.strip()
            
            return json.loads(response)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON: {e}")
            logger.debug(f"Response was: {response[:200]}")
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
