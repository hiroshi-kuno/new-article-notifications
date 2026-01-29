#!/usr/bin/env python3
"""Test script for new sites (GIJN and Datawrapper)."""
import sys
from src.scrapers import get_scraper, ScraperError

def test_site(url: str):
    """Test scraping a site."""
    print(f"\n{'='*60}")
    print(f"Testing: {url}")
    print(f"{'='*60}")

    try:
        # Get appropriate scraper
        scraper = get_scraper(url)
        print(f"✓ Scraper: {scraper.__class__.__name__}")

        # Scrape the page
        print(f"\nFetching page...")
        article, etag, last_modified = scraper.scrape(url)

        if article:
            print(f"\n✓ SUCCESS! Article found:")
            print(f"  Title: {article.title}")
            print(f"  URL: {article.url}")
            if article.published_time:
                print(f"  Published: {article.published_time}")
            return True
        else:
            print(f"\n✗ FAILED: No article found")
            return False

    except ScraperError as e:
        print(f"\n✗ FAILED: Scraper error: {e}")
        return False
    except Exception as e:
        print(f"\n✗ FAILED: Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main entry point."""
    print("Testing New Sites")
    print("="*60)

    sites = [
        "https://gijn.org/topic/data-journalism-top-10/",
        "https://www.datawrapper.de/blog/category/data-vis-dispatch"
    ]

    results = []
    for site in sites:
        success = test_site(site)
        results.append((site, success))

    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    for site, success in results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{status}: {site}")

    # Exit code
    all_passed = all(success for _, success in results)
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
