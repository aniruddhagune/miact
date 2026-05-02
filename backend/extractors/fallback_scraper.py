"""
A robust, tag-dense fallback scraper for sites where newspaper misses content.
Utilizes trafilatura for high-quality extraction and manual heuristics as a secondary fallback.
"""
import trafilatura
from bs4 import BeautifulSoup
from backend.services.http_client import get as http_get
from backend.utils.logger import logger

def extract_dense_text(url: str, min_char_len: int = 35) -> dict:
    """
    Primary fallback using Trafilatura, secondary using manual p/span extraction.
    Returns {title, text, method, source}.
    """
    logger.debug("EXTRACTOR", f"Fallback scraper triggered for: {url}")
    
    # ---- 1. Trafilatura (High Quality Extraction) ----
    try:
        downloaded = trafilatura.fetch_url(url)
        if downloaded:
            extracted_text = trafilatura.extract(downloaded, include_comments=False, include_tables=False)
            if extracted_text and len(extracted_text) > 500:
                logger.info("EXTRACTOR", f"Successfully extracted via Trafilatura: {len(extracted_text)} chars")
                return {
                    "title": "", # Trafilatura doesn't always return title in extract()
                    "text": extracted_text,
                    "method": "trafilatura",
                    "source": url
                }
    except Exception as e:
        logger.warning("EXTRACTOR", f"Trafilatura failed for {url}: {e}")

    # ---- 2. Manual Heuristics (Last Resort) ----
    try:
        logger.debug("EXTRACTOR", "Attempting manual p/span fallback")
        response = http_get(url)
        if not response or response.status_code != 200:
            return {"text": "", "error": "HTTP fetch failed"}
            
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.extract()
            
        # Target Tags
        tags = soup.find_all(["p", "span"])
        
        content_blocks = []
        for tag in tags:
            clean_text = tag.get_text().strip()
            # Only keep 'dense' text blocks to avoid UI noise (buttons, labels)
            if len(clean_text) >= min_char_len:
                # Basic check to avoid navigational 'Click here' style text
                if "|" in clean_text or ">>" in clean_text:
                    continue
                content_blocks.append(clean_text)
                
        full_text = "\n\n".join(content_blocks)
        
        if full_text:
            logger.info("EXTRACTOR", f"Manual fallback successful: {len(full_text)} chars")
        
        return {
            "title": soup.title.string.strip() if soup.title else "",
            "text": full_text,
            "method": "fallback_dense",
            "source": url
        }
    except Exception as e:
        logger.error("EXTRACTOR", f"Manual fallback failed for {url}: {e}")
        return {"text": "", "error": str(e)}
