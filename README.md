# New Article Notifications

A Python-based system that monitors New York Times reporter pages and detects when new articles are published. The system runs automatically via GitHub Actions and persists state across runs.

## Overview

This system periodically checks reporter pages and RSS feeds (e.g., NYT reporter pages or Washington Post RSS feeds) and detects when the top (most recent) article changes. It's designed to be:

- **Reliable**: Prioritizes detecting updates over missing them
- **Respectful**: Minimizes load on NYT servers with conditional requests, delays, and no aggressive retries
- **Resilient**: Individual source failures don't crash the entire system
- **Maintainable**: Easy to add new reporter pages or extend to other sites

## How It Works

### Architecture

```
┌─────────────────────────────────────────────────────────┐
│ GitHub Actions (runs hourly)                            │
│  ├─ Load configuration (config/sources.json)            │
│  ├─ Load previous state (state/*.json)                  │
│  ├─ For each enabled source:                            │
│  │   ├─ Fetch reporter page (with conditional headers)  │
│  │   ├─ Parse top article (title, URL, time)            │
│  │   ├─ Compare with previous state                     │
│  │   └─ Update state if changed                         │
│  └─ Commit & push state changes back to repo            │
└─────────────────────────────────────────────────────────┘
```

### Components

- **`check_articles.py`**: Main orchestration script
- **`src/config.py`**: Configuration loader
- **`src/models.py`**: Data models (Article, SourceState)
- **`src/state_manager.py`**: State persistence layer
- **`src/scrapers.py`**: Web scraping logic with NYT-specific parsers and RSS feed support
- **`config/sources.json`**: List of reporter pages to monitor
- **`state/`**: Directory storing per-source state files

### Detection Logic

1. **Fetch page** using requests with conditional headers (If-None-Match, If-Modified-Since)
2. **Parse HTML** with BeautifulSoup using multiple fallback strategies
3. **Extract top article** (title, URL, publication time)
4. **Compare** with previous state:
   - If first run: Record the article
   - If article URL differs: Detect as NEW ARTICLE
   - If same: No change
5. **Save state** including caching headers for next run

## State Persistence

### How State Works

Each monitored source has a JSON file in `state/{source_id}.json` containing:

```json
{
  "source_id": "agnes-chang",
  "last_article": {
    "title": "Article Title Here",
    "url": "https://www.nytimes.com/2025/01/28/...",
    "published_time": "2025-01-28T10:00:00Z"
  },
  "last_checked": "2025-01-28T15:30:00Z",
  "etag": "W/\"abc123\"",
  "last_modified": "Mon, 28 Jan 2025 10:00:00 GMT",
  "error_count": 0,
  "last_error": null
}
```

### Persistence Mechanism

1. GitHub Actions checks out the repository
2. Script reads state files from `state/` directory
3. After checking all sources, updates state files
4. GitHub Actions commits and pushes changes back to `main` branch
5. **Important**: This approach does NOT rely on GitHub Actions cache

## Server Load Minimization

We're respectful of NYT servers through several mechanisms:

### 1. Conditional Requests

The system stores `ETag` and `Last-Modified` headers and sends them on subsequent requests:

```
If-None-Match: W/"abc123"
If-Modified-Since: Mon, 28 Jan 2025 10:00:00 GMT
```

If the page hasn't changed, NYT returns `304 Not Modified` with no body, saving bandwidth.

### 2. Clear User-Agent

```
NYT-Article-Monitor/1.0 (GitHub Actions; article-change-detection; +https://github.com)
```

This identifies our bot clearly, making it easy for site operators to contact us or block if needed.

### 3. Request Delays

Built-in 2-second delay between requests (configurable in `src/scrapers.py`).

### 4. Timeouts

All requests timeout after 15 seconds (no hanging connections).

### 5. No Aggressive Retries

Single attempt per source per run. If it fails, we record the error and move on.

### 6. Hourly Schedule

Checks run once per hour, not constantly.

### 7. No Article Body Fetching

We only fetch the reporter listing page, never individual articles.

## Adding New Reporter Pages

### Quick Start

1. Edit `config/sources.json`
2. Add a new entry:

```json
{
  "url": "https://www.nytimes.com/by/reporter-name",
  "enabled": true
}
```

3. Commit and push
4. The next GitHub Actions run will automatically pick it up

### Example

```json
{
  "sources": [
    {
      "url": "https://www.nytimes.com/by/agnes-chang",
      "enabled": true
    },
    {
      "url": "https://www.nytimes.com/by/john-doe",
      "enabled": true
    }
  ]
}
```

### Configuration Fields

- **`url`**: Full URL to the reporter page or RSS feed
  - NYT reporter pages: `https://www.nytimes.com/by/{reporter-name}`
  - RSS feeds: URLs containing `/rss/` or ending with `.rss`/`.xml`
- **`enabled`**: Set to `false` to temporarily disable without removing

**Note:** The source ID is automatically extracted from the URL (e.g., `agnes-chang` from `/by/agnes-chang`)

### Supported Sources

- **NYT Reporter Pages**: HTML scraping with multiple fallback strategies
- **RSS Feeds**: Standard RSS 2.0 and Atom feeds (Washington Post, Guardian, etc.)

The system automatically detects the source type from the URL pattern.

## Running Locally

### Prerequisites

- Python 3.11+
- pip

### Setup

```bash
# Clone the repository
git clone <your-repo-url>
cd new-article-notifications

# Install dependencies
pip install -r requirements.txt

# Run the checker
python check_articles.py
```

### Testing

Run manually to test:

```bash
python check_articles.py
```

Check the output and `state/` directory for results.

## GitHub Actions Setup

### Required Secrets

**For basic functionality:**
- **None!** The system uses the default `GITHUB_TOKEN` which is automatically provided by GitHub Actions.

**For Slack notifications (optional):**
- `SLACK_WEBHOOK_URL`: Slack Incoming Webhook URL for new article notifications

See `SLACK_SETUP.md` for detailed setup instructions.

### Permissions

The workflow needs `contents: write` permission to commit state changes. This is already configured in `.github/workflows/check-articles.yml`.

### Schedule

Currently runs every hour (`0 * * * *`). To change:

1. Edit `.github/workflows/check-articles.yml`
2. Modify the cron expression:

```yaml
schedule:
  - cron: '*/30 * * * *'  # Every 30 minutes
  # or
  - cron: '0 */2 * * *'   # Every 2 hours
```

### Manual Triggering

You can manually trigger a check:

1. Go to "Actions" tab in your GitHub repository
2. Select "Check for New Articles" workflow
3. Click "Run workflow"

## Extending the System

### Adding RSS Feeds

To add RSS feeds from other sites:

```json
{
  "url": "https://www.washingtonpost.com/arcio/rss/author/{author-name}/",
  "enabled": true
}
```

The system automatically detects RSS feeds by URL pattern. See `RSS_SUPPORT.md` for details.

### Adding New Site Types

The architecture supports multiple site types:

1. **Create a new scraper class** in `src/scrapers.py`:

```python
class CustomSiteScraper:
    def scrape(self, url, etag=None, last_modified=None):
        # Your scraping logic
        pass
```

2. **Register in the factory function**:

```python
def get_scraper(url: str):
    if 'nytimes.com/by/' in url:
        return NYTReporterScraper()
    elif 'example.com/author/' in url:
        return CustomSiteScraper()
    else:
        raise ValueError(f"No scraper for URL: {url}")
```

3. **Add sources**:

```json
{
  "url": "https://example.com/author/writer-name",
  "enabled": true
}
```

### Slack Notifications

Slack notifications are **built-in** and ready to use:

1. Create a Slack Incoming Webhook
2. Add `SLACK_WEBHOOK_URL` to GitHub Secrets
3. New articles will automatically notify Slack

See `SLACK_SETUP.md` for detailed instructions.

### Adding Other Notifications

To add email, Discord, or other notification methods, modify `src/notifications.py`:

```python
class EmailNotifier:
    def send(self, source_id: str, article: Article, previous_article: Optional[Article]):
        # Your email notification logic
        pass

# Register in check_articles.py
email_notifier = EmailNotifier()
```

## Troubleshooting

### No state changes being committed

Check that:
1. The workflow has `contents: write` permission
2. State files in `state/` directory are not in `.gitignore`
3. The git commands in the workflow are executing

### Scraper not finding articles

The NYT DOM structure may have changed. Check:
1. Visit the reporter page manually
2. Inspect the HTML structure
3. Update parsing strategies in `src/scrapers.py`
4. Consider adding a new `_parse_strategy_N()` method

### HTTP 403 or 429 errors

NYT may be rate-limiting. Consider:
1. Increasing `REQUEST_DELAY` in `src/scrapers.py`
2. Reducing check frequency in workflow
3. Verifying User-Agent is appropriate

### State file conflicts

If multiple workflow runs happen simultaneously, there might be git conflicts. The workflow should handle this, but if issues persist:
1. Ensure only one instance runs at a time
2. Consider adding concurrency control in workflow:

```yaml
concurrency:
  group: article-check
  cancel-in-progress: false
```

## License

[Specify your license here]

## Contributing

Contributions welcome! Please:
1. Test locally before submitting PR
2. Follow existing code style
3. Update README if adding new features

## Contact

[Your contact information or GitHub profile]
