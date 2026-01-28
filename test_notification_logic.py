#!/usr/bin/env python3
"""Test notification logic without actual scraping."""
import sys
import os

# Disable Slack notifications for this test
if 'SLACK_WEBHOOK_URL' in os.environ:
    del os.environ['SLACK_WEBHOOK_URL']

from src.config import Config
from src.state_manager import StateManager
from src.models import Article, SourceState
from src.notifications import get_notifier


def simulate_check(scenario_name: str, state: SourceState, article: Article, notifier):
    """Simulate the check logic."""
    print(f"\n{'='*60}")
    print(f"Scenario: {scenario_name}")
    print(f"{'='*60}")

    print(f"\nCurrent state:")
    if state.last_article:
        print(f"  Last article URL: {state.last_article.url}")
    else:
        print(f"  Last article: None (first run)")

    print(f"\nNew article:")
    if article:
        print(f"  URL: {article.url}")
    else:
        print(f"  None (304 Not Modified)")

    print(f"\n--- Decision Logic ---")

    # Simulate the logic from check_articles.py
    if article is None:
        print(f"Page not modified (304)")
        print(f"→ Notification: NOT sent (page not modified)")

    elif state.last_article is None:
        print(f"First check for this source")
        print(f"→ Notification: NOT sent (first check, establishing baseline)")

    elif state.last_article != article:
        print(f"NEW ARTICLE DETECTED!")
        print(f"  Previous: {state.last_article.url}")
        print(f"  Current:  {article.url}")
        print(f"→ Notification: Attempting to send...")
        if notifier.is_enabled():
            print(f"  → Notification: SENT successfully")
        else:
            print(f"  → Notification: NOT sent (SLACK_WEBHOOK_URL not configured)")

    else:
        print(f"No change (same article)")
        print(f"  URL: {article.url}")
        print(f"→ Notification: NOT sent (article URL unchanged)")


def main():
    """Run all scenarios."""
    print("="*60)
    print("NOTIFICATION LOGIC TEST")
    print("="*60)

    notifier = get_notifier()
    print(f"\nSlack notifications enabled: {notifier.is_enabled()}")

    # Scenario 1: First run (no previous state)
    state1 = SourceState(source_id="test-1")
    article1 = Article(
        title="First Article",
        url="https://example.com/article-1",
        published_time="2025-01-28T10:00:00Z"
    )
    simulate_check("First Run", state1, article1, notifier)

    # Scenario 2: Second run, same article
    state2 = SourceState(
        source_id="test-2",
        last_article=Article(
            title="Old Article",
            url="https://example.com/article-1",
            published_time="2025-01-28T10:00:00Z"
        )
    )
    article2 = Article(
        title="Old Article",
        url="https://example.com/article-1",  # Same URL
        published_time="2025-01-28T10:00:00Z"
    )
    simulate_check("Same Article (No Change)", state2, article2, notifier)

    # Scenario 3: New article detected
    state3 = SourceState(
        source_id="test-3",
        last_article=Article(
            title="Old Article",
            url="https://example.com/article-1",
            published_time="2025-01-28T10:00:00Z"
        )
    )
    article3 = Article(
        title="New Article",
        url="https://example.com/article-2",  # Different URL
        published_time="2025-01-28T12:00:00Z"
    )
    simulate_check("New Article Detected", state3, article3, notifier)

    # Scenario 4: 304 Not Modified
    state4 = SourceState(
        source_id="test-4",
        last_article=Article(
            title="Old Article",
            url="https://example.com/article-1",
            published_time="2025-01-28T10:00:00Z"
        )
    )
    article4 = None  # 304 response
    simulate_check("304 Not Modified", state4, article4, notifier)

    print(f"\n{'='*60}")
    print("TEST COMPLETE")
    print(f"{'='*60}")


if __name__ == "__main__":
    sys.exit(main())
