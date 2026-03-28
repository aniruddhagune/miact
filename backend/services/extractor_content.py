from newspaper import Article
import requests
from bs4 import BeautifulSoup


HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0.0.0 Safari/537.36"
}


def extract_content(url: str):
    # ---- SPECIAL CASE: Wikipedia ----
    if "wikipedia.org" in url:
        return extract_wikipedia(url)

    try:
        article = Article(url)
        article.download()
        article.parse()

        text = article.text

        # ---- fallback if too small ----
        if len(text) < 500:
            return fallback_extract(url)

        return {
            "title": article.title,
            "text": text,
            "method": "newspaper",
            "source": url
        }

    except Exception:
        return fallback_extract(url)


def extract_wikipedia(url: str):
    try:
        response = requests.get(url, headers=HEADERS)
        soup = BeautifulSoup(response.text, "html.parser")

        content = soup.find("div", {"id": "mw-content-text"})
        if not content:
            return fallback_extract(url)

        parser_output = content.find("div", {"class": "mw-parser-output"})
        if not parser_output:
            return fallback_extract(url)

        paragraphs = parser_output.find_all("p")

        text_parts = []
        for p in paragraphs:
            t = p.get_text().strip()
            if len(t) > 50:
                text_parts.append(t)

        text = " ".join(text_parts)

        title_tag = soup.find("h1")
        title = title_tag.get_text() if title_tag else ""

        return {
            "title": title,
            "text": text,
            "method": "wikipedia_bs4",
            "source": url
        }

    except Exception as e:
        return {
            "error": str(e),
            "url": url
        }


def fallback_extract(url: str):
    try:
        response = requests.get(url, headers=HEADERS)
        soup = BeautifulSoup(response.text, "html.parser")

        paragraphs = soup.find_all("p")

        text = " ".join(
            p.get_text().strip()
            for p in paragraphs
            if len(p.get_text().strip()) > 30
        )

        title = soup.title.string if soup.title else ""

        return {
            "title": title,
            "text": text,
            "method": "fallback_bs4",
            "source": url
        }

    except Exception as e:
        return {
            "error": str(e),
            "url": url
        }