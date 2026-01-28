"""Configuration management."""
import json
from pathlib import Path
from typing import List, Dict
from urllib.parse import urlparse


class Config:
    """Configuration loader and manager."""

    def __init__(self, config_path: str = "config/sources.json"):
        """Initialize configuration.

        Args:
            config_path: Path to configuration file
        """
        self.config_path = Path(config_path)
        self.sources: List[Dict] = []
        self._load()

    def _load(self) -> None:
        """Load configuration from file."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")

        with open(self.config_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.sources = data.get('sources', [])

    def get_enabled_sources(self) -> List[Dict]:
        """Get list of enabled sources.

        Returns:
            List of source configuration dictionaries
        """
        return [s for s in self.sources if s.get('enabled', True)]

    @staticmethod
    def extract_source_id(url: str) -> str:
        """Extract source ID from URL.

        Args:
            url: Source URL

        Returns:
            Source ID (last path component)
        """
        parsed = urlparse(url)
        path = parsed.path.rstrip('/')
        return path.split('/')[-1] if path else 'unknown'
