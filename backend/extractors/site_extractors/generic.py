from bs4 import BeautifulSoup
from backend.services.http_client import get as http_get
from backend.utils.date_extractor import extract_publication_date


def extract(url: str):
    try:
        response = http_get(url)
        if not response:
            return {"title": "", "published_at": None, "text": "", "method": "blocked", "source": url}

        soup = BeautifulSoup(response.text, "html.parser")

        paragraphs = soup.find_all("p")

        text = " ".join(
            p.get_text().strip()
            for p in paragraphs
            if len(p.get_text().strip()) > 30
        )

        title = soup.title.string.strip() if soup.title and soup.title.string else ""

        return {
            "title": title,
            "published_at": extract_publication_date(soup=soup, url=url),
            "text": text,
            "method": "generic",
            "source": url
        }

    except Exception as e:
        return {
            "title": "",
            "published_at": None,
            "text": "",
            "method": "error",
            "source": url,
            "error": str(e)
        }