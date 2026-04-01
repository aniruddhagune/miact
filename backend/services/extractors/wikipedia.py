import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}


def extract(url: str):
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")

        content = soup.find("div", {"id": "mw-content-text"})
        if not content:
            return None

        parser_output = content.find("div", {"class": "mw-parser-output"})
        if not parser_output:
            return None

        paragraphs = parser_output.find_all("p")

        text_parts = []
        for p in paragraphs:
            t = p.get_text().strip()
            if len(t) > 50:
                text_parts.append(t)

        text = " ".join(text_parts)

        title_tag = soup.find("h1")
        title = title_tag.get_text().strip() if title_tag else ""

        # ---- INFOBOX EXTRACTION (CORRECT PLACE) ----
        infobox_data = []

        infobox = soup.find("table", {"class": "infobox"})

        if infobox:
            rows = infobox.find_all("tr")

            for row in rows:
                header = row.find("th")
                data = row.find("td")

                if not header or not data:
                    continue

                key = header.get_text(strip=True).lower()
                value = data.get_text(" ", strip=True)

                # normalize
                value = (
                    value
                    .replace("\xa0", " ")
                    .replace("·", " ")
                    .replace("╖", " ")
                    .replace("–", "-")
                    .replace("û", "-")
                )

                infobox_data.append({
                    "aspect": key,
                    "value": value,
                    "type": "table"
                })

        if not text or len(text) < 300:
            return None

        return {
            "title": title,
            "published_at": None,
            "text": text,
            "tables": infobox_data,   # 👈 IMPORTANT
            "method": "wikipedia",
            "source": url
        }

    except Exception as e:
        print("[WIKIPEDIA ERROR]", e)
        return None