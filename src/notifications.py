"""Notification handlers for new articles."""
import os
from typing import Optional
import requests

from .models import Article


class DiscordNotifier:
    """Send notifications to Discord via Incoming Webhooks."""

    def __init__(self):
        """Initialize Discord notifier.

        Loads all WEBHOOK_URL_* environment variables automatically.
        Also supports legacy DISCORD_WEBHOOK_URL as the default fallback.
        """
        self._webhooks: dict[str, str] = {}

        # Legacy default webhook
        if url := os.environ.get('DISCORD_WEBHOOK_URL'):
            self._webhooks['DISCORD_WEBHOOK_URL'] = url

        # All source-specific webhooks
        for key, value in os.environ.items():
            if key.startswith('WEBHOOK_URL_') and value:
                self._webhooks[key] = value

    def is_enabled(self) -> bool:
        """Check if any webhook is configured."""
        return bool(self._webhooks)

    def configured_webhooks(self) -> list[str]:
        """Return list of configured webhook keys."""
        return list(self._webhooks.keys())

    def send(
        self,
        source_id: str,
        article: Article,
        previous_article: Optional[Article] = None,
        webhook_key: Optional[str] = None,
    ) -> bool:
        """Send a notification about a new article.

        Args:
            source_id: ID of the source
            article: New article
            previous_article: Previous article (optional)
            webhook_key: Env var name of the webhook to use (e.g. 'WEBHOOK_URL_NYT').
                         Falls back to DISCORD_WEBHOOK_URL if not specified.

        Returns:
            True if notification sent successfully, False otherwise
        """
        if webhook_key:
            webhook_url = self._webhooks.get(webhook_key)
            if not webhook_url:
                print(f"  ✗ Webhook {webhook_key} not configured")
                return False
        else:
            webhook_url = self._webhooks.get('DISCORD_WEBHOOK_URL')
            if not webhook_url:
                print(f"  ✗ No default webhook URL (DISCORD_WEBHOOK_URL) configured")
                return False

        try:
            message = self._build_message(source_id, article, previous_article)
            response = requests.post(webhook_url, json=message, timeout=10)

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

    def _build_message(
        self,
        source_id: str,
        article: Article,
        previous_article: Optional[Article],
    ) -> dict:
        """Build Discord message payload."""
        site_emoji = "📰"
        embed_color = 0x5865F2  # Discord blurple
        if "nytimes.com" in article.url:
            site_emoji = "🗽"
            embed_color = 0x000000
        elif "washingtonpost.com" in article.url:
            site_emoji = "🏛️"
            embed_color = 0x14171A

        fields = [
            {"name": "Title", "value": article.title, "inline": False},
            {"name": "URL", "value": f"[View Article]({article.url})", "inline": False},
        ]

        if article.published_time:
            fields.append({"name": "Published", "value": article.published_time, "inline": False})

        embed = {
            "title": f"{site_emoji} New Article: {source_id}",
            "color": embed_color,
            "fields": fields,
        }

        if previous_article:
            embed["footer"] = {"text": f"Previous: {previous_article.title}"}

        return {
            "content": f"{site_emoji} New article from {source_id}",
            "embeds": [embed],
        }


def get_notifier() -> DiscordNotifier:
    """Get the configured notifier."""
    return DiscordNotifier()
