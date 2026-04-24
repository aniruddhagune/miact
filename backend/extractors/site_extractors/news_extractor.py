import re
from bs4 import BeautifulSoup
from backend.services.http_client import get as http_get
from backend.utils.date_extractor import extract_publication_date
from backend.utils.logger import logger

# Common CSS selectors for news article bodies across various sites
NEWS_BODY_SELECTORS = [
    "article",
    ".story-body",
    ".article-content",
    ".ArticleBody",
    ".content-area",
    ".entry-content",
    ".story-full-width",
    "[itemprop='articleBody']",
    ".article__content",
    ".article-text",
    "#article-body",
    ".main-content"
]

def extract(url: str, html: str = None) -> dict:
    """
    Dedicated news article extractor using heuristic body identification.
    Can accept pre-fetched HTML (e.g. from Playwright).
    """
    try:
        if not html:
            response = http_get(url)
            if not response or response.status_code != 200:
                return {"title": "", "published_at": None, "text": "", "method": "blocked", "source": url}
            html = response.content

        soup = BeautifulSoup(html, "html.parser")

        # 1. Extract Title
        title = ""
        # Try metadata/itemprop first
        title_tag = soup.find(["h1"], itemprop="headline") or soup.find("h1", class_=re.compile("title|headline", re.I))
        if title_tag:
            title = title_tag.get_text(strip=True)
        
        if not title and soup.title:
            title = soup.title.string.strip() if soup.title.string else ""

        # 2. Extract Date
        published_at = extract_publication_date(soup=soup, url=url)

        # 3. Heuristic Body Extraction
        article_body = None
        for selector in NEWS_BODY_SELECTORS:
            if selector.startswith("."):
                article_body = soup.find(class_=selector[1:])
            elif selector.startswith("#"):
                article_body = soup.find(id=selector[1:])
            elif selector.startswith("["):
                # Simplified attr match
                attr, val = selector[1:-1].split("=")
                val = val.strip("'").strip('"')
                article_body = soup.find(attrs={attr: val})
            else:
                article_body = soup.find(selector)
            
            if article_body:
                # Basic validation: does it have enough text?
                if len(article_body.get_text(strip=True)) > 500:
                    break
                else:
                    article_body = None

        # 4. Extract Paragraphs
        if article_body:
            # Only keep paragraphs to avoid scripts, ads, and nav links
            # that might be nested in the container
            paragraphs = article_body.find_all("p")
            text_blocks = []
            for p in paragraphs:
                p_text = p.get_text(" ", strip=True)
                # Filter out very short lines or navigational boilerplate
                if len(p_text) > 40 and not any(x in p_text.lower() for x in ["click here", "follow us", "read more"]):
                    text_blocks.append(p_text)
            
            full_text = "\n\n".join(text_blocks)
        else:
            # Fallback: just grab all p tags in the document if no container found
            paragraphs = soup.find_all("p")
            full_text = "\n\n".join([p.get_text(" ", strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 60])

        if len(full_text) < 200:
            logger.warning("EXTRACTOR", f"Heuristic extraction yielded very little text for {url}")

        return {
            "title": title,
            "published_at": published_at,
            "text": full_text,
            "method": "news_heuristic",
            "source": url
        }

    except Exception as e:
        logger.error("EXTRACTOR", f"News heuristic extractor failed for {url}: {e}")
        return {
            "title": "",
            "published_at": None,
            "text": "",
            "method": "error",
            "source": url,
            "error": str(e)
        }
