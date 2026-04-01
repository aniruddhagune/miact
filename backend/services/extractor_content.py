from newspaper import Article

from backend.services.extractors.wikipedia import extract as wiki_extract
from backend.services.extractors.generic import extract as generic_extract


def extract_content(url: str):

    # ---- DOMAIN DISPATCH ----
    if "wikipedia.org" in url:
        result = wiki_extract(url)
        if result:
            return result

    # ---- PRIMARY: newspaper ----
    try:
        article = Article(url)
        article.download()
        article.parse()

        text = article.text.strip()

        if text and len(text) > 500:
            return {
                "title": article.title or "",
                "published_at": str(article.publish_date) if article.publish_date else None,
                "text": text,
                "method": "newspaper",
                "source": url
            }

    except Exception:
        pass

    # ---- FALLBACK ----
    return generic_extract(url)