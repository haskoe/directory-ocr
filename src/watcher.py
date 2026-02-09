"""File system watcher for monitoring incoming folder."""

import logging
import time
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent
from .file_processor import FileProcessor
from .config import Config

logger = logging.getLogger(__name__)


class FileWatcher(FileSystemEventHandler):
    """Watch for new files in the incoming folder."""
    
    def __init__(self, processor: FileProcessor, config: Config):
        """
        Initialize file watcher.
        
        Args:
            processor: File processor instance
            config: Configuration object
        """
        super().__init__()
        self.processor = processor
        self.config = config
        
        # Get supported extensions
        processing = config.processing
        self.supported_extensions = set(
            processing.get('image_extensions', []) + 
            processing.get('pdf_extensions', [])
        )
        
        logger.info(f"Watching for files with extensions: {self.supported_extensions}")
    
    def on_created(self, event: FileCreatedEvent) -> None:
        """
        Handle file creation event.
        
        Args:
            event: File system event
        """
        # Ignore directories
        if event.is_directory:
            return
        
        file_path = Path(event.src_path)
        
        # Check if file extension is supported
        if file_path.suffix.lower() not in self.supported_extensions:
            logger.debug(f"Ignoring unsupported file: {file_path.name}")
            return
        
        logger.info(f"New file detected: {file_path.name}")
        
        # Small delay to ensure file is fully written
        time.sleep(0.5)
        
        # Process the file
        try:
            self.processor.process_file(file_path)
        except Exception as e:
            logger.error(f"Unexpected error processing {file_path.name}: {e}", exc_info=True)


class DirectoryWatcher:
    """Directory watcher service."""
    
    def __init__(self, config: Config):
        """
        Initialize directory watcher.
        
        Args:
            config: Configuration object
        """
        self.config = config
        self.processor = FileProcessor(config)
        self.handler = FileWatcher(self.processor, config)
        self.observer = Observer()
        
        self.watch_dir = config.get_folder_path('incoming')
        self.watch_dir.mkdir(parents=True, exist_ok=True)
    
    def start(self) -> None:
        """Start watching the incoming directory."""
        logger.info(f"Starting directory watch on: {self.watch_dir}")
        
        self.observer.schedule(
            self.handler,
            str(self.watch_dir),
            recursive=False
        )
        
        self.observer.start()
        logger.info("Directory watcher started successfully")
    
    def stop(self) -> None:
        """Stop watching the directory."""
        logger.info("Stopping directory watcher")
        self.observer.stop()
        self.observer.join()
        logger.info("Directory watcher stopped")
    
    def run(self) -> None:
        """Run the watcher (blocking)."""
        self.start()
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Received shutdown signal")
            self.stop()
