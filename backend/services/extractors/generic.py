import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}


def extract(url: str):
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
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
            "published_at": None,
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