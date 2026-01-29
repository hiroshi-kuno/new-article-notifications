#!/usr/bin/env python3
"""Test script for NYT scraper."""
import sys
from src.scrapers import get_scraper, ScraperError

def test_nyt():
    """Test NYT scraper."""
    url = "https://www.nytimes.com/by/agnes-chang"

    print(f"Testing NYT Scraper")
    print(f"{'='*60}")
    print(f"URL: {url}")
    print(f"{'='*60}")

    try:
        # Get scraper
        scraper = get_scraper(url)
        print(f"✓ Scraper: {scraper.__class__.__name__}")

        # Scrape
        print(f"\nFetching page...")
        article, etag, last_modified = scraper.scrape(url)

        if article:
            print(f"\n✓ SUCCESS! Article found:")
            print(f"  Title: {article.title}")
            print(f"  URL: {article.url}")
            if article.published_time:
                print(f"  Published: {article.published_time}")
            return 0
        else:
            print(f"\n✗ FAILED: No article found")
            return 1

    except Exception as e:
        print(f"\n✗ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(test_nyt())
