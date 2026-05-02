import re

from bs4 import BeautifulSoup

from backend.services.http_client import get as http_get
from backend.utils.date_extractor import extract_publication_date


def normalize_url(url: str) -> str:
    """
    Normalize tab-specific DeviceSpecifications URLs back to the canonical
    specifications page.

    Example:
      https://www.devicespecifications.com/en/model-height/7d8455de
      -> https://www.devicespecifications.com/en/model/7d8455de
    """
    return re.sub(
        r"(https?://www\.devicespecifications\.com/en/)model-[^/]+/([a-z0-9]+)",
        r"\1model/\2",
        url,
        flags=re.IGNORECASE,
    )


def extract(url: str):
    """
    Extracts purely structured tabular specs from devicespecifications.com.
    """
    try:
        normalized_url = normalize_url(url)
        response = http_get(normalized_url, referer="https://www.google.com/search?q=devicespecifications")
        if not response:
            return None
        soup = BeautifulSoup(response.content, "html.parser")

        # Support both modern and classic layouts
        table_classes = ["model-specifications-table-item", "model-information-table"]
        tables = []
        for cls in table_classes:
            tables.extend(soup.find_all("table", class_=cls))

        extracted_tables = []

        for table in tables:
            # Section header might be a <th> or a previous <h2>
            th = table.find("th")
            section_name = th.get_text(strip=True).lower() if th else ""

            # Fallback for section name from previous header if it's a model-information-table
            if not section_name:
                prev_h2 = table.find_previous("h2", class_="header")
                if prev_h2:
                    section_name = prev_h2.get_text(strip=True).lower()
                else:
                    prev_header = table.find_previous("header")
                    if prev_header and prev_header.h2:
                        section_name = prev_header.h2.get_text(strip=True).lower()

            rows = table.find_all("tr")
            for row in rows:
                all_tds = row.find_all("td")
                label_td = row.find("td", class_="cell-label") or (all_tds[0] if all_tds else None)
                value_td = row.find("td", class_="cell-value") or (all_tds[1] if len(all_tds) > 1 else None)

                if not label_td or not value_td or label_td == value_td:
                    continue

                # DeviceSpecifications often nests extra explanatory nodes in the label cell.
                for extra in label_td.find_all(["p", "div", "span"], recursive=True):
                    extra.decompose()

                aspect = label_td.get_text(strip=True).lower()

                if aspect == "type" and section_name:
                    aspect = f"{section_name} type"
                elif section_name in ["os", "operating system"]:
                    aspect = f"os {aspect}"

                value = value_td.get_text(" ", strip=True)
                value = re.sub(r"\s+", " ", value).strip()
                value = value.replace("\xa0", " ").replace("Â·", " ").replace("â•–", " ").replace("â€“", "-").lower()

                if aspect and value:
                    extracted_tables.append({
                        "aspect": aspect,
                        "value": value,
                        "type": "table"
                    })

        return {
            "title": soup.title.string if soup.title else "Device Specifications",
            "published_at": extract_publication_date(soup=soup, url=normalized_url),
            "text": "",
            "tables": extracted_tables,
            "method": "devicespecifications",
            "source": normalized_url
        }

    except Exception as e:
        print("[DEVICESPECIFICATIONS EXTRACT ERROR]", e)
        return None
