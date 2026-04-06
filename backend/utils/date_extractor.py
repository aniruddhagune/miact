"""
Shared date extraction utility.
Extracts publication dates from web pages using a cascade:
  1. JSON-LD (schema.org datePublished)
  2. HTML <meta> tags (article:published_time, og:article:published_time, etc.)
  3. URL date patterns (/2025/03/15/ or /2025-03-15/)
  4. In-page visible date (via dateutil parser on common patterns)
"""
import re
import json
from datetime import datetime
from typing import Optional

from bs4 import BeautifulSoup


def _try_parse_date(date_str: str) -> Optional[str]:
    """Attempt to parse a date string into ISO format. Returns None on failure."""
    if not date_str or not isinstance(date_str, str):
        return None
    date_str = date_str.strip()
    if not date_str:
        return None

    # Try common formats
    formats = [
        "%Y-%m-%dT%H:%M:%S%z",       # ISO 8601 with timezone
        "%Y-%m-%dT%H:%M:%SZ",        # ISO 8601 UTC
        "%Y-%m-%dT%H:%M:%S",         # ISO 8601 no tz
        "%Y-%m-%dT%H:%M:%S.%f%z",    # ISO 8601 with microseconds
        "%Y-%m-%d",                   # Plain date
        "%B %d, %Y",                  # March 15, 2025
        "%b %d, %Y",                  # Mar 15, 2025
        "%d %B %Y",                   # 15 March 2025
        "%d %b %Y",                   # 15 Mar 2025
        "%Y/%m/%d",                   # 2025/03/15
        "%m/%d/%Y",                   # 03/15/2025
    ]

    for fmt in formats:
        try:
            dt = datetime.strptime(date_str[:30], fmt)
            return dt.strftime("%Y-%m-%d")
        except (ValueError, IndexError):
            continue

    return None


def extract_date_from_jsonld(soup: BeautifulSoup) -> Optional[str]:
    """Extract datePublished from JSON-LD script tags."""
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string or "")
            # Handle both single objects and arrays
            items = data if isinstance(data, list) else [data]
            for item in items:
                # Check top-level
                if "datePublished" in item:
                    parsed = _try_parse_date(item["datePublished"])
                    if parsed:
                        return parsed
                # Check nested @graph
                if "@graph" in item:
                    for node in item["@graph"]:
                        if "datePublished" in node:
                            parsed = _try_parse_date(node["datePublished"])
                            if parsed:
                                return parsed
        except (json.JSONDecodeError, TypeError, AttributeError):
            continue
    return None


def extract_date_from_meta(soup: BeautifulSoup) -> Optional[str]:
    """Extract publication date from HTML meta tags."""
    # Priority-ordered list of meta tag attributes to check
    meta_selectors = [
        {"property": "article:published_time"},
        {"property": "og:article:published_time"},
        {"name": "date"},
        {"name": "DC.date.issued"},
        {"name": "DC.date"},
        {"name": "publish-date"},
        {"name": "sailthru.date"},
        {"property": "article:published"},
        {"itemprop": "datePublished"},
    ]

    for attrs in meta_selectors:
        tag = soup.find("meta", attrs=attrs)
        if tag and tag.get("content"):
            parsed = _try_parse_date(tag["content"])
            if parsed:
                return parsed

    # Also check <time> elements with datetime attribute
    time_tag = soup.find("time", attrs={"datetime": True})
    if time_tag:
        parsed = _try_parse_date(time_tag["datetime"])
        if parsed:
            return parsed

    return None


def extract_date_from_url(url: str) -> Optional[str]:
    """Extract date from URL path patterns like /2025/03/15/ or /2025-03-15/."""
    # Pattern: /YYYY/MM/DD/ or /YYYY/M/D/
    match = re.search(r"/(\d{4})/(\d{1,2})/(\d{1,2})/", url)
    if match:
        try:
            y, m, d = int(match.group(1)), int(match.group(2)), int(match.group(3))
            if 2000 <= y <= 2100 and 1 <= m <= 12 and 1 <= d <= 31:
                return f"{y:04d}-{m:02d}-{d:02d}"
        except ValueError:
            pass

    # Pattern: /YYYY-MM-DD/ in path
    match = re.search(r"/(\d{4})-(\d{2})-(\d{2})", url)
    if match:
        try:
            y, m, d = int(match.group(1)), int(match.group(2)), int(match.group(3))
            if 2000 <= y <= 2100 and 1 <= m <= 12 and 1 <= d <= 31:
                return f"{y:04d}-{m:02d}-{d:02d}"
        except ValueError:
            pass

    return None


def extract_publication_date(soup: BeautifulSoup = None, url: str = None) -> Optional[str]:
    """
    Master extraction function. Tries all methods in reliability order.
    Returns ISO date string (YYYY-MM-DD) or None.
    
    Args:
        soup: BeautifulSoup parsed HTML (for JSON-LD and meta extraction)
        url: The page URL (for URL pattern extraction)
    """
    # 1. JSON-LD (most reliable)
    if soup:
        date = extract_date_from_jsonld(soup)
        if date:
            return date

    # 2. Meta tags
    if soup:
        date = extract_date_from_meta(soup)
        if date:
            return date

    # 3. URL pattern (costs nothing)
    if url:
        date = extract_date_from_url(url)
        if date:
            return date

    return None
