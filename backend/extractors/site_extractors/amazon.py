from __future__ import annotations

import re
from bs4 import BeautifulSoup

from backend.services.http_client import get as http_get
from backend.utils.date_extractor import extract_publication_date


def _clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", value.replace("\xa0", " ")).strip()


def _extract_title(soup: BeautifulSoup) -> str:
    selectors = [
        "#productTitle",
        "#title span",
        "span#title",
    ]
    for selector in selectors:
        node = soup.select_one(selector)
        if node:
            text = _clean_text(node.get_text(" ", strip=True))
            if text:
                return text
    return "Amazon"


def _extract_price_rows(soup: BeautifulSoup) -> list[dict]:
    rows = []
    seen = set()

    sale_selectors = [
        "span.a-price.aok-align-center span.a-offscreen",
        "span.a-price span.a-offscreen",
        "#corePrice_feature_div span.a-offscreen",
        "#price_inside_buybox",
        "#priceblock_dealprice",
        "#priceblock_ourprice",
        "#tp_price_block_total_price_ww span.a-offscreen",
    ]

    list_price_selectors = [
        "span.a-price.a-text-price span.a-offscreen",
        "#listPrice span.a-offscreen",
        "#basisPrice span.a-offscreen",
    ]

    def add_row(raw_text: str, kind: str):
        text = _clean_text(raw_text)
        if not text:
            return
        match = re.search(r"([₹$€£])\s*([\d,]+(?:\.\d{1,2})?)", text)
        if not match:
            return
        symbol, amount = match.groups()
        currency = {
            "₹": "INR",
            "$": "USD",
            "€": "EUR",
            "£": "GBP",
        }.get(symbol)
        normalized = amount.replace(",", "")
        key = (kind, normalized, currency)
        if key in seen:
            return
        seen.add(key)
        rows.append({
            "aspect": "price",
            "value": normalized,
            "unit": currency,
            "type": "table",
            "metadata": {
                "raw": text,
                "kind": kind,
            },
        })

    for selector in sale_selectors:
        for node in soup.select(selector):
            add_row(node.get_text(" ", strip=True), "sale_price")

    for selector in list_price_selectors:
        for node in soup.select(selector):
            add_row(node.get_text(" ", strip=True), "list_price")

    return rows


def _extract_bullets(soup: BeautifulSoup) -> tuple[list[dict], list[dict]]:
    tables = []
    opinions = []
    seen_bullets = set()

    bullet_selectors = [
        "#feature-bullets li",
        "#feature-bullets ul li",
        "#productFactsDesktop_feature_div li",
    ]

    for selector in bullet_selectors:
        for node in soup.select(selector):
            text = _clean_text(node.get_text(" ", strip=True))
            if len(text) < 8:
                continue
            lowered = text.lower()
            if lowered in seen_bullets:
                continue
            seen_bullets.add(lowered)
            tables.append({
                "aspect": "highlights",
                "value": text,
                "type": "table",
            })

            # Highlights on product pages are descriptive claims, so we keep them
            # separately as soft opinions for the downstream sentiment pipeline.
            opinions.append({
                "text": text,
                "source": "amazon_highlight",
                "type": "subjective",
            })

    return tables, opinions


def _extract_detail_tables(soup: BeautifulSoup) -> list[dict]:
    rows = []
    seen = set()

    selectors = [
        "#productDetails_techSpec_section_1 tr",
        "#productDetails_detailBullets_sections1 tr",
        "#technicalSpecifications_section_1 tr",
        "table.prodDetTable tr",
    ]

    for selector in selectors:
        for tr in soup.select(selector):
            key_node = tr.select_one("th") or tr.select_one("td.a-span3")
            value_node = tr.select_one("td") if tr.select_one("th") else tr.select_one("td.a-span9")

            if not key_node or not value_node:
                tds = tr.find_all("td")
                if len(tds) >= 2:
                    key_node, value_node = tds[0], tds[1]
                else:
                    continue

            aspect = _clean_text(key_node.get_text(" ", strip=True)).lower()
            value = _clean_text(value_node.get_text(" ", strip=True))

            if not aspect or not value or aspect == value.lower():
                continue

            key = (aspect, value.lower())
            if key in seen:
                continue
            seen.add(key)
            rows.append({
                "aspect": aspect,
                "value": value,
                "type": "table",
            })

    return rows


def _extract_reviews(soup: BeautifulSoup) -> list[dict]:
    opinions = []
    seen = set()

    containers = soup.select("[data-hook='review']")
    for review in containers:
        title_node = review.select_one("[data-hook='review-title']")
        body_node = review.select_one("[data-hook='review-body']")

        title = _clean_text(title_node.get_text(" ", strip=True)) if title_node else ""
        body = _clean_text(body_node.get_text(" ", strip=True)) if body_node else ""
        text = body or title
        if title and body and title.lower() not in body.lower():
            text = f"{title}. {body}"

        if len(text) < 8:
            continue

        lowered = text.lower()
        if lowered in seen:
            continue
        seen.add(lowered)

        opinions.append({
            "text": text,
            "source": "amazon_review",
            "type": "subjective",
        })

    return opinions


def parse_html(html: str, url: str) -> dict | None:
    soup = BeautifulSoup(html, "html.parser")

    title = _extract_title(soup)
    price_rows = _extract_price_rows(soup)
    bullet_rows, bullet_opinions = _extract_bullets(soup)
    detail_rows = _extract_detail_tables(soup)
    review_opinions = _extract_reviews(soup)

    text_parts = []
    if title:
        text_parts.append(title)
    for row in bullet_rows[:20]:
        text_parts.append(row["value"])
    for op in review_opinions[:20]:
        text_parts.append(op["text"])

    tables = price_rows + bullet_rows + detail_rows
    opinions = bullet_opinions + review_opinions

    return {
        "title": title,
        "published_at": extract_publication_date(soup=soup, url=url),
        "text": " ".join(text_parts),
        "tables": tables,
        "opinions": opinions,
        "method": "amazon",
        "source": url,
    }


def extract(url: str):
    try:
        response = http_get(url, referer="https://www.google.com/search?q=amazon+product")
        if not response:
            return None
        return parse_html(response.text, url)
    except Exception as e:
        print("[AMAZON EXTRACT ERROR]", e)
        return None
