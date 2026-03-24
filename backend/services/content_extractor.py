from newspaper import Article
import requests
from bs4 import BeautifulSoup


def extract_content(url: str):
    try:
        article = Article(url)
        article.download()
        article.parse()

        text = article.text

        # ---- fallback condition ----
        if len(text) < 500:  # too small → likely incomplete
            return fallback_extract(url)

        return {
            "title": article.title,
            "text": text,
            "method": "newspaper"
        }

    except Exception:
        return fallback_extract(url)
    
def fallback_extract(url: str):
    try:
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(response.text, "html.parser")

        paragraphs = soup.find_all("p")
        text = " ".join(p.get_text() for p in paragraphs)

        title = soup.title.string if soup.title else ""

        return {
            "title": title,
            "text": text,
            "method": "fallback_bs4"
        }

    except Exception as e:
        return {
            "error": str(e),
            "url": url
        }