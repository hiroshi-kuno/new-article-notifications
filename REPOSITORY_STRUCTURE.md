# Repository Structure

Complete file structure of the NYT Article Monitor project.

## Directory Tree

```
new-article-notifications/
├── .github/
│   ├── workflows/
│   │   └── check-articles.yml       # GitHub Actions workflow (hourly checks)
│   └── FUNDING.yml                   # Optional: Project funding links
│
├── config/
│   └── sources.json                  # Reporter pages to monitor (USER EDITABLE)
│
├── src/
│   ├── __init__.py                   # Package initialization
│   ├── config.py                     # Configuration loader
│   ├── models.py                     # Data models (Article, SourceState)
│   ├── scrapers.py                   # Web scraping logic
│   └── state_manager.py              # State persistence layer
│
├── state/
│   ├── .gitkeep                      # Keeps directory in git
│   ├── {source-id}.json              # State files (auto-generated)
│   └── agnes-chang.json.example      # Example state file
│
├── check_articles.py                 # Main entry point (executable)
├── requirements.txt                  # Python dependencies
├── .gitignore                        # Git ignore patterns
│
├── README.md                         # Main documentation
├── QUICKSTART.md                     # Quick start guide
├── TESTING.md                        # Testing guide
├── ARCHITECTURE.md                   # Architecture documentation
├── REPOSITORY_STRUCTURE.md           # This file
└── LICENSE                           # MIT License
```

## File Descriptions

### Configuration Files

#### `config/sources.json` ⭐ USER EDITABLE
Configuration file listing all reporter pages to monitor.

```json
{
  "sources": [
    {
      "url": "https://www.nytimes.com/by/reporter-name",
      "enabled": true
    }
  ]
}
```

**Fields:**
- `url`: Reporter page URL (NYT reporter pages only)
- `enabled`: Boolean to enable/disable without removing

**Note:** Source ID is automatically extracted from URL (e.g., `reporter-name` from `/by/reporter-name`)

### Source Code

#### `check_articles.py` (285 lines)
Main orchestration script that:
- Loads configuration
- Initializes state manager
- Checks each source for updates
- Handles errors gracefully
- Prints detailed logs
- Saves state
- Returns appropriate exit code

**Key Functions:**
- `main()`: Entry point
- `check_source()`: Process single source

#### `src/config.py` (35 lines)
Configuration management:
- Loads `sources.json`
- Validates structure
- Filters enabled sources

**Key Class:**
- `Config`: Configuration loader

#### `src/models.py` (70 lines)
Data models using Python dataclasses:

**Classes:**
- `Article`: Represents a news article
  - `title`: str
  - `url`: str
  - `published_time`: Optional[str]
  - `__eq__()`: Compare by URL

- `SourceState`: Tracks source state
  - `source_id`: str
  - `last_article`: Optional[Article]
  - `last_checked`: Optional[str]
  - `etag`: Optional[str]
  - `last_modified`: Optional[str]
  - `error_count`: int
  - `last_error`: Optional[str]

#### `src/state_manager.py` (60 lines)
State persistence layer:
- Reads/writes JSON state files
- Creates state directory if needed
- Handles missing/corrupt files
- Updates timestamps automatically

**Key Class:**
- `StateManager`: State file manager
  - `load_state(source_id)`: Load state
  - `save_state(state)`: Save state

#### `src/scrapers.py` (280 lines)
Web scraping with BeautifulSoup:

**Constants:**
- `USER_AGENT`: Clear bot identification
- `REQUEST_TIMEOUT`: 15 seconds
- `REQUEST_DELAY`: 2 seconds between requests

**Classes:**
- `ScraperError`: Base exception
- `NYTReporterScraper`: NYT-specific scraper
  - `fetch_page()`: HTTP GET with conditionals
  - `parse_top_article()`: Extract article
  - `_parse_strategy_1/2/3()`: Multiple parsing strategies
  - `scrape()`: Main entry point

**Functions:**
- `get_scraper(type)`: Factory function

### GitHub Actions

#### `.github/workflows/check-articles.yml` (50 lines)
Automated workflow configuration:

**Triggers:**
- Schedule: Every hour (`0 * * * *`)
- Manual: workflow_dispatch
- Push: On push to main (for testing)

**Steps:**
1. Checkout repository
2. Setup Python 3.11
3. Install dependencies (with caching)
4. Run check_articles.py
5. Commit state changes
6. Push to repository

**Permissions:**
- `contents: write` (required for commits)

### State Files

#### `state/{source-id}.json` (auto-generated)
Per-source state tracking:

**Created by:** StateManager during first check
**Updated by:** Every check run
**Format:** JSON

**Contains:**
- Last seen article details
- Caching headers (ETag, Last-Modified)
- Check timestamp
- Error tracking

**Example:** See `state/agnes-chang.json.example`

### Documentation

#### `README.md` (400+ lines)
Comprehensive main documentation:
- Overview and architecture
- How it works
- State persistence explanation
- Server load minimization
- Adding new sources
- Running locally
- GitHub Actions setup
- Extending the system
- Troubleshooting

#### `QUICKSTART.md` (150 lines)
Get started in 5 minutes:
- Installation
- Configuration
- Testing
- Deployment
- Common commands
- What to expect

#### `TESTING.md` (300+ lines)
Comprehensive testing guide:
- Local testing procedures
- Component testing
- Manual DOM inspection
- GitHub Actions testing
- Troubleshooting
- Performance testing

#### `ARCHITECTURE.md` (500+ lines)
Deep technical documentation:
- System diagrams
- Component details
- Data flow
- Extension points
- Performance considerations
- Security considerations
- Future enhancements

#### `REPOSITORY_STRUCTURE.md` (this file)
Complete repository structure documentation.

### Other Files

#### `requirements.txt`
Python dependencies:
```
requests>=2.31.0
beautifulsoup4>=4.12.0
```

#### `.gitignore`
Standard Python .gitignore:
- `__pycache__/`
- `*.pyc`
- Virtual environments
- IDE files
- OS files

#### `LICENSE`
MIT License (permissive open source).

## File Statistics

```
Total Files: ~20
Total Lines of Code: ~1,000
Python Code: ~700 lines
Documentation: ~1,500 lines
Configuration: ~50 lines

Size Breakdown:
- src/: ~450 lines (models, state, scraper, config)
- check_articles.py: ~285 lines
- Documentation: ~1,500 lines
- Configuration: ~50 lines
```

## Dependencies

### Runtime
- **Python 3.11+**: Language runtime
- **requests**: HTTP client library
- **beautifulsoup4**: HTML parsing

### Development (optional)
- **pytest**: Testing framework
- **black**: Code formatter
- **mypy**: Type checker
- **actionlint**: GitHub Actions linter

### External Services
- **GitHub Actions**: Automation platform
- **Git**: Version control & state storage

## Git Workflow

### Main Branch Protection
Recommended settings:
- Require pull request reviews: Optional
- Require status checks: Optional
- Allow force pushes: No
- Allow deletions: No

### Branch Structure
```
main (default)
├── state/ (auto-updated by GitHub Actions)
├── config/ (manually updated)
└── src/ (manually updated)
```

### Commit Patterns
```
User commits:
- "Add new reporter: John Doe"
- "Update scraper parsing strategy"
- "Fix error handling"

Bot commits:
- "Update article check state [skip ci]"
```

## State Storage Pattern

### Why Git for State?
1. **Free**: No database costs
2. **Durable**: Git history is backup
3. **Auditable**: See all state changes
4. **Simple**: No external services
5. **Portable**: Works anywhere

### State File Lifecycle
```
1. First run
   └─> Create state/source-id.json

2. Subsequent runs
   ├─> Read current state
   ├─> Check for updates
   ├─> Update if changed
   └─> Commit & push

3. History
   └─> Git log shows all state changes
```

## Execution Flow

```
GitHub Actions (scheduler)
        ↓
    Trigger workflow
        ↓
    Setup environment
        ↓
    check_articles.py
        ↓
    Load config/sources.json
        ↓
    For each source:
        ├─> Load state/source-id.json
        ├─> Fetch & parse webpage
        ├─> Compare with previous
        ├─> Detect changes
        └─> Save state/source-id.json
        ↓
    Git commit & push
        ↓
    Complete
```

## Extension Points

### Easy Extensions
- Add reporter pages (edit config/sources.json)
- Change check frequency (edit workflow cron)
- Disable sources (set enabled: false)

### Medium Extensions
- Add notifications (modify check_articles.py)
- Add logging (add logging module)
- Add metrics (add metrics tracking)

### Advanced Extensions
- New site types (add new scraper class)
- Web dashboard (add Flask/FastAPI app)
- Database storage (replace StateManager)
- Real-time monitoring (add websocket server)

## Development Setup

```bash
# Clone repository
git clone <repo-url>
cd new-article-notifications

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt

# Install development dependencies (optional)
pip install pytest black mypy

# Run tests
python check_articles.py

# Format code
black src/ check_articles.py

# Type checking
mypy src/
```

## Production Deployment

### Option 1: GitHub Actions (Recommended)
Already configured! Just push to GitHub.

### Option 2: Cron Job
```bash
# Add to crontab
0 * * * * cd /path/to/repo && python check_articles.py
```

### Option 3: Docker
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "check_articles.py"]
```

### Option 4: Cloud Functions
Adapt `check_articles.py` to run as:
- AWS Lambda
- Google Cloud Functions
- Azure Functions

## Maintenance

### Regular Tasks
- Monitor GitHub Actions runs
- Review state/ changes
- Update sources in config
- Check for errors in logs

### Periodic Tasks
- Update dependencies
- Test scraper still works
- Review and update DOM parsing strategies
- Check NYT robots.txt

### Emergency Tasks
- If scraper breaks: Update parsing strategies
- If rate limited: Increase delays
- If Actions fail: Check permissions

## Resources

- Python requests docs: https://requests.readthedocs.io/
- BeautifulSoup docs: https://www.crummy.com/software/BeautifulSoup/
- GitHub Actions docs: https://docs.github.com/actions
- NYT robots.txt: https://www.nytimes.com/robots.txt
