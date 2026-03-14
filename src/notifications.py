"""Notification handlers for new articles."""
import os
from typing import Optional
import requests

from .models import Article


class NotificationError(Exception):
    """Base exception for notification errors."""
    pass


class DiscordNotifier:
    """Send notifications to Discord via Incoming Webhooks."""

    def __init__(self, webhook_url: Optional[str] = None):
        """Initialize Discord notifier.

        Args:
            webhook_url: Discord webhook URL (if None, reads from DISCORD_WEBHOOK_URL env var)
        """
        self.webhook_url = webhook_url or os.environ.get('DISCORD_WEBHOOK_URL')
        self.nyt_webhook_url = os.environ.get('WEBHOOK_URL_NYT')
        self.wapo_webhook_url = os.environ.get('WEBHOOK_URL_WAPO')
        self.blog_webhook_url = os.environ.get('WEBHOOK_URL_BLOG')

    def is_enabled(self) -> bool:
        """Check if Discord notifications are enabled.

        Returns:
            True if webhook URL is configured
        """
        return bool(self.webhook_url or self.nyt_webhook_url or self.wapo_webhook_url or self.blog_webhook_url)

    def send(self, source_id: str, article: Article, previous_article: Optional[Article] = None) -> bool:
        """Send a notification about a new article.

        Args:
            source_id: ID of the source
            article: New article
            previous_article: Previous article (optional)

        Returns:
            True if notification sent successfully, False otherwise
        """
        if not self.is_enabled():
            return False

        try:
            # Build Discord message
            message = self._build_message(source_id, article, previous_article)

            # Determine which webhook to use
            if "nytimes.com" in article.url and self.nyt_webhook_url:
                webhook_url = self.nyt_webhook_url
            elif "washingtonpost.com" in article.url and self.wapo_webhook_url:
                webhook_url = self.wapo_webhook_url
            elif source_id == "data-vis-dispatch" and self.blog_webhook_url:
                webhook_url = self.blog_webhook_url
            else:
                webhook_url = self.webhook_url

            if not webhook_url:
                print(f"  ✗ No webhook URL configured for this source")
                return False

            # Send to Discord
            response = requests.post(
                webhook_url,
                json=message,
                timeout=10
            )

            if response.status_code == 204:
                print(f"  ✓ Discord notification sent")
                return True
            else:
                print(f"  ✗ Discord notification failed: HTTP {response.status_code}")
                return False

        except requests.RequestException as e:
            print(f"  ✗ Discord notification error: {e}")
            return False
        except Exception as e:
            print(f"  ✗ Unexpected error sending Discord notification: {e}")
            return False

    def _build_message(self, source_id: str, article: Article, previous_article: Optional[Article]) -> dict:
        """Build Discord message payload.

        Args:
            source_id: ID of the source
            article: New article
            previous_article: Previous article (optional)

        Returns:
            Discord message payload
        """
        # Determine site type and color
        site_emoji = "📰"
        embed_color = 0x5865F2  # Discord blurple
        if "nytimes.com" in article.url:
            site_emoji = "🗽"
            embed_color = 0x000000  # Black for NYT
        elif "washingtonpost.com" in article.url:
            site_emoji = "🏛️"
            embed_color = 0x14171A  # Dark for WaPo

        # Build embed fields
        fields = [
            {
                "name": "Title",
                "value": article.title,
                "inline": False
            },
            {
                "name": "URL",
                "value": f"[View Article]({article.url})",
                "inline": False
            }
        ]

        # Add publication time if available
        if article.published_time:
            fields.append({
                "name": "Published",
                "value": article.published_time,
                "inline": False
            })

        # Build embed
        embed = {
            "title": f"{site_emoji} New Article: {source_id}",
            "color": embed_color,
            "fields": fields
        }

        # Add footer with previous article info if available
        if previous_article:
            embed["footer"] = {
                "text": f"Previous: {previous_article.title}"
            }

        return {
            "content": f"{site_emoji} New article from {source_id}",
            "embeds": [embed]
        }


def get_notifier() -> DiscordNotifier:
    """Get the configured notifier.

    Returns:
        DiscordNotifier instance
    """
    return DiscordNotifier()
