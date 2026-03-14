#!/usr/bin/env python3
"""Test script for NYT Discord webhook notifications."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.notifications import DiscordNotifier
from src.models import Article


def test_nyt_webhook_notification():
    """Send a test notification to the NYT-specific Discord webhook."""
    print("=" * 60)
    print("NYT Webhook Notification Test")
    print("=" * 60)

    # Check if NYT webhook URL is set
    nyt_webhook_url = os.environ.get('WEBHOOK_URL_NYT')
    if not nyt_webhook_url:
        print("\n❌ WEBHOOK_URL_NYT environment variable is not set")
        print("\nTo test, run:")
        print('  export WEBHOOK_URL_NYT="https://discord.com/api/webhooks/..."')
        print("  python test_nyt_webhook.py")
        return 1

    print(f"\n✓ NYT Webhook URL configured")
    print(f"  URL: {nyt_webhook_url[:50]}...")

    # Create test NYT articles
    print("\n" + "-" * 60)
    print("Creating test NYT article...")
    print("-" * 60)

    new_article = Article(
        title="🧪 TEST: NYT Webhook Detection Working!",
        url="https://www.nytimes.com/by/test-author",
        published_time="2026-03-14T15:00:00Z"
    )

    previous_article = Article(
        title="Previous NYT Article Title",
        url="https://www.nytimes.com/by/test-author/old",
        published_time="2026-03-13T10:00:00Z"
    )

    print(f"\nNew article:")
    print(f"  Title: {new_article.title}")
    print(f"  URL: {new_article.url}")
    print(f"  Published: {new_article.published_time}")

    # Send notification
    print("\n" + "-" * 60)
    print("Sending test notification to NYT webhook...")
    print("-" * 60)

    notifier = DiscordNotifier()
    success = notifier.send(
        source_id="nyt-test",
        article=new_article,
        previous_article=previous_article
    )

    print()
    if success:
        print("=" * 60)
        print("✅ SUCCESS!")
        print("=" * 60)
        print("\nTest notification sent to NYT webhook successfully!")
        print("Check the NYT Discord channel for the message.")
        return 0
    else:
        print("=" * 60)
        print("❌ FAILED")
        print("=" * 60)
        print("\nFailed to send notification.")
        print("Check the error message above.")
        return 1


if __name__ == "__main__":
    sys.exit(test_nyt_webhook_notification())
