"""Configuration loader for Directory OCR."""

import yaml
from pathlib import Path
from typing import Dict, Any


class Config:
    """Configuration manager for the application."""
    
    def __init__(self, config_path: str = "config.yaml"):
        """
        Initialize configuration from YAML file.
        
        Args:
            config_path: Path to the configuration file
        """
        self.config_path = Path(config_path)
        self.config = self._load_config()
        
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        with open(self.config_path, 'r') as f:
            return yaml.safe_load(f)
    
    @property
    def folders(self) -> Dict[str, str]:
        """Get folder paths configuration."""
        return self.config.get('folders', {})
    
    @property
    def llm(self) -> Dict[str, Any]:
        """Get LLM configuration."""
        return self.config.get('llm', {})
    
    @property
    def processing(self) -> Dict[str, Any]:
        """Get processing settings."""
        return self.config.get('processing', {})
    
    @property
    def extraction_prompt(self) -> str:
        """Get the extraction prompt template."""
        return self.config.get('extraction_prompt', '')
    
    @property
    def ocr_prompt(self) -> str:
        """Get the OCR prompt."""
        return self.config.get('ocr_prompt', '')
    
    @property
    def match_file_path(self) -> Path:
        """Get the path to the match CSV file."""
        match_file = self.processing.get('match_file', 'data/matchwith.csv')
        return Path(match_file).resolve()
    
    @property
    def sleep_time(self) -> int:
        """Get the sleep time in seconds between processing loops."""
        return self.processing.get('sleep_time', 2)
    
    def get_folder_path(self, folder_name: str) -> Path:
        """
        Get absolute path for a folder.
        
        Args:
            folder_name: Name of the folder (incoming, extracted, processed, matches, errors, output)
            
        Returns:
            Absolute path to the folder
        """
        folder_path = self.folders.get(folder_name, folder_name)
        return Path(folder_path).resolve()
