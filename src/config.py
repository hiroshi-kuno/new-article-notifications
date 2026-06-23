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

    # Trailing path segments that don't identify the source itself
    _SOURCE_ID_SKIP = ('rss', 'feed', 'rss.xml', 'feed.xml', 'atom.xml', 'index.xml')

    @staticmethod
    def extract_source_id(url_or_source) -> str:
        """Extract source ID from a URL string or source config dict.

        Accepts either a URL string (legacy) or a source dict from sources.json.
        When given a dict, an explicit "source_id" field takes precedence over
        the URL-derived ID — use this to disambiguate sources whose URLs would
        produce the same trailing path segment.

        Args:
            url_or_source: URL string or source config dict.

        Returns:
            Source ID (explicit override, or last meaningful path component).
        """
        if isinstance(url_or_source, dict):
            if explicit := url_or_source.get('source_id'):
                return explicit
            url = url_or_source.get('url', '')
        else:
            url = url_or_source

        parsed = urlparse(url)
        path = parsed.path.rstrip('/')
        if not path:
            return 'unknown'
        segments = path.split('/')
        while segments and segments[-1].lower() in Config._SOURCE_ID_SKIP:
            segments.pop()
        return segments[-1] if segments and segments[-1] else 'unknown'
