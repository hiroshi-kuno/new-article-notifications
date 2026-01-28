"""Notification handlers for new articles."""
import os
from typing import Optional
import requests

from .models import Article


class NotificationError(Exception):
    """Base exception for notification errors."""
    pass


class SlackNotifier:
    """Send notifications to Slack via Incoming Webhooks."""

    def __init__(self, webhook_url: Optional[str] = None):
        """Initialize Slack notifier.

        Args:
            webhook_url: Slack webhook URL (if None, reads from SLACK_WEBHOOK_URL env var)
        """
        self.webhook_url = webhook_url or os.environ.get('SLACK_WEBHOOK_URL')

    def is_enabled(self) -> bool:
        """Check if Slack notifications are enabled.

        Returns:
            True if webhook URL is configured
        """
        return bool(self.webhook_url)

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
            # Build Slack message
            message = self._build_message(source_id, article, previous_article)

            # Send to Slack
            response = requests.post(
                self.webhook_url,
                json=message,
                timeout=10
            )

            if response.status_code == 200:
                print(f"  ✓ Slack notification sent")
                return True
            else:
                print(f"  ✗ Slack notification failed: HTTP {response.status_code}")
                return False

        except requests.RequestException as e:
            print(f"  ✗ Slack notification error: {e}")
            return False
        except Exception as e:
            print(f"  ✗ Unexpected error sending Slack notification: {e}")
            return False

    def _build_message(self, source_id: str, article: Article, previous_article: Optional[Article]) -> dict:
        """Build Slack message payload.

        Args:
            source_id: ID of the source
            article: New article
            previous_article: Previous article (optional)

        Returns:
            Slack message payload
        """
        # Determine site type
        site_emoji = "📰"
        if "nytimes.com" in article.url:
            site_emoji = "🗽"
        elif "washingtonpost.com" in article.url:
            site_emoji = "🏛️"

        # Build text
        text = f"{site_emoji} *New article from {source_id}*"

        # Build blocks for rich formatting
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{site_emoji} New Article: {source_id}",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Title:*\n{article.title}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*URL:*\n<{article.url}|View Article>"
                    }
                ]
            }
        ]

        # Add publication time if available
        if article.published_time:
            blocks.append({
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Published:*\n{article.published_time}"
                    }
                ]
            })

        # Add previous article info if available
        if previous_article:
            blocks.append({
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"Previous: _{previous_article.title}_"
                    }
                ]
            })

        # Add divider
        blocks.append({"type": "divider"})

        return {
            "text": text,
            "blocks": blocks
        }


def get_notifier() -> SlackNotifier:
    """Get the configured notifier.

    Returns:
        SlackNotifier instance
    """
    return SlackNotifier()
