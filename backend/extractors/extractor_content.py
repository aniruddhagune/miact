from newspaper import Article
from backend.utils.logger import logger
from backend.extractors.site_extractors.wikipedia import extract as wiki_extract
from backend.extractors.site_extractors.generic import extract as generic_extract
from backend.extractors.fallback_scraper import extract_dense_text
from backend.services.playwright_service import scrape_dynamic
import asyncio
import traceback


async def extract_content(url: str):
    logger.debug("EXTRACTOR", f"Attempting content extraction from: {url}")

    # ---- DOMAIN DISPATCH (Static/Optimized) ----
    if "wikipedia.org" in url:
        logger.debug("EXTRACTOR", "Dispatching to Wikipedia extractor")
        # Wikipedia is usually static and fast
        result = await asyncio.to_thread(wiki_extract, url)
        if result: return result

    if "gsmarena.com" in url and "-review-" not in url and "/news/" not in url:
        logger.debug("EXTRACTOR", "Dispatching to GSMArena Specs extractor")
        from backend.extractors.site_extractors.gsmarena import extract as gsm_extract
        result = await asyncio.to_thread(gsm_extract, url)
        if result: return result

    if "devicespecifications.com" in url and "/article" not in url:
        logger.debug("EXTRACTOR", "Dispatching to DeviceSpecifications extractor")
        from backend.extractors.site_extractors.devicespecifications import extract as ds_extract
        result = await asyncio.to_thread(ds_extract, url)
        if result: return result

    if "notebookcheck." in url:
        logger.debug("EXTRACTOR", "Dispatching to NotebookCheck extractor")
        from backend.extractors.site_extractors.notebookcheck import extract as notebookcheck_extract
        result = await asyncio.to_thread(notebookcheck_extract, url)
        if result: return result

    if "amazon." in url:
        logger.debug("EXTRACTOR", "Dispatching to Amazon extractor")
        from backend.extractors.site_extractors.amazon import extract as amazon_extract
        result = await asyncio.to_thread(amazon_extract, url)
        if result: return result

    # ---- PRIMARY: Newspaper3k ----
    from backend.services.http_client import get as http_get
    try:
        logger.debug("EXTRACTOR", "Attempting 'newspaper' extraction")
        response = await asyncio.to_thread(http_get, url)
        if response and response.status_code == 200:
            article = Article(url)
            article.set_html(response.text)
            article.parse()
            text = article.text.strip()
            if text and len(text) > 500:
                logger.info("EXTRACTOR", f"Successfully extracted {len(text)} chars via newspaper")
                return {
                    "title": article.title or "",
                    "published_at": str(article.publish_date) if article.publish_date else None,
                    "text": text,
                    "method": "newspaper",
                    "source": url
                }
    except Exception as e:
        logger.warning("EXTRACTOR", f"Newspaper extraction failed for {url}: {e}")

    # ---- SECONDARY: Trafilatura & Dense Fallback ----
    try:
        logger.debug("EXTRACTOR", "Attempting Trafilatura / Dense fallback")
        dense_result = await asyncio.to_thread(extract_dense_text, url)
        if dense_result.get("text") and len(dense_result["text"]) > 500:
            return dense_result
    except Exception as e:
        logger.warning("EXTRACTOR", f"Trafilatura/Dense fallback failed: {e}")

    # ---- TERTIARY: Playwright (Dynamic Content) ----
    # Only use for domains known to require JS or after all else fails
    # (Optional: check domain against list)
    try:
        logger.info("EXTRACTOR", f"Attempting dynamic scrape via Playwright for: {url}")
        dynamic_result = await scrape_dynamic(url)
        if dynamic_result and len(dynamic_result.get("text", "")) > 500:
            return dynamic_result
    except Exception as e:
        logger.error("EXTRACTOR", f"Playwright dynamic scrape failed for {url}: {e}\n{traceback.format_exc()}")

    # ---- LAST RESORT: Generic BeautifulSoup ----
    logger.debug("EXTRACTOR", "Falling back to generic BeautifulSoup scraper")
    return await asyncio.to_thread(generic_extract, url)
