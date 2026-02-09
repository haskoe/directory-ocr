"""Main entry point for Directory OCR application."""

import sys
import logging
from pathlib import Path
from .config import Config
from .watcher import DirectoryWatcher


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
    
    # Reduce noise from watchdog
    logging.getLogger('watchdog').setLevel(logging.WARNING)


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
        logger.info(f"Watch folder: {config.get_folder_path('incoming')}")
        logger.info(f"Output folder: {config.get_folder_path('output')}")
        logger.info(f"Processed folder: {config.get_folder_path('processed')}")
        logger.info(f"Errors folder: {config.get_folder_path('errors')}")
        logger.info(f"Vision endpoint: {config.llm.get('vision_endpoint')}")
        logger.info(f"Text endpoint: {config.llm.get('text_endpoint')}")
        
        # Start directory watcher
        watcher = DirectoryWatcher(config)
        logger.info("Starting file monitor...")
        logger.info("Press Ctrl+C to stop")
        print("-" * 60)
        
        watcher.run()
        
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
