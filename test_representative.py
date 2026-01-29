#!/usr/bin/env python3
"""Test representative sources from each type."""
import sys
from src.config import Config
from src.state_manager import StateManager
from src.scrapers import get_scraper, ScraperError
from src.notifications import get_notifier

def test_source(source_url: str) -> bool:
    """Test a single source."""
    from src.config import Config

    source_id = Config.extract_source_id(source_url)

    print(f"\n{'='*60}")
    print(f"Testing: {source_id}")
    print(f"URL: {source_url}")
    print(f"{'='*60}")

    try:
        # Get scraper
        scraper = get_scraper(source_url)
        print(f"✓ Scraper: {scraper.__class__.__name__}")

        # Fetch and parse
        print(f"\nFetching page...")
        article, etag, last_modified = scraper.scrape(source_url)

        if article:
            print(f"\n✓ Article found:")
            print(f"  Title: {article.title}")
            print(f"  URL: {article.url}")
            if article.published_time:
                print(f"  Published: {article.published_time}")
            return True
        else:
            print(f"\n✗ No article found")
            return False

    except ScraperError as e:
        print(f"\n✗ Scraper error: {e}")
        return False
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Test representative sources."""
    print("="*60)
    print("Testing Representative Sources")
    print("="*60)

    # Representative sources from each type
    test_sources = [
        # NYT reporters
        ("https://www.nytimes.com/by/agnes-chang", "NYT Reporter"),
        ("https://www.nytimes.com/by/charlie-smart", "NYT Reporter"),

        # Washington Post RSS
        ("https://www.washingtonpost.com/arcio/rss/author/Aaron-Steckelberg/", "WaPo RSS"),

        # New sites
        ("https://gijn.org/topic/data-journalism-top-10/", "GIJN"),
        ("https://www.datawrapper.de/blog/category/data-vis-dispatch", "Datawrapper"),
    ]

    results = []
    for url, label in test_sources:
        success = test_source(url)
        results.append((label, url, success))

    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")

    for label, url, success in results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{status}: {label}")

    # Overall result
    all_passed = all(success for _, _, success in results)
    passed_count = sum(1 for _, _, success in results if success)
    total_count = len(results)

    print(f"\nResult: {passed_count}/{total_count} tests passed")

    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
