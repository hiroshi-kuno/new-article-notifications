# Testing Guide

This document explains how to test the New Article Notification system locally before deploying to GitHub Actions.

## Prerequisites

```bash
# Python 3.11 or higher
python3 --version

# Install dependencies
pip install -r requirements.txt
```

## Local Testing

### 1. Basic Functionality Test

Run the checker once:

```bash
python check_articles.py
```

Expected output:
```
############################################################
# New Article Notification Checker
# Started: 2025-01-28T15:30:00.000000Z
############################################################

Found 1 enabled source(s)

============================================================
Checking: agnes-chang
URL: https://www.nytimes.com/by/agnes-chang
============================================================
Fetching page...

Top article found:
  Title: [Article title]
  URL: https://www.nytimes.com/...
  Published: 2025-01-28T...

  First check for this source - recording article

State saved successfully

############################################################
# Summary
############################################################

Total sources: 1
Successful: 1
Failed: 0

Completed: 2025-01-28T15:30:05.000000Z
```

### 2. Verify State Creation

Check that state file was created:

```bash
ls -la state/
cat state/agnes-chang.json
```

The file should contain:
- `source_id`
- `last_article` (with title, URL, published_time)
- `last_checked` timestamp
- `etag` and `last_modified` (if provided by server)

### 3. Test Change Detection

Run again immediately:

```bash
python check_articles.py
```

You should see:
```
  Page not modified (304), skipping parse
```

Or:
```
  No change (same article as before)
```

### 4. Test Multiple Sources

Add another source to `config/sources.json`:

```json
{
  "sources": [
    {
      "url": "https://www.nytimes.com/by/agnes-chang",
      "enabled": true
    },
    {
      "url": "https://www.nytimes.com/by/some-other-reporter",
      "enabled": true
    }
  ]
}
```

Run and verify both sources are checked:

```bash
python check_articles.py
```

### 5. Test Error Handling

Add an invalid URL:

```json
{
  "url": "https://www.nytimes.com/by/this-does-not-exist-12345",
  "enabled": true
}
```

Run and verify:
- Error is logged
- Other sources still process
- Script doesn't crash

```bash
python check_articles.py
echo "Exit code: $?"
```

Exit code should be 0 (unless all sources failed).

### 6. Test Disabled Source

Disable a source:

```json
{
  "url": "https://www.nytimes.com/by/test",
  "enabled": false
}
```

Verify it's not checked:

```bash
python check_articles.py
```

## Testing Specific Components

### Test Configuration Loading

```python
from src.config import Config

config = Config()
sources = config.get_enabled_sources()
print(f"Enabled sources: {len(sources)}")
for source in sources:
    source_id = Config.extract_source_id(source['url'])
    print(f"  - {source_id}: {source['url']}")
```

### Test State Management

```python
from src.state_manager import StateManager
from src.models import Article, SourceState

# Create state manager
sm = StateManager()

# Load (or create new) state
state = sm.load_state("test-id")
print(f"State: {state.source_id}")

# Create article
article = Article(
    title="Test Article",
    url="https://example.com/test",
    published_time="2025-01-28T10:00:00Z"
)

# Update and save state
state.last_article = article
sm.save_state(state)

# Reload and verify
state2 = sm.load_state("test-id")
print(f"Loaded article: {state2.last_article.title}")
```

### Test Scraper

```python
from src.scrapers import NYTReporterScraper

scraper = NYTReporterScraper()
url = "https://www.nytimes.com/by/agnes-chang"

try:
    article, etag, last_modified = scraper.scrape(url)
    if article:
        print(f"Title: {article.title}")
        print(f"URL: {article.url}")
        print(f"Published: {article.published_time}")
        print(f"ETag: {etag}")
        print(f"Last-Modified: {last_modified}")
    else:
        print("No article found or page not modified")
except Exception as e:
    print(f"Error: {e}")
```

## Manual DOM Inspection

If scraping fails, inspect the HTML manually:

```python
import requests
from bs4 import BeautifulSoup

url = "https://www.nytimes.com/by/agnes-chang"
headers = {
    'User-Agent': 'Mozilla/5.0 (compatible; TestBot/1.0)'
}

response = requests.get(url, headers=headers, timeout=15)
soup = BeautifulSoup(response.text, 'html.parser')

# Save HTML for inspection
with open('debug.html', 'w', encoding='utf-8') as f:
    f.write(soup.prettify())

print("HTML saved to debug.html")

# Try finding article elements
print("\nLooking for <ol> tags:")
for ol in soup.find_all('ol')[:3]:
    print(f"  Found: {ol.get('class')}")

print("\nLooking for article links:")
links = soup.find_all('a', href=lambda x: x and '/2025/' in x)
for link in links[:5]:
    print(f"  {link.get('href')}")
    title = link.find(['h1', 'h2', 'h3'])
    if title:
        print(f"    Title: {title.get_text(strip=True)[:50]}...")
```

## GitHub Actions Testing

### 1. Test Workflow Syntax

```bash
# Install actionlint (workflow linter)
# macOS: brew install actionlint
# Linux: Download from https://github.com/rhysd/actionlint

actionlint .github/workflows/check-articles.yml
```

### 2. Test Locally with Act

```bash
# Install act (run GitHub Actions locally)
# macOS: brew install act
# Linux: https://github.com/nektos/act

# Run the workflow
act workflow_dispatch

# Or test the scheduled run
act schedule
```

### 3. Enable GitHub Actions

1. Push code to GitHub
2. Go to repository → Settings → Actions → General
3. Ensure "Allow all actions" is enabled
4. Go to Actions tab
5. Click "Check for New Articles"
6. Click "Run workflow"
7. Monitor the run

### 4. Verify State Persistence

After the first run:

```bash
git pull
ls state/
cat state/*.json
```

Verify:
- State files exist
- Contain expected data
- Committed by github-actions[bot]

## Troubleshooting Tests

### ImportError or ModuleNotFoundError

```bash
# Ensure you're in the project root
pwd

# Verify Python can find src/
python -c "import sys; print(sys.path)"

# Try running with explicit path
PYTHONPATH=. python check_articles.py
```

### HTTP 403 Forbidden

NYT might be blocking your IP. Try:

1. Wait a few minutes
2. Use a VPN
3. Check if you're making too many requests

### No Articles Found

The DOM structure may have changed. Run manual inspection (see above) and update parsing strategies in `src/scrapers.py`.

### State Not Committing in GitHub Actions

Check:
1. Repository permissions (Settings → Actions → General → Workflow permissions)
2. Set to "Read and write permissions"
3. Workflow has `permissions: contents: write`

## Performance Testing

Test with multiple sources:

```bash
# Add 5-10 sources to config
time python check_articles.py
```

With 10 sources and 2-second delay, expect ~20-30 seconds total.

## Continuous Testing

Set up a simple loop for continuous monitoring:

```bash
# Check every 5 minutes for 1 hour
for i in {1..12}; do
  echo "=== Run $i ==="
  python check_articles.py
  echo "Sleeping 5 minutes..."
  sleep 300
done
```

Monitor:
- State file changes
- Error patterns
- 304 responses (good! saves bandwidth)
- Detection accuracy
