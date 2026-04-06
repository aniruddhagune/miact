from newspaper import Article

from backend.extractors.site_extractors.wikipedia import extract as wiki_extract
from backend.extractors.site_extractors.generic import extract as generic_extract
from backend.extractors.fallback_scraper import extract_dense_text


def extract_content(url: str):

    # ---- DOMAIN DISPATCH ----
    if "wikipedia.org" in url:
        result = wiki_extract(url)
        if result:
            return result

    if "gsmarena.com" in url and "-review-" not in url and "/news/" not in url:
        from backend.extractors.site_extractors.gsmarena import extract as gsm_extract
        result = gsm_extract(url)
        if result:
            return result

    if "devicespecifications.com" in url and "/article" not in url:
        from backend.extractors.site_extractors.devicespecifications import extract as ds_extract
        result = ds_extract(url)
        if result:
            return result

    if "notebookcheck." in url:
        from backend.extractors.site_extractors.notebookcheck import extract as notebookcheck_extract
        result = notebookcheck_extract(url)
        if result:
            return result

    if "amazon." in url:
        from backend.extractors.site_extractors.amazon import extract as amazon_extract
        result = amazon_extract(url)
        if result:
            return result

    # ---- PRIMARY: newspaper ----
    from backend.services.http_client import get as http_get
    try:
        response = http_get(url)
        if response and response.status_code == 200:
            article = Article(url)
            # Inject Cloudflare-bypassed HTML into newspaper directly
            article.set_html(response.text)
            article.parse()
        else:
            raise Exception("HTTP fetch failed")

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

    # ---- SECONDARY: Dense Fallback (p/span) ----
    try:
        dense_result = extract_dense_text(url)
        if dense_result.get("text") and len(dense_result["text"]) > 500:
            return dense_result
    except Exception:
        pass

    # ---- FALLBACK: Generic BeautifulSoup ----
    return generic_extract(url)
