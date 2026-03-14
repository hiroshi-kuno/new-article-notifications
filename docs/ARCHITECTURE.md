# Architecture Documentation

This document explains the internal architecture of the NYT article monitoring system.

## System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                      GitHub Actions                          │
│                    (Scheduler/Orchestrator)                  │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        │ triggers hourly
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                   check_articles.py                          │
│                  (Main Orchestration)                        │
└─────┬───────────────────────────────────────────────────────┘
      │
      │ loads
      ▼
┌─────────────────────────────────────────────────────────────┐
│                  config/sources.json                         │
│            (List of reporter pages to monitor)               │
└──────────────────────────────────────────────────────────────┘
      │
      │ for each source
      ▼
┌─────────────────────────────────────────────────────────────┐
│                    StateManager                              │
│              (Load previous state)                           │
│                                                              │
│  state/source-1.json ◄──┐                                   │
│  state/source-2.json    │ read/write                        │
│  state/source-3.json ◄──┘                                   │
└──────────────────────────────────────────────────────────────┘
      │
      │ fetch & parse
      ▼
┌─────────────────────────────────────────────────────────────┐
│                  NYTReporterScraper                          │
│                                                              │
│  1. HTTP GET with conditional headers                       │
│     If-None-Match: etag                                     │
│     If-Modified-Since: date                                 │
│                                                              │
│  2. Handle 304 Not Modified                                 │
│     └─> Skip parsing                                        │
│                                                              │
│  3. Parse HTML (BeautifulSoup)                              │
│     ├─> Strategy 1: <ol> lists                             │
│     ├─> Strategy 2: <div> containers                       │
│     └─> Strategy 3: Fallback patterns                      │
│                                                              │
│  4. Extract Article                                          │
│     ├─> title                                               │
│     ├─> url                                                 │
│     └─> published_time                                      │
└──────────────────────────────────────────────────────────────┘
      │
      │ compare
      ▼
┌─────────────────────────────────────────────────────────────┐
│                   Change Detection                           │
│                                                              │
│  IF article.url != state.last_article.url:                  │
│     NEW ARTICLE DETECTED!                                   │
│     └─> Update state                                        │
│  ELSE:                                                       │
│     No change                                               │
└──────────────────────────────────────────────────────────────┘
      │
      │ save
      ▼
┌─────────────────────────────────────────────────────────────┐
│                    StateManager                              │
│                  (Save updated state)                        │
│                                                              │
│  state/source-1.json                                        │
│  state/source-2.json                                        │
│  state/source-3.json                                        │
└──────────────────────────────────────────────────────────────┘
      │
      │ commit & push
      ▼
┌─────────────────────────────────────────────────────────────┐
│                      Git Repository                          │
│              (Persistent state storage)                      │
└──────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. check_articles.py (Main Orchestrator)

**Responsibilities:**
- Load configuration
- Initialize state manager
- Loop through all enabled sources
- Handle errors per-source (isolation)
- Print summary statistics
- Exit with appropriate code

**Error Handling:**
- Individual source failures don't crash the system
- Errors are logged and counted
- System only exits with error if ALL sources fail

**Flow:**
```python
def main():
    config = load_config()
    state_manager = StateManager()

    for source in config.enabled_sources:
        try:
            check_source(source, state_manager)
        except Exception:
            log_error()
            continue  # Don't crash

    return exit_code
```

### 2. Config (src/config.py)

**Responsibilities:**
- Load sources.json
- Validate configuration
- Filter enabled sources

**Data Model:**
```json
{
  "sources": [
    {
      "url": "https://...",       // Target URL (NYT reporter page)
      "enabled": true             // On/off switch
    }
  ]
}
```

**Note:** Source ID is automatically extracted from the URL path.

### 3. StateManager (src/state_manager.py)

**Responsibilities:**
- Load state from JSON files
- Save state to JSON files
- Create state/ directory if needed
- Handle missing/corrupt state files

**State File Format:**
```json
{
  "source_id": "agnes-chang",
  "last_article": {
    "title": "...",
    "url": "...",
    "published_time": "..."
  },
  "last_checked": "2025-01-28T15:30:00Z",
  "etag": "W/\"abc123\"",
  "last_modified": "Mon, 28 Jan 2025 10:00:00 GMT",
  "error_count": 0,
  "last_error": null
}
```

**Key Features:**
- Atomic writes (write to temp, rename)
- Graceful handling of missing files
- ISO 8601 timestamps

### 4. Models (src/models.py)

**Article:**
```python
@dataclass
class Article:
    title: str
    url: str
    published_time: Optional[str]

    def __eq__(self, other):
        # Two articles equal if same URL
        return self.url == other.url
```

**SourceState:**
```python
@dataclass
class SourceState:
    source_id: str
    last_article: Optional[Article]
    last_checked: Optional[str]
    etag: Optional[str]
    last_modified: Optional[str]
    error_count: int
    last_error: Optional[str]
```

### 5. Scrapers (src/scrapers.py)

**NYTReporterScraper:**

#### Key Features

1. **Session Management**
   - Reuses HTTP connections
   - Maintains cookies
   - Single session per scraper instance

2. **Request Headers**
   ```python
   User-Agent: NYT-Article-Monitor/1.0 (...)
   Accept: text/html,application/xhtml+xml,...
   Accept-Language: en-US,en;q=0.9
   DNT: 1
   ```

3. **Conditional Requests**
   ```python
   If-None-Match: {etag}
   If-Modified-Since: {last_modified}
   ```

   If page unchanged, server returns 304, saving:
   - Bandwidth
   - Server CPU
   - Parsing time

4. **Timeout & Delay**
   - 15-second request timeout
   - 2-second delay between requests
   - No retries (fail fast)

#### Parsing Strategies

**Strategy 1: Article Lists**
- Look for `<ol>` tags
- Find `<a>` with href containing `/20XX/`
- Extract `<h3>`, `<h2>`, or `<h4>` for title
- Find `<time datetime="...">` for timestamp

**Strategy 2: Container Divs**
- Search `<div>`, `<section>`, `<article>` tags
- Find article links with year patterns
- Extract heading tags
- Look for time elements

**Strategy 3: Fallback**
- Find any link with year pattern
- Try to extract title from link text
- Check parent elements for headings
- No timestamp (set to None)

**Why Multiple Strategies?**
- DOM structure changes over time
- Different reporters may have different layouts
- Increases robustness
- Fails gracefully

### 6. GitHub Actions Workflow

**Trigger Mechanisms:**
1. **Schedule**: `cron: '0 * * * *'` (hourly)
2. **Manual**: workflow_dispatch
3. **Push**: For testing

**Steps:**
```yaml
1. Checkout code
2. Setup Python 3.11
3. Install dependencies (cached)
4. Run check_articles.py
5. Commit state changes
6. Push to repository
```

**Commit Strategy:**
```bash
git add state/
if changes exist:
    git commit -m "Update article check state [skip ci]"
    git push
```

**[skip ci] Tag:**
- Prevents infinite loop
- State commits don't trigger new workflows

## Data Flow

### First Run (Cold Start)

```
1. Load config
   └─> sources.json: [source1, source2]

2. For source1:
   ├─> Load state
   │   └─> No file exists → Create empty state
   ├─> Fetch page (no conditional headers)
   │   └─> HTTP 200 OK
   ├─> Parse HTML
   │   └─> Extract article A
   ├─> Compare
   │   └─> No previous article → Record as baseline
   └─> Save state
       └─> Write state/source1.json

3. For source2:
   └─> [same process]

4. Commit & push state files
```

### Subsequent Run (Warm State)

```
1. Load config
2. For source1:
   ├─> Load state
   │   └─> File exists → Load last_article = A
   ├─> Fetch page (with etag, last-modified)
   │   ├─> HTTP 304 → Skip parse
   │   │   └─> Return None
   │   └─> HTTP 200 → Parse
   │       └─> Extract article B
   ├─> Compare
   │   ├─> B == A → No change
   │   └─> B != A → NEW ARTICLE!
   └─> Save state
       └─> Update state/source1.json

3. Commit changes (if any)
```

## Extension Points

### Adding New Scrapers

1. Create new scraper class:
```python
class CustomScraper:
    def scrape(self, url, etag, last_modified):
        # Implement scraping logic
        return article, etag, last_modified
```

2. Register in factory:
```python
def get_scraper(source_type):
    if source_type == 'custom':
        return CustomScraper()
```

3. Add source with new type:
```json
{"type": "custom", ...}
```

### Adding Notifications

Hook into `check_articles.py`:

```python
def check_source(source, state_manager):
    # ... existing code ...

    if state.last_article != article:
        # NEW ARTICLE
        notify(
            title=f"New article from {source['name']}",
            body=article.title,
            url=article.url
        )
```

Notification options:
- Email (SMTP, SendGrid, SES)
- Slack webhook
- Discord webhook
- GitHub Issues
- Twitter API
- RSS feed

### Adding Analytics

Track metrics:
```python
# In check_source()
metrics.record({
    'source_id': source_id,
    'check_time': time.time(),
    'status': 'success' | 'error',
    'article_changed': bool,
    'http_status': 200 | 304 | 403,
    'parse_strategy': 1 | 2 | 3
})
```

Options:
- Log to file
- Send to CloudWatch
- Push to Prometheus
- Store in GitHub repo

## Performance Considerations

### Time Complexity

With N sources and D=2s delay:
- Best case (all 304): ~2N seconds
- Worst case (all parse): ~2N + parsing_time

For 10 sources:
- Best: ~20 seconds
- Worst: ~30 seconds

### Memory

- BeautifulSoup parses one page at a time
- Session reuse saves memory
- State files kept small (JSON)
- No caching of HTML content

### Network

- Conditional requests save bandwidth
- Session connection pooling
- No article body fetches
- Respectful delays

## Security Considerations

### Input Validation

- URLs validated by requests library
- JSON parsing with error handling
- No code execution from config

### Secrets

- No API keys required
- Uses GitHub's built-in GITHUB_TOKEN
- State files contain no sensitive data

### Rate Limiting

- Built-in delays
- No aggressive retries
- Clear identification (User-Agent)
- Honors 304 responses

## Future Enhancements

1. **Pluggable Notifications**
   - Abstract notification interface
   - Multiple notification backends
   - Per-source notification config

2. **Better DOM Resilience**
   - Machine learning for pattern detection
   - CSS selector learning
   - Automatic strategy updates

3. **Multi-site Support**
   - Washington Post
   - Guardian
   - Reuters
   - Configurable parsers

4. **Advanced State**
   - Article history (last N articles)
   - Detection of article updates
   - Author information

5. **Dashboard**
   - Web interface for viewing state
   - Real-time notifications
   - Historical graphs
