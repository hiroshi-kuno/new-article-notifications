"""Data models for article tracking."""
from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class Article:
    """Represents a single article."""
    title: str
    url: str
    published_time: Optional[str] = None

    def __eq__(self, other) -> bool:
        """Two articles are equal if they have the same URL."""
        if not isinstance(other, Article):
            return False
        return self.url == other.url

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "title": self.title,
            "url": self.url,
            "published_time": self.published_time
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Article":
        """Create Article from dictionary."""
        return cls(
            title=data["title"],
            url=data["url"],
            published_time=data.get("published_time")
        )


@dataclass
class SourceState:
    """Represents the state of a monitored source."""
    source_id: str
    last_article: Optional[Article] = None
    last_checked: Optional[str] = None
    etag: Optional[str] = None
    last_modified: Optional[str] = None
    error_count: int = 0
    last_error: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "source_id": self.source_id,
            "last_article": self.last_article.to_dict() if self.last_article else None,
            "last_checked": self.last_checked,
            "etag": self.etag,
            "last_modified": self.last_modified,
            "error_count": self.error_count,
            "last_error": self.last_error
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SourceState":
        """Create SourceState from dictionary."""
        last_article = None
        if data.get("last_article"):
            last_article = Article.from_dict(data["last_article"])

        return cls(
            source_id=data["source_id"],
            last_article=last_article,
            last_checked=data.get("last_checked"),
            etag=data.get("etag"),
            last_modified=data.get("last_modified"),
            error_count=data.get("error_count", 0),
            last_error=data.get("last_error")
        )
