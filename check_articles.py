#!/usr/bin/env python3
"""Main script to check for new articles on monitored sources."""
import sys
from datetime import datetime

from src.config import Config
from src.state_manager import StateManager
from src.scrapers import get_scraper, ScraperError
from src.notifications import get_notifier


def check_source(source: dict, state_manager: StateManager, notifier) -> bool:
    """Check a single source for updates.

    Args:
        source: Source configuration dictionary
        state_manager: StateManager instance
        notifier: Notifier instance

    Returns:
        True if check was successful, False otherwise
    """
    source_url = source['url']
    source_id = Config.extract_source_id(source_url)
    webhook_key = source.get('webhook')

    print(f"\n{'='*60}")
    print(f"Checking: {source_id}")
    print(f"URL: {source_url}")
    print(f"{'='*60}")

    state = state_manager.load_state(source_id)

    try:
        scraper = get_scraper(source_url)

        print(f"Fetching page...")
        article, new_etag, new_last_modified = scraper.scrape(
            source_url,
            etag=state.etag,
            last_modified=state.last_modified
        )

        state.etag = new_etag
        state.last_modified = new_last_modified

        if article is None:
            print(f"No changes detected (page not modified)")
            print(f"  → Notification: NOT sent (page not modified)")
            state_manager.save_state(state)
            return True

        print(f"\nTop article found:")
        print(f"  Title: {article.title}")
        print(f"  URL: {article.url}")
        if article.published_time:
            print(f"  Published: {article.published_time}")

        if state.last_article is None:
            print(f"\n  First check for this source - recording article")
            print(f"  → Notification: NOT sent (first check, establishing baseline)")
            state.last_article = article
            state.error_count = 0
            state.last_error = None
        elif state.last_article != article:
            print(f"\n  NEW ARTICLE DETECTED!")
            print(f"\n  Previous article:")
            print(f"    Title: {state.last_article.title}")
            print(f"    URL: {state.last_article.url}")
            print(f"\n  New article:")
            print(f"    Title: {article.title}")
            print(f"    URL: {article.url}")

            print(f"\n  → Notification: Attempting to send...")
            if notifier.is_enabled():
                success = notifier.send(source_id, article, state.last_article, webhook_key=webhook_key)
                if success:
                    print(f"  → Notification: SENT successfully")
                else:
                    print(f"  → Notification: FAILED to send (check error above)")
            else:
                print(f"  → Notification: NOT sent (no webhook configured)")

            state.last_article = article
            state.error_count = 0
            state.last_error = None
        else:
            print(f"\n  No change (same article as before)")
            print(f"  → Notification: NOT sent (article URL unchanged)")
            print(f"    Previous URL: {state.last_article.url}")
            print(f"    Current URL:  {article.url}")
            state.error_count = 0
            state.last_error = None

        state_manager.save_state(state)
        print(f"\nState saved successfully")
        return True

    except ScraperError as e:
        print(f"\nError scraping source: {e}")
        print(f"  → Notification: NOT sent (scraping error)")
        state.error_count += 1
        state.last_error = str(e)
        state_manager.save_state(state)
        return False

    except Exception as e:
        print(f"\nUnexpected error: {e}")
        print(f"  → Notification: NOT sent (unexpected error)")
        state.error_count += 1
        state.last_error = f"Unexpected: {str(e)}"
        state_manager.save_state(state)
        return False


def main():
    """Main entry point."""
    print(f"{'#'*60}")
    print(f"# New Article Notification Checker")
    print(f"# Started: {datetime.utcnow().isoformat()}Z")
    print(f"{'#'*60}")

    try:
        config = Config()
        sources = config.get_enabled_sources()

        if not sources:
            print("\nNo enabled sources found in configuration.")
            return 0

        print(f"\nFound {len(sources)} enabled source(s)")

        state_manager = StateManager()

        notifier = get_notifier()
        if notifier.is_enabled():
            print(f"\n✓ Notifications enabled")
            for key in notifier.configured_webhooks():
                print(f"  ✓ {key}")
        else:
            print(f"\n⚠ Notifications disabled (no WEBHOOK_URL_* env vars set)")

        results = []
        for source in sources:
            source_id = Config.extract_source_id(source['url'])
            success = check_source(source, state_manager, notifier)
            results.append((source_id, success))

        print(f"\n{'#'*60}")
        print(f"# Summary")
        print(f"{'#'*60}")

        success_count = sum(1 for _, success in results if success)
        fail_count = len(results) - success_count

        print(f"\nTotal sources: {len(results)}")
        print(f"Successful: {success_count}")
        print(f"Failed: {fail_count}")

        if fail_count > 0:
            print(f"\nFailed sources:")
            for result_id, success in results:
                if not success:
                    print(f"  - {result_id}")

        print(f"\nCompleted: {datetime.utcnow().isoformat()}Z")

        if fail_count == len(results):
            print("\nAll sources failed!")
            return 1

        return 0

    except Exception as e:
        print(f"\nFatal error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
