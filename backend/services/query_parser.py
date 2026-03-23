# Currently works for simple, comma separated, and "vs" queries.

import re

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
    query = query.lower().strip()

    # ---- Detect News ----
    if any(word in query for word in NEWS_KEYWORDS):
        return {
            "mode": "news",
            "entities": [query],
            "attribute": None
        }

    # ---- Detect Comparison ----
    if " vs " in query or "," in query:
        parts = re.split(r",| vs ", query)
        entities = [p.strip() for p in parts if p.strip()]

        return {
            "mode": "product",
            "type": "comparison",
            "entities": entities,
            "attribute": None
        }

    # ---- Detect Attribute ----
    attribute = None
    for attr, keywords in ATTRIBUTE_KEYWORDS.items():
        if any(word in query for word in keywords):
            attribute = attr
            break

    if attribute:
        entity = query
        for word in ATTRIBUTE_KEYWORDS[attribute]:
            entity = entity.replace(word, "")

        entity = entity.strip()

        return {
            "mode": "product",
            "type": "attribute",
            "entities": [entity],
            "attribute": attribute
        }

    # ---- Default: Direct Entity ----
    return {
        "mode": "product",
        "type": "simple",
        "entities": [query],
        "attribute": None
    }