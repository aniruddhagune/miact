"""
Shared HTTP client with User-Agent rotation and realistic browser headers.
All extractors should import get_session() or get_headers() from here.
"""
import random
import requests

# ---- BLOCKED DOMAINS ----
# Sites that consistently block scrapers even with UA rotation.
# These will be skipped gracefully rather than hanging on a timeout.
BLOCKED_DOMAINS = [
    # Add domains here as they are confirmed to block
]

# ---- USER AGENT POOL ----
_USER_AGENTS = [
    # Chrome 120 Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    # Chrome 119 Mac
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    # Firefox 120 Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
    # Firefox 119 Mac
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14.1; rv:119.0) Gecko/20100101 Firefox/119.0",
    # Edge 120
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
    # Safari 17 Mac
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    # Chrome 118 Linux
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
]


def is_blocked(url: str) -> bool:
    """Return True if this URL's domain is in the blocked list."""
    return any(blocked in url.lower() for blocked in BLOCKED_DOMAINS)


def get_headers(referer: str = "https://www.google.com/") -> dict:
    """Return a randomized but realistic set of browser request headers."""
    ua = random.choice(_USER_AGENTS)
    is_chrome = "Chrome" in ua and "Edg" not in ua
    is_firefox = "Firefox" in ua
    is_safari = "Safari" in ua and "Chrome" not in ua

    if is_firefox:
        sec_ch_ua = ""  # Firefox doesn't send this
        accept = "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"
    elif is_safari:
        sec_ch_ua = ""
        accept = "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
    else:
        # Chrome / Edge
        sec_ch_ua = '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"'
        accept = "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8"

    headers = {
        "User-Agent": ua,
        "Accept": accept,
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Referer": referer,
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "cross-site",
        "Sec-Fetch-User": "?1",
        "Cache-Control": "max-age=0",
    }

    if sec_ch_ua:
        headers["Sec-Ch-Ua"] = sec_ch_ua
        headers["Sec-Ch-Ua-Mobile"] = "?0"
        headers["Sec-Ch-Ua-Platform"] = '"Windows"'

    return headers


def get(url: str, timeout: int = 12, referer: str = "https://www.google.com/") -> requests.Response | None:
    """
    Perform a GET request with rotating UA + realistic headers.
    Returns None if the domain is blocked or the request fails.
    """
    if is_blocked(url):
        print(f"[HTTP] Skipping blocked domain: {url}")
        return None

    try:
        return requests.get(url, headers=get_headers(referer), timeout=timeout)
    except Exception as e:
        print(f"[HTTP] Request failed for {url}: {e}")
        return None
