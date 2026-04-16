import re
from backend.services.mapper_domain import detect_domain
from backend.domains.tech import ASPECT_KEYWORDS, UNIT_ASPECT_MAPPING
from backend.domains.news import NEWS_KEYWORDS
from backend.utils.logger import logger


SOURCE_KEYWORDS = [
    "wikipedia",
    "gsmarena",
    "amazon",
    "flipkart"
    ]


# -------------------------------
# ENTITY (FIRST — DO NOT TOUCH)
# -------------------------------
def extract_entity(query: str, attribute: str = None, source: str = None):
    query = query.lower()

    # remove source
    if source:
        query = re.sub(rf"\b{source}\b", "", query)

    # remove attribute keywords
    if attribute:
        from backend.domains.tech import ASPECT_KEYWORDS
        for word in ASPECT_KEYWORDS.get(attribute, []):
            query = re.sub(rf"\b{word}\b", "", query)

    # remove filter phrases
    query = re.sub(r"(under|less than|above|over|greater than)\s+\d+", "", query)

    # remove standalone units (mah, gb, etc.)
    query = re.sub(r"\b\d+\s*(mah|mp|hz|gb|tb|w)\b", "", query)

    # clean spaces
    query = re.sub(r"\s+", " ", query).strip()

    # split comparisons
    parts = re.split(r"\bvs\b|,", query)

    return [p.strip() for p in parts if p.strip()]


# -------------------------------
# ATTRIBUTE
# -------------------------------
def detect_attribute(query_lower: str):
    for aspect, keywords in ASPECT_KEYWORDS.items():
        for word in keywords:
            if re.search(rf"\b{word}\b", query_lower):
                return aspect

    # fallback: detect from unit
    for unit, aspect in UNIT_ASPECT_MAPPING.items():
        if re.search(rf"\b{unit}\b", query_lower):
            return aspect

    return None


# -------------------------------
# FILTER
# -------------------------------
def detect_filter(query_lower: str):
    # explicit filters
    patterns = [
        (r"(under|less than|below)\s+(\d+)", "lt"),
        (r"(above|over|greater than)\s+(\d+)", "gt")
    ]

    for pattern, op in patterns:
        match = re.search(pattern, query_lower)
        if match:
            return {
                "operator": op,
                "value": int(match.group(2))
            }

    # implicit (e.g. 4500 mah)
    match = re.search(r"\b(\d+)\s*(mah|mp|hz|gb|tb|w)\b", query_lower)

    if match:
        return {
            "operator": "eq",
            "value": int(match.group(1))
        }



    return None


# -------------------------------
# SOURCE
# -------------------------------
def detect_source(query_lower: str):
    for word in SOURCE_KEYWORDS:
        if word in query_lower:
            return word
    return None


# -------------------------------
# MAIN PARSER
# -------------------------------
def parse_query(query: str):
    logger.debug("PARSER", f"Parsing query: '{query}'")
    original_query = query.strip()
    query_lower = original_query.lower()

    # ---- DOMAIN ----
    domain = detect_domain(query_lower)

    # ---- NEWS ----
    if any(word in query_lower for word in NEWS_KEYWORDS):
        res = {
            "mode": "news",
            "original": original_query,
            "entities": [],
            "attribute": None
        }
        logger.info("PARSER", "Query identified as NEWS mode")
        return res

    attribute = detect_attribute(query_lower)
    source = detect_source(query_lower)
    filter_data = detect_filter(query_lower)

    entities = extract_entity(query_lower, attribute, source)

    # ---- SOURCE ----
    source = detect_source(query_lower)
    if source:
        entities = [
            re.sub(rf"\b{source}\b", "", e).strip()
            for e in entities
        ]

    # ---- TYPE ----
    query_type = "comparison" if len(entities) > 1 else "simple"

    res = {
        "mode": "product",
        "type": query_type,
        "original": original_query,
        "entities": entities,
        "attribute": attribute,
        "filter": filter_data,
        "source": source
    }
    logger.info("PARSER", f"Parsed: mode={res['mode']}, type={res['type']}, entities={res['entities']}, attr={res['attribute']}")
    return res
