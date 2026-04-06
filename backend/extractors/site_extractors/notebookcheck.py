from __future__ import annotations

import json
import re
from bs4 import BeautifulSoup

from backend.services.http_client import get as http_get


def _clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", value.replace("\xa0", " ")).strip()


def _parse_published_at(soup: BeautifulSoup) -> str | None:
    time_tag = soup.find("time", attrs={"datetime": True})
    if time_tag and time_tag.get("datetime"):
        return time_tag["datetime"]

    for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
        raw = script.string or script.get_text(" ", strip=True)
        if not raw:
            continue
        try:
            data = json.loads(raw)
        except Exception:
            continue

        items = data if isinstance(data, list) else [data]
        for item in items:
            if isinstance(item, dict) and item.get("@type") == "Article":
                published = item.get("datePublished")
                if published:
                    return str(published)

    return None


def parse_html(html: str, url: str) -> dict | None:
    soup = BeautifulSoup(html, "html.parser")

    title_tag = soup.find("h1")
    title = _clean_text(title_tag.get_text(" ", strip=True)) if title_tag else ""
    if not title and soup.title and soup.title.string:
        title = _clean_text(soup.title.string)

    published_at = _parse_published_at(soup)

    text_parts: list[str] = []

    intro = soup.select_one("div.nbcintroelwide_text div.nbcintroelwide_abstract")
    if intro:
        intro_text = _clean_text(intro.get_text(" ", strip=True))
        if intro_text:
            text_parts.append(intro_text)

    for p in soup.find_all("p"):
        paragraph = _clean_text(p.get_text(" ", strip=True))
        if len(paragraph) < 60:
            continue
        if any(skip in paragraph.lower() for skip in ["add to comparison", "see all specifications"]):
            continue
        text_parts.append(paragraph)

    seen_text = set()
    cleaned_parts = []
    for part in text_parts:
        if part not in seen_text:
            seen_text.add(part)
            cleaned_parts.append(part)

    extracted_tables = []
    seen_specs = set()
    for spec in soup.select("div.specs_whole div.specs_element"):
        aspect_el = spec.select_one("div.specs")
        if not aspect_el:
            continue

        detail_el = spec.select_one("div.specs_details")
        if not detail_el:
            continue

        aspect = _clean_text(aspect_el.get_text(" ", strip=True)).lower()
        value = _clean_text(detail_el.get_text(" ", strip=True))

        if not aspect or not value:
            continue

        key = (aspect, value.lower())
        if key in seen_specs:
            continue
        seen_specs.add(key)

        extracted_tables.append({
            "aspect": aspect,
            "value": value,
            "type": "table",
        })

    opinions = []
    seen_opinions = set()
    opinion_selectors = [
        ("span.pro_eintrag", "notebookcheck_pro"),
        ("span.contra_eintrag", "notebookcheck_con"),
    ]

    for selector, source in opinion_selectors:
        for item in soup.select(selector):
            text = _clean_text(item.get_text(" ", strip=True))
            if len(text) < 3:
                continue
            lowered = text.lower()
            if lowered in seen_opinions:
                continue
            seen_opinions.add(lowered)
            opinions.append({
                "text": text,
                "source": source,
                "type": "subjective",
            })

    return {
        "title": title or "Notebookcheck",
        "published_at": published_at,
        "text": " ".join(cleaned_parts),
        "tables": extracted_tables,
        "opinions": opinions,
        "method": "notebookcheck",
        "source": url,
    }


def extract(url: str):
    try:
        response = http_get(url, referer="https://www.google.com/search?q=notebookcheck")
        if not response:
            return None
        return parse_html(response.text, url)
    except Exception as e:
        print("[NOTEBOOKCHECK EXTRACT ERROR]", e)
        return None
