#!/usr/bin/env python3
"""Test script for Slack notifications."""
import sys
import os

from src.notifications import SlackNotifier
from src.models import Article


def test_slack_notification():
    """Send a test notification to Slack."""
    print("=" * 60)
    print("Slack Notification Test")
    print("=" * 60)

    # Check if webhook URL is set
    webhook_url = os.environ.get('SLACK_WEBHOOK_URL')
    if not webhook_url:
        print("\n❌ SLACK_WEBHOOK_URL environment variable is not set")
        print("\nTo test, run:")
        print('  export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/..."')
        print("  python test_slack.py")
        return 1

    print(f"\n✓ Webhook URL configured")
    print(f"  URL: {webhook_url[:50]}...")

    # Create test articles
    print("\n" + "-" * 60)
    print("Creating test article...")
    print("-" * 60)

    new_article = Article(
        title="🧪 TEST: New Article Detection System Working!",
        url="https://github.com/test/article-monitoring",
        published_time="2025-01-28T15:00:00Z"
    )

    previous_article = Article(
        title="Old Article Title",
        url="https://github.com/test/old-article",
        published_time="2025-01-27T10:00:00Z"
    )

    print(f"\nNew article:")
    print(f"  Title: {new_article.title}")
    print(f"  URL: {new_article.url}")
    print(f"  Published: {new_article.published_time}")

    # Send notification
    print("\n" + "-" * 60)
    print("Sending test notification to Slack...")
    print("-" * 60)

    notifier = SlackNotifier(webhook_url)
    success = notifier.send(
        source_id="test-source",
        article=new_article,
        previous_article=previous_article
    )

    print()
    if success:
        print("=" * 60)
        print("✅ SUCCESS!")
        print("=" * 60)
        print("\nTest notification sent successfully!")
        print("Check your Slack channel for the message.")
        return 0
    else:
        print("=" * 60)
        print("❌ FAILED")
        print("=" * 60)
        print("\nFailed to send notification.")
        print("Check the error message above.")
        return 1


if __name__ == "__main__":
    sys.exit(test_slack_notification())
