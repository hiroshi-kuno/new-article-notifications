# Changelog

## [1.1.0] - 2025-01-28

### Added
- **RSS Feed Support**: Monitor RSS/Atom feeds in addition to NYT reporter pages
  - Washington Post RSS feeds
  - Guardian RSS feeds
  - Any standard RSS 2.0 or Atom feed
- New `RSSScraper` class for parsing RSS feeds
- Automatic scraper detection based on URL pattern
- New documentation: `RSS_SUPPORT.md`

### Changed
- Updated `requirements.txt` to include `feedparser>=6.0.0`
- Enhanced `get_scraper()` to auto-detect RSS feeds
- Updated all documentation to reflect RSS support

### Configuration Examples

**NYT Reporter Page:**
```json
{"url": "https://www.nytimes.com/by/reporter-name", "enabled": true}
```

**RSS Feed:**
```json
{"url": "https://www.washingtonpost.com/arcio/rss/author/Author-Name/", "enabled": true}
```

## [1.0.0] - 2025-01-28

### Initial Release

#### Features
- Monitor NYT reporter pages for new articles
- Automated checks via GitHub Actions (hourly)
- State persistence using Git commits
- Conditional HTTP requests (ETag, If-Modified-Since)
- Multiple HTML parsing strategies for robustness
- Per-source error isolation
- Respectful server load management

#### Configuration
- Simple `sources.json` format with only `url` and `enabled` fields
- Source ID automatically extracted from URL
- Easy to add/remove reporter pages

#### Documentation
- Comprehensive README
- Quick start guide
- Testing guide
- Architecture documentation
- Repository structure documentation

### Configuration Format

**Simplified format (v1.0.0):**
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

- Source ID is automatically extracted from URL path
- Only NYT reporter pages are supported in this version
- Scraper type is determined automatically from URL pattern
