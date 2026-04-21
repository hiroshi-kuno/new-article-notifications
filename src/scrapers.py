"""Scrapers for different news sources."""
import time
from typing import Optional, Dict
import requests
from bs4 import BeautifulSoup
import feedparser

from .models import Article


# User agent that clearly identifies this as a monitoring bot
USER_AGENT = "NYT-Article-Monitor/1.0 (GitHub Actions; article-change-detection; +https://github.com)"

# Request timeout in seconds
REQUEST_TIMEOUT = 15

# Sleep between requests (seconds) to be respectful
REQUEST_DELAY = 2.0


class ScraperError(Exception):
    """Base exception for scraper errors."""
    pass


class NYTReporterScraper:
    """Scraper for New York Times reporter pages."""

    def __init__(self):
        """Initialize the scraper."""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': USER_AGENT,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })

    def fetch_page(
        self,
        url: str,
        etag: Optional[str] = None,
        last_modified: Optional[str] = None
    ) -> tuple[Optional[str], Optional[str], Optional[str]]:
        """Fetch a page with conditional request headers.

        Args:
            url: URL to fetch
            etag: ETag from previous request (if any)
            last_modified: Last-Modified from previous request (if any)

        Returns:
            Tuple of (html_content, new_etag, new_last_modified)
            Returns (None, None, None) if page not modified (304)

        Raises:
            ScraperError: If request fails
        """
        headers = {}
        if etag:
            headers['If-None-Match'] = etag
        if last_modified:
            headers['If-Modified-Since'] = last_modified

        try:
            response = self.session.get(
                url,
                headers=headers,
                timeout=REQUEST_TIMEOUT,
                allow_redirects=True
            )

            # Handle 304 Not Modified
            if response.status_code == 304:
                print(f"  Page not modified (304), skipping parse")
                return None, etag, last_modified

            # Handle other errors
            if response.status_code != 200:
                raise ScraperError(f"HTTP {response.status_code}")

            # Extract caching headers for next request
            new_etag = response.headers.get('ETag')
            new_last_modified = response.headers.get('Last-Modified')

            response.encoding = response.apparent_encoding
            return response.text, new_etag, new_last_modified

        except requests.Timeout:
            raise ScraperError(f"Request timeout after {REQUEST_TIMEOUT}s")
        except requests.RequestException as e:
            raise ScraperError(f"Request failed: {str(e)}")

    def parse_top_article(self, html: str) -> Optional[Article]:
        """Parse the top article from a NYT reporter page.

        Args:
            html: HTML content of the page

        Returns:
            Article object or None if no article found
        """
        soup = BeautifulSoup(html, 'html.parser')

        # Try multiple strategies to find the top article
        article_data = (
            self._parse_strategy_1(soup) or
            self._parse_strategy_2(soup) or
            self._parse_strategy_3(soup)
        )

        if not article_data:
            return None

        return Article(**article_data)

    def _parse_strategy_1(self, soup: BeautifulSoup) -> Optional[Dict]:
        """Primary parsing strategy: Look for article list items."""
        # NYT often uses <ol> with <li> containing articles
        # Each article typically has a link with specific CSS classes

        # Try finding article list
        article_lists = soup.find_all('ol')
        for ol in article_lists:
            # Find first article link
            link = ol.find('a', href=lambda x: x and '/20' in x and x.startswith('/'))
            if link and link.get('href'):
                title_elem = link.find('h3') or link.find('h2') or link.find('h4')
                if title_elem:
                    title = title_elem.get_text(strip=True)
                    url = link['href']

                    # Make URL absolute if needed
                    if url.startswith('/'):
                        url = 'https://www.nytimes.com' + url

                    # Try to find publication time
                    time_elem = None
                    parent = link.find_parent('li')
                    if parent:
                        time_elem = parent.find('time')

                    pub_time = time_elem.get('datetime') if time_elem else None

                    return {
                        'title': title,
                        'url': url,
                        'published_time': pub_time
                    }

        return None

    def _parse_strategy_2(self, soup: BeautifulSoup) -> Optional[Dict]:
        """Secondary strategy: Look for article containers with specific patterns."""
        # Try finding divs or sections that might contain articles
        containers = soup.find_all(['div', 'section', 'article'])

        for container in containers:
            # Look for a link that looks like an article
            links = container.find_all('a', href=lambda x: x and '/20' in x)
            for link in links:
                if not link.get('href'):
                    continue

                # Look for title in various heading tags
                title_elem = link.find(['h1', 'h2', 'h3', 'h4', 'h5'])
                if title_elem:
                    title = title_elem.get_text(strip=True)
                    if len(title) > 10:  # Reasonable title length
                        url = link['href']
                        if url.startswith('/'):
                            url = 'https://www.nytimes.com' + url

                        # Try to find time
                        time_elem = container.find('time')
                        pub_time = time_elem.get('datetime') if time_elem else None

                        return {
                            'title': title,
                            'url': url,
                            'published_time': pub_time
                        }

        return None

    def _parse_strategy_3(self, soup: BeautifulSoup) -> Optional[Dict]:
        """Fallback strategy: Find any article-like link."""
        # Find all links that look like articles
        links = soup.find_all('a', href=lambda x: x and '/20' in x and '/' in x)

        for link in links:
            href = link.get('href', '')
            # Article URLs typically contain year patterns like /2024/ or /2025/
            if not any(year in href for year in ['/2024/', '/2025/', '/2026/']):
                continue

            # Get text from link or nearby elements
            title = link.get_text(strip=True)
            if not title or len(title) < 10:
                # Try to find title in parent
                parent = link.find_parent(['div', 'li', 'article'])
                if parent:
                    heading = parent.find(['h1', 'h2', 'h3', 'h4', 'h5'])
                    if heading:
                        title = heading.get_text(strip=True)

            if title and len(title) > 10:
                url = href
                if url.startswith('/'):
                    url = 'https://www.nytimes.com' + url

                return {
                    'title': title,
                    'url': url,
                    'published_time': None
                }

        return None

    def scrape(
        self,
        url: str,
        etag: Optional[str] = None,
        last_modified: Optional[str] = None
    ) -> tuple[Optional[Article], Optional[str], Optional[str]]:
        """Scrape the top article from a reporter page.

        Args:
            url: URL of the reporter page
            etag: ETag from previous request
            last_modified: Last-Modified from previous request

        Returns:
            Tuple of (Article or None, new_etag, new_last_modified)

        Raises:
            ScraperError: If scraping fails
        """
        # Fetch the page
        html, new_etag, new_last_modified = self.fetch_page(url, etag, last_modified)

        # If page not modified, return None
        if html is None:
            return None, new_etag, new_last_modified

        # Parse the top article
        article = self.parse_top_article(html)

        # Sleep to be respectful
        time.sleep(REQUEST_DELAY)

        return article, new_etag, new_last_modified


class RSSScraper:
    """Scraper for RSS feeds."""

    def __init__(self):
        """Initialize the scraper."""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': USER_AGENT,
            'Accept': 'application/rss+xml, application/xml, text/xml, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive'
        })

    def fetch_feed(
        self,
        url: str,
        etag: Optional[str] = None,
        last_modified: Optional[str] = None
    ) -> tuple[Optional[str], Optional[str], Optional[str]]:
        """Fetch an RSS feed with conditional request headers.

        Args:
            url: URL to fetch
            etag: ETag from previous request (if any)
            last_modified: Last-Modified from previous request (if any)

        Returns:
            Tuple of (xml_content, new_etag, new_last_modified)
            Returns (None, None, None) if feed not modified (304)

        Raises:
            ScraperError: If request fails
        """
        headers = {}
        if etag:
            headers['If-None-Match'] = etag
        if last_modified:
            headers['If-Modified-Since'] = last_modified

        try:
            response = self.session.get(
                url,
                headers=headers,
                timeout=REQUEST_TIMEOUT,
                allow_redirects=True
            )

            # Handle 304 Not Modified
            if response.status_code == 304:
                print(f"  Feed not modified (304), skipping parse")
                return None, etag, last_modified

            # Handle other errors
            if response.status_code != 200:
                raise ScraperError(f"HTTP {response.status_code}")

            # Extract caching headers for next request
            new_etag = response.headers.get('ETag')
            new_last_modified = response.headers.get('Last-Modified')

            response.encoding = response.apparent_encoding
            return response.text, new_etag, new_last_modified

        except requests.Timeout:
            raise ScraperError(f"Request timeout after {REQUEST_TIMEOUT}s")
        except requests.RequestException as e:
            raise ScraperError(f"Request failed: {str(e)}")

    def parse_top_article(self, xml: str) -> Optional[Article]:
        """Parse the top article from an RSS feed.

        Args:
            xml: XML content of the RSS feed

        Returns:
            Article object or None if no article found
        """
        # Parse the RSS feed
        feed = feedparser.parse(xml)

        # Check for parsing errors
        if feed.bozo:
            # bozo=1 means there were issues, but feedparser is lenient
            # We'll try to continue anyway
            pass

        # Get entries (articles)
        if not feed.entries:
            return None

        # Get the first (most recent) entry
        entry = feed.entries[0]

        # Extract title
        title = entry.get('title', '').strip()
        if not title:
            return None

        # Extract URL (try multiple fields)
        url = entry.get('link', '').strip()
        if not url:
            return None

        # Skip if URL is exactly the Washington Post homepage
        if url == 'https://www.washingtonpost.com':
            return None

        # Extract publication time
        # RSS feeds can have 'published' or 'updated' or 'pubDate'
        pub_time = None
        if hasattr(entry, 'published_parsed') and entry.published_parsed:
            # Convert time tuple to ISO format
            import time as time_module
            pub_time = time_module.strftime('%Y-%m-%dT%H:%M:%SZ', entry.published_parsed)
        elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
            import time as time_module
            pub_time = time_module.strftime('%Y-%m-%dT%H:%M:%SZ', entry.updated_parsed)
        elif hasattr(entry, 'published'):
            pub_time = entry.published
        elif hasattr(entry, 'updated'):
            pub_time = entry.updated

        return Article(
            title=title,
            url=url,
            published_time=pub_time
        )

    def scrape(
        self,
        url: str,
        etag: Optional[str] = None,
        last_modified: Optional[str] = None
    ) -> tuple[Optional[Article], Optional[str], Optional[str]]:
        """Scrape the top article from an RSS feed.

        Args:
            url: URL of the RSS feed
            etag: ETag from previous request
            last_modified: Last-Modified from previous request

        Returns:
            Tuple of (Article or None, new_etag, new_last_modified)

        Raises:
            ScraperError: If scraping fails
        """
        # Fetch the feed
        xml, new_etag, new_last_modified = self.fetch_feed(url, etag, last_modified)

        # If feed not modified, return None
        if xml is None:
            return None, new_etag, new_last_modified

        # Parse the top article
        article = self.parse_top_article(xml)

        # Sleep to be respectful
        time.sleep(REQUEST_DELAY)

        return article, new_etag, new_last_modified


class GenericHTMLScraper:
    """Generic scraper for HTML pages (GIJN, Datawrapper, etc)."""

    def __init__(self):
        """Initialize the scraper."""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': USER_AGENT,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })

    def fetch_page(
        self,
        url: str,
        etag: Optional[str] = None,
        last_modified: Optional[str] = None
    ) -> tuple[Optional[str], Optional[str], Optional[str]]:
        """Fetch a page with conditional request headers.

        Args:
            url: URL to fetch
            etag: ETag from previous request (if any)
            last_modified: Last-Modified from previous request (if any)

        Returns:
            Tuple of (html_content, new_etag, new_last_modified)
            Returns (None, None, None) if page not modified (304)

        Raises:
            ScraperError: If request fails
        """
        headers = {}
        if etag:
            headers['If-None-Match'] = etag
        if last_modified:
            headers['If-Modified-Since'] = last_modified

        try:
            response = self.session.get(
                url,
                headers=headers,
                timeout=REQUEST_TIMEOUT,
                allow_redirects=True
            )

            # Handle 304 Not Modified
            if response.status_code == 304:
                print(f"  Page not modified (304), skipping parse")
                return None, etag, last_modified

            # Handle other errors
            if response.status_code != 200:
                raise ScraperError(f"HTTP {response.status_code}")

            # Extract caching headers for next request
            new_etag = response.headers.get('ETag')
            new_last_modified = response.headers.get('Last-Modified')

            response.encoding = response.apparent_encoding
            return response.text, new_etag, new_last_modified

        except requests.Timeout:
            raise ScraperError(f"Request timeout after {REQUEST_TIMEOUT}s")
        except requests.RequestException as e:
            raise ScraperError(f"Request failed: {str(e)}")

    def parse_top_article(self, html: str, base_url: str) -> Optional[Article]:
        """Parse the top article from an HTML page.

        Args:
            html: HTML content of the page
            base_url: Base URL for resolving relative URLs

        Returns:
            Article object or None if no article found
        """
        soup = BeautifulSoup(html, 'html.parser')
        from urllib.parse import urljoin

        # Strategy 1: Look for article lists (most reliable)
        article_lists = soup.find_all(['ol', 'ul', 'div'], class_=lambda x: x and ('post' in x.lower() or 'article' in x.lower() or 'entry' in x.lower()))
        for list_elem in article_lists:
            link = list_elem.find('a', href=lambda x: x and len(x) > 5)
            if link and link.get('href'):
                href = link['href']
                # Skip non-article links
                if any(skip in href.lower() for skip in ['#', 'mailto:', 'javascript:', 'facebook.com', 'twitter.com', 'linkedin.com']):
                    continue

                # Look for title
                title_elem = link.find(['h1', 'h2', 'h3', 'h4', 'h5'])
                if not title_elem:
                    # Try getting text from link itself
                    title = link.get_text(strip=True)
                else:
                    title = title_elem.get_text(strip=True)

                if title and len(title) > 10:
                    url = urljoin(base_url, href)

                    # Try to find publication time
                    time_elem = list_elem.find('time')
                    pub_time = time_elem.get('datetime') if time_elem else None

                    return Article(
                        title=title,
                        url=url,
                        published_time=pub_time
                    )

        # Strategy 2: Look for <article> tags
        articles = soup.find_all('article')
        for article_elem in articles:
            link = article_elem.find('a', href=lambda x: x and len(x) > 5)
            if link and link.get('href'):
                href = link['href']
                if any(skip in href.lower() for skip in ['#', 'mailto:', 'javascript:']):
                    continue

                title_elem = article_elem.find(['h1', 'h2', 'h3', 'h4', 'h5'])
                if title_elem:
                    title = title_elem.get_text(strip=True)
                    if len(title) > 10:
                        url = urljoin(base_url, href)
                        time_elem = article_elem.find('time')
                        pub_time = time_elem.get('datetime') if time_elem else None

                        return Article(
                            title=title,
                            url=url,
                            published_time=pub_time
                        )

        # Strategy 3: Find first meaningful heading with a link
        headings = soup.find_all(['h1', 'h2', 'h3'], limit=10)
        for heading in headings:
            link = heading.find('a', href=lambda x: x and len(x) > 5)
            if link and link.get('href'):
                href = link['href']
                if any(skip in href.lower() for skip in ['#', 'mailto:', 'javascript:']):
                    continue

                title = heading.get_text(strip=True)
                if len(title) > 10:
                    url = urljoin(base_url, href)
                    return Article(
                        title=title,
                        url=url,
                        published_time=None
                    )

        # Strategy 4: <a> wrapping a heading (pudding.cool, straitstimes.com style)
        skip_patterns = ['#', 'mailto:', 'javascript:', 'facebook.com', 'twitter.com', 'linkedin.com']
        for a in soup.find_all('a', href=True):
            href = a.get('href', '')
            if any(skip in href.lower() for skip in skip_patterns):
                continue
            heading = a.find(['h1', 'h2', 'h3', 'h4'])
            if heading:
                title = heading.get_text(strip=True)
                if len(title) > 10:
                    url = urljoin(base_url, href)
                    time_elem = a.find('time') or a.parent.find('time') if a.parent else None
                    pub_time = time_elem.get('datetime') if time_elem else None
                    return Article(title=title, url=url, published_time=pub_time)

        return None

    def scrape(
        self,
        url: str,
        etag: Optional[str] = None,
        last_modified: Optional[str] = None
    ) -> tuple[Optional[Article], Optional[str], Optional[str]]:
        """Scrape the top article from a page.

        Args:
            url: URL of the page
            etag: ETag from previous request
            last_modified: Last-Modified from previous request

        Returns:
            Tuple of (Article or None, new_etag, new_last_modified)

        Raises:
            ScraperError: If scraping fails
        """
        # Fetch the page
        html, new_etag, new_last_modified = self.fetch_page(url, etag, last_modified)

        # If page not modified, return None
        if html is None:
            return None, new_etag, new_last_modified

        # Parse the top article
        article = self.parse_top_article(html, url)

        # Sleep to be respectful
        time.sleep(REQUEST_DELAY)

        return article, new_etag, new_last_modified


class ReutersScraper(GenericHTMLScraper):
    """Scraper for Reuters section pages (e.g. /graphics/)."""

    def parse_top_article(self, html: str, base_url: str) -> Optional[Article]:
        """Parse the top article from a Reuters section page.

        Reuters article URLs end with a date pattern: /slug-YYYY-MM-DD/
        """
        import re
        from urllib.parse import urljoin

        soup = BeautifulSoup(html, 'html.parser')

        # Strategy 1: links ending with date pattern (Reuters article URL format)
        date_pattern = re.compile(r'\d{4}-\d{2}-\d{2}/?$')
        for a in soup.find_all('a', href=True):
            href = a['href']
            if not date_pattern.search(href):
                continue
            title = a.get_text(strip=True)
            if len(title) > 10:
                url = urljoin('https://www.reuters.com', href)
                return Article(title=title, url=url, published_time=None)

        # Strategy 2: fallback to generic
        return super().parse_top_article(html, base_url)


class FTScraper(GenericHTMLScraper):
    """Scraper for Financial Times section pages."""

    def parse_top_article(self, html: str, base_url: str) -> Optional[Article]:
        """Parse the top article from an FT section page.

        FT uses o-teaser__heading > js-teaser-heading-link for the featured article.
        """
        soup = BeautifulSoup(html, 'html.parser')
        from urllib.parse import urljoin

        # Strategy 1: o-teaser__heading (FT's featured article structure)
        heading_div = soup.find('div', class_='o-teaser__heading')
        if heading_div:
            link = heading_div.find('a', href=lambda x: x and '/content/' in str(x))
            if link:
                href = link.get('href', '')
                title = link.get_text(strip=True)
                if title and len(title) > 5:
                    url = urljoin('https://www.ft.com', href)
                    # Look for timestamp in parent teaser
                    teaser = heading_div.find_parent(class_=lambda x: x and 'o-teaser' in ' '.join(x))
                    time_elem = teaser.find('time') if teaser else None
                    pub_time = time_elem.get('datetime') if time_elem else None
                    return Article(title=title, url=url, published_time=pub_time)

        # Strategy 2: fallback to generic
        return super().parse_top_article(html, base_url)


class LATimesPeopleScraper(RSSScraper):
    """Scraper for LA Times author pages using their RSS feed."""

    def scrape(
        self,
        url: str,
        etag: Optional[str] = None,
        last_modified: Optional[str] = None
    ) -> tuple[Optional[Article], Optional[str], Optional[str]]:
        return super().scrape(url + '.rss', etag, last_modified)


# Domains handled by the generic HTML scraper
_GENERIC_HTML_DOMAINS = ('gijn.org', 'datawrapper.de', 'anychart.com', 'aljazeera.com', 'pudding.cool', 'straitstimes.com', 'asahi.com')


def get_scraper(url: str):
    """Factory function to get appropriate scraper for URL.

    Args:
        url: Source URL

    Returns:
        Scraper instance

    Raises:
        ValueError: If URL is not supported
    """
    if '/rss/' in url.lower() or url.endswith(('.rss', '.xml')):
        return RSSScraper()
    if 'nytimes.com/by/' in url:
        return NYTReporterScraper()
    if 'ft.com/' in url:
        return FTScraper()
    if 'latimes.com/people/' in url:
        return LATimesPeopleScraper()
    if 'reuters.com/' in url:
        return ReutersScraper()
    if any(domain in url for domain in _GENERIC_HTML_DOMAINS):
        return GenericHTMLScraper()
    raise ValueError(f"No scraper available for URL: {url}")
