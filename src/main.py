"""Main entry point for Directory OCR application."""

import sys
import time
import logging
from pathlib import Path
from .config import Config
from .file_processor import FileProcessor


def setup_logging(level: str = "INFO") -> None:
    """
    Configure logging for the application.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
    """
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))
    root_logger.addHandler(console_handler)


def main() -> None:
    """Main entry point."""
    print("=" * 60)
    print("Directory OCR - Automated File Processing Pipeline")
    print("=" * 60)
    
    # Setup logging
    log_level = "INFO"
    if len(sys.argv) > 1 and sys.argv[1] == "--debug":
        log_level = "DEBUG"
    
    setup_logging(log_level)
    logger = logging.getLogger(__name__)
    
    try:
        # Load configuration
        config_path = Path("config.yaml")
        if not config_path.exists():
            logger.error(f"Configuration file not found: {config_path}")
            sys.exit(1)
        
        config = Config(str(config_path))
        logger.info("Configuration loaded successfully")
        
        # Display configuration
        logger.info(f"Incoming folder: {config.get_folder_path('incoming')}")
        logger.info(f"Extracted folder: {config.get_folder_path('extracted')}")
        logger.info(f"Matches folder: {config.get_folder_path('matches')}")
        logger.info(f"Processed folder: {config.get_folder_path('processed')}")
        logger.info(f"Errors folder: {config.get_folder_path('errors')}")
        logger.info(f"Match file: {config.match_file_path}")
        logger.info(f"Sleep time: {config.sleep_time}s")
        logger.info(f"Vision endpoint: {config.llm.get('vision_endpoint')}")
        logger.info(f"Text endpoint: {config.llm.get('text_endpoint')}")
        
        # Initialize processor
        processor = FileProcessor(config)
        logger.info("File processor initialized")
        logger.info("Starting processing loop...")
        logger.info("Press Ctrl+C to stop")
        print("-" * 60)
        
        # Main processing loop
        iteration = 0
        while True:
            iteration += 1
            logger.debug(f"--- Loop iteration {iteration} ---")
            
            # Step 1: Process files in incoming folder
            processed_count = processor.process_step1()
            
            # Step 2: Match files in extracted folder (only if step 1 processed files)
            if processed_count > 0:
                processor.process_step2()
            
            # Sleep before next iteration
            time.sleep(config.sleep_time)
        
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
