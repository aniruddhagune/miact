from bs4 import BeautifulSoup
from backend.services.http_client import get as http_get

def extract(url: str):
    """
    Extracts purely structured tabular specs from devicespecifications.com.
    """
    try:
        response = http_get(url, referer="https://www.google.com/search?q=devicespecifications")
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
                # Support both class-based and positional lookup
                label_td = row.find("td", class_="cell-label") or row.find_all("td")[0] if row.find_all("td") else None
                value_td = row.find("td", class_="cell-value") or row.find_all("td")[1] if len(row.find_all("td")) > 1 else None
                
                if not label_td or not value_td or label_td == value_td:
                    continue
                
                # DeviceSpecifications often has extra info in <p> tags within the label cell.
                # We want the main label text only.
                # Remove any <p> or secondary tags before getting text
                for extra in label_td.find_all(["p", "div", "span"], recursive=True):
                    extra.decompose()
                
                aspect = label_td.get_text(strip=True).lower()

                if aspect == "type" and section_name:
                    aspect = f"{section_name} type"
                elif section_name in ["os", "operating system"]:
                     aspect = f"os {aspect}"
                    
                # Clean value: remove approximate bullets and extra whitespace
                value = value_td.get_text(" ", strip=True)
                
                import re
                # Remove approximate bullets (often a span with class approximation-bullet)
                value = re.sub(r"\s+", " ", value).strip()
                value = value.replace("\xa0", " ").replace("·", " ").replace("╖", " ").replace("–", "-").lower()
                
                if aspect and value:
                    extracted_tables.append({
                        "aspect": aspect,
                        "value": value,
                        "type": "table"
                    })
                    
        return {
            "title": soup.title.string if soup.title else "Device Specifications",
            "published_at": None,
            "text": "",
            "tables": extracted_tables,
            "method": "devicespecifications",
            "source": url
        }

    except Exception as e:
        print("[DEVICESPECIFICATIONS EXTRACT ERROR]", e)
        return None
