# Currently works for simple, comma separated, and "vs" queries.

import re
from backend.services.mapper_domain import detect_domain

ATTRIBUTE_KEYWORDS = {
    "battery": ["battery", "mah"],
    "price": ["price", "cost"],
    "camera": ["camera", "mp"],
    "display": ["display", "screen"],
    "size": ["size", "length", "width", "height"],
    "power": ["watt", "watts"]
}

NEWS_KEYWORDS = [
    "news", "latest", "update", "war", "election",
    "launch", "announcement", "report"
]


def parse_query(query: str):
    original_query = query.strip()
    query_lower = query.lower().strip()

    # ---- NEWS DETECTION ----
    if any(word in query for word in NEWS_KEYWORDS):
        return {
            "mode": "news",
            "original": original_query,
            "entities": [original_query],
            "attribute": None
        }

    # ---- ATTRIBUTE DETECTION ----
    attribute = None
    for attr, keywords in ATTRIBUTE_KEYWORDS.items():
        if any(word in query_lower for word in keywords):
            attribute = attr
            break

    # ---- CLEAN QUERY (remove attribute words) ----
    clean_query = original_query
    if attribute:
        for word in ATTRIBUTE_KEYWORDS[attribute]:
            clean_query = re.sub(word, "", clean_query, flags=re.IGNORECASE)

    clean_query = clean_query.strip()

    # ---- COMPARISON ----
    if " vs " in query_lower or "," in query_lower:
        raw_parts = re.split(r",| vs ", original_query)

        entities = []

        for part in raw_parts:
            cleaned = part

            # remove attribute words from each entity
            if attribute:
                for word in ATTRIBUTE_KEYWORDS[attribute]:
                    cleaned = re.sub(word, "", cleaned, flags=re.IGNORECASE)

            cleaned = cleaned.strip()

            if cleaned:
                entities.append(cleaned)

        return {
            "mode": "product",
            "type": "comparison",
            "original": original_query,
            "entities": entities,
            "attribute": attribute
        }

    # ---- DEFAULT ----
    return {
        "mode": "product",
        "type": "simple",
        "original": original_query,
        "entities": [original_query],
        "attribute": None
    }