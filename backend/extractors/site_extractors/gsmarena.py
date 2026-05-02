import re
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
from backend.services.http_client import get as http_get
from backend.utils.date_extractor import extract_publication_date

# ---- URL Pattern constants ----
# Specs:         oneplus_9-10747.php
# Review:        oneplus_9-review-2240.php  or  oneplus_9-review-2240p2.php
# User opinions: oneplus_9-reviews-10747.php  or  oneplus_9-reviews-10747p2.php
# Review comments: reviewcomm-2240.php  or  reviewcomm-2240p2.php

_RE_SPECS       = re.compile(r"gsmarena\.com/[^/]+-\d+\.php(?:\?.*)?$")
_RE_REVIEW      = re.compile(r"gsmarena\.com/[^/]+-review-(\d+)(p\d+)?\.php")
_RE_USER_OPS    = re.compile(r"gsmarena\.com/[^/]+-reviews-(\d+)(p\d+)?\.php")
_RE_REVIEWCOMM  = re.compile(r"gsmarena\.com/reviewcomm-(\d+)(p\d+)?\.php")

MAX_PAGES = 4  # Max additional pages to fetch beyond the first


def classify_gsmarena_url(url: str) -> str:
    """Returns 'review', 'user_opinions', 'review_comments', or 'specs'."""
    if _RE_REVIEWCOMM.search(url):
        return "review_comments"
    if _RE_USER_OPS.search(url):
        return "user_opinions"
    if _RE_REVIEW.search(url):
        return "review"
    return "specs"


def _base_url(url: str) -> str:
    """Strip query string and #fragment."""
    p = urlparse(url)
    return f"{p.scheme}://{p.netloc}{p.path}"


def _paginate_url(base_url: str, page: int) -> str:
    """
    Build a paginated GSMArena URL.
    Base:  oneplus_9-review-2240.php
    Page2: oneplus_9-review-2240p2.php
    """
    if ".php" not in base_url:
        return base_url
    return re.sub(r"(p\d+)?\.php$", f"p{page}.php", base_url)


def _fetch_soup(url: str):
    response = http_get(url, referer="https://www.google.com/search?q=gsmarena")
    if not response:
        return None
    return BeautifulSoup(response.content, "html.parser")


def _extract_specs(soup: BeautifulSoup) -> list:
    """Parse the specs table on a product page."""
    extracted = []
    for table in soup.find_all("table"):
        th = table.find("th")
        section_name = th.get_text(strip=True).lower() if th else ""

        for row in table.find_all("tr"):
            ttl = row.find("td", class_="ttl")
            nfo = row.find("td", class_="nfo")
            if not (ttl and nfo):
                continue

            aspect = ttl.get_text(strip=True).lower()
            if (aspect == "type" and section_name) or section_name == "our tests":
                aspect = f"{section_name} {aspect}"

            for br in nfo.find_all("br"):
                br.replace_with(" + ")

            value = nfo.get_text(" ", strip=True)
            value = re.sub(r"\s*\(#\d+\)\s*", " ", value)
            value = value.replace("\xa0", " ").replace("·", " ").replace("╖", " ").replace("–", "-").lower()
            value = re.sub(r"\s+", " ", value).strip()

            if aspect and value:
                extracted.append({
                    "aspect": aspect.strip(),
                    "value": value,
                    "type": "table"
                })
    return extracted


def _extract_user_comments(soup: BeautifulSoup, source_label: str) -> list:
    """Extract user-thread comments (used for both user opinions and review comments pages)."""
    opinions = []
    for thread in soup.find_all("div", class_="user-thread"):
        p = thread.find("p", class_="uopin")
        if p:
            text = p.get_text(" ", strip=True)
            if text:
                opinions.append({
                    "text": text,
                    "source": source_label,
                    "type": "subjective"
                })
    return opinions


def _extract_review_text(soup: BeautifulSoup) -> str:
    """Extract paragraph text from the review body on a review page."""
    body = soup.find("div", id="review-body")
    if not body:
        return ""
    paragraphs = []
    for el in body.find_all(["p", "h3"]):
        # Skip inline iframes (YouTube), pricing tables, image rows
        if el.find("iframe") or el.find("table"):
            continue
        if "image-row" in el.get("class", []):
            continue
        text = el.get_text(" ", strip=True)
        if text and len(text) > 20:
            paragraphs.append(text)
    return "\n\n".join(paragraphs)


def _get_next_page_url(soup: BeautifulSoup, current_url: str) -> str | None:
    """
    Detect next page via <link rel='next'> or the 'pages-next' link in the nav.
    Returns an absolute URL or None.
    """
    # Prefer the canonical <link rel="next"> in <head>
    link_next = soup.find("link", rel="next")
    if link_next and link_next.get("href"):
        href = link_next["href"]
        return href if href.startswith("http") else urljoin(current_url, href)

    # Fallback: nav arrow
    next_a = soup.find("a", class_="pages-next")
    if next_a and next_a.get("href") and next_a["href"] not in ("#", ""):
        return urljoin(current_url, next_a["href"])

    return None


def _scrape_paginated_comments(first_soup: BeautifulSoup, base_url: str, source_label: str) -> list:
    """Collect comments from first page + follow pagination up to MAX_PAGES."""
    all_opinions = _extract_user_comments(first_soup, source_label)
    current_soup = first_soup
    current_url = base_url

    for _ in range(MAX_PAGES - 1):
        next_url = _get_next_page_url(current_soup, current_url)
        if not next_url:
            break
        current_soup = _fetch_soup(next_url)
        if not current_soup:
            break
        current_url = next_url
        page_ops = _extract_user_comments(current_soup, source_label)
        if not page_ops:
            break
        all_opinions.extend(page_ops)

    return all_opinions


def _scrape_paginated_review(first_soup: BeautifulSoup, base_url: str) -> str:
    """Collect review text from first page + follow pagination up to MAX_PAGES."""
    all_text = [_extract_review_text(first_soup)]
    current_soup = first_soup
    current_url = base_url

    for _ in range(MAX_PAGES - 1):
        next_url = _get_next_page_url(current_soup, current_url)
        if not next_url:
            break
        current_soup = _fetch_soup(next_url)
        if not current_soup:
            break
        current_url = next_url
        page_text = _extract_review_text(current_soup)
        if not page_text:
            break
        all_text.append(page_text)

    return "\n\n".join(t for t in all_text if t)


def extract(url: str):
    try:
        page_type = classify_gsmarena_url(url)
        base = _base_url(url)

        first_soup = _fetch_soup(url)
        if not first_soup:
            return None

        title = first_soup.title.string if first_soup.title else "GSMArena"
        pub_date = extract_publication_date(soup=first_soup, url=url)

        if page_type == "specs":
            tables = _extract_specs(first_soup)
            # Also grab the few inline user comments shown on spec pages
            inline_opinions = _extract_user_comments(first_soup, "gsma_spec_comment")
            return {
                "title": title,
                "published_at": pub_date,
                "text": "",
                "tables": tables,
                "opinions": inline_opinions,
                "method": "gsmarena_specs",
                "source": url
            }

        elif page_type == "review":
            review_text = _scrape_paginated_review(first_soup, base)
            # The first review page also shows a few reader comments at the bottom
            inline_opinions = _extract_user_comments(first_soup, "gsma_review_comment")
            return {
                "title": title,
                "published_at": pub_date,
                "text": review_text,
                "tables": [],
                "opinions": inline_opinions,
                "method": "gsmarena_review",
                "source": url
            }

        elif page_type == "user_opinions":
            opinions = _scrape_paginated_comments(first_soup, base, "gsma_user_opinion")
            return {
                "title": title,
                "published_at": pub_date,
                "text": "",
                "tables": [],
                "opinions": opinions,
                "method": "gsmarena_user_opinions",
                "source": url
            }

        elif page_type == "review_comments":
            opinions = _scrape_paginated_comments(first_soup, base, "gsma_review_comment")
            return {
                "title": title,
                "published_at": pub_date,
                "text": "",
                "tables": [],
                "opinions": opinions,
                "method": "gsmarena_review_comments",
                "source": url
            }

    except Exception as e:
        print(f"[GSMARENA EXTRACT ERROR] {e}")
        return None
