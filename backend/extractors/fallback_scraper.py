"""
A robust, tag-dense fallback scraper for sites where newspaper misses content.
Targets 'p' and 'span' tags with length-based heuristics.
"""
from bs4 import BeautifulSoup
from backend.services.http_client import get as http_get

def extract_dense_text(url: str, min_char_len: int = 35) -> dict:
    """
    Manually scrape text from p and span tags.
    Returns {title, text, method}.
    """
    try:
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
        
        return {
            "title": soup.title.string.strip() if soup.title else "",
            "text": full_text,
            "method": "fallback_dense",
            "source": url
        }
    except Exception as e:
        return {"text": "", "error": str(e)}
