import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0.0.0 Safari/537.36"
}

def extract(url: str):
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(response.content, "html.parser")
        
        extracted_tables = []
        
        tables = soup.find_all("table")
        for table in tables:
            th = table.find("th")
            section_name = th.get_text(strip=True).lower() if th else ""

            rows = table.find_all("tr")
            for row in rows:
                ttl = row.find("td", class_="ttl")
                nfo = row.find("td", class_="nfo")
                
                if ttl and nfo:
                    aspect = ttl.get_text(strip=True).lower()
                    # Prepend section name for common 'type' aspect or 'our tests' section
                    if (aspect == "type" and section_name) or section_name == "our tests":
                        aspect = f"{section_name} {aspect}"
                    
                    for br in nfo.find_all("br"):
                        br.replace_with(" + ")
                        
                    value = nfo.get_text(" ", strip=True)
                    # Use regex to clean up common specification noise like #1, #2 footnotes
                    import re
                    value = re.sub(r"\s*\(#\d+\)\s*", " ", value)
                    value = value.replace("\xa0", " ").replace("·", " ").replace("╖", " ").replace("–", "-").lower()
                    # Clean up multiple spaces
                    value = re.sub(r"\s+", " ", value).strip()
                    
                    if aspect and value:
                        extracted_tables.append({
                            "aspect": aspect.strip(),
                            "value": value,
                            "type": "table"
                        })
                        
        # ---- OPINIONS EXTRACTION ----
        opinions = []
        user_comments_div = soup.find("div", id="user-comments")
        if user_comments_div:
            threads = user_comments_div.find_all("div", class_="user-thread")
            for thread in threads:
                opinion_text_p = thread.find("p", class_="uopin")
                if opinion_text_p:
                    # Clean up the text (handling potential <br> or ellipsis)
                    text = opinion_text_p.get_text(" ", strip=True)
                    # GSMArena comments often have "..." if truncated on main page, 
                    # but we'll take what's available.
                    opinions.append({
                        "text": text,
                        "source": "gsma_comment",
                        "type": "subjective"
                    })

        return {
            "title": soup.title.string if soup.title else "GSMArena",
            "published_at": None,
            "text": "",
            "tables": extracted_tables,
            "opinions": opinions, # New field
            "method": "gsmarena",
            "source": url
        }
    except Exception as e:
        print("[GSMARENA EXTRACT ERROR]", e)
        return None
