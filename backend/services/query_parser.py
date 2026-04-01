# Currently works for simple, comma separated, and "vs" queries.

import re
from backend.services.mapper_domain import detect_domain

from backend.domains.tech import ASPECT_KEYWORDS, NON_ASPECT_TERMS, UNIT_ASPECT_MAPPING
from backend.domains.news import NEWS_KEYWORDS

def extract_filter(query_lower: str):
    # explicit filter
    patterns = [
        (r"(under|less than|lower)\s+(\d+)", "lt"),
        (r"(above|over|greater than|higher)\s+(\d+)", "gt")
    ]

    for pattern, operator in patterns:
        match = re.search(pattern, query_lower)
        if match:
            value = int(match.group(2))
            return operator, value

    # implicit filter (4500 mah)
    match = re.search(r"(\d+)\s*(mah|mp|hz|gb|tb|w)", query_lower)
    if match:
        value = int(match.group(1))
        return "eq", value  # treat as equality for now

    return None, None

def detect_unit_aspect(query_lower: str):
    for unit, aspect in UNIT_ASPECT_MAPPING.items():
        if re.search(rf"\b{unit}\b", query_lower):
            return aspect, unit
    return None, None

def parse_query(query: str):
    original_query = query.strip()
    query_lower = query.lower().strip()

    # ---- DOMAIN DETECTION ----
    domain = detect_domain(query_lower)

    # ---- NEWS DETECTION ----
    if any(word in query_lower for word in NEWS_KEYWORDS):
        return {
            "mode": "news",
            "original": original_query,
            "entities": [],
            "attribute": None
        }
    
    # ---- FILTER DETECTION ----
    operator, value = extract_filter(query_lower)
    filter_data = None

    unit_aspect, detected_unit = detect_unit_aspect(query_lower)

    # ---- ATTRIBUTE DETECTION ----
    attribute = None

    # priority 1: explicit keywords
    for aspect, keywords in ASPECT_KEYWORDS.items():
        if any(word in query_lower for word in keywords):
            attribute = aspect
            break

    # priority 2: infer from unit
    if not attribute and unit_aspect:
        attribute = unit_aspect

    # ---- FILTER BINDING ----
    if operator and value:
        filter_data = {
            "aspect": attribute,
            "operator": operator,
            "value": value
        }

    # ---- CLEAN QUERY ----
    clean_query = original_query
    # remove aspect keywords
    if attribute:
        for word in ASPECT_KEYWORDS[attribute]:
            clean_query = re.sub(rf"\b{word}\b", "", clean_query, flags=re.IGNORECASE)

    # remove detected unit ONLY if it's not needed anymore
    if detected_unit:
        clean_query = re.sub(rf"\b{detected_unit}\b", "", clean_query, flags=re.IGNORECASE)

    # remove generic non-aspect terms (THIS FIXES "specs")
    for word in NON_ASPECT_TERMS:
        clean_query = re.sub(rf"\b{word}\b", "", clean_query, flags=re.IGNORECASE)

    clean_query = re.sub(
        r"(under|less than|lower|above|over|greater than|higher)\s+\d+",
        "",
        clean_query,
        flags=re.IGNORECASE
    )

    clean_query = re.sub(r"\b\d+\b", "", clean_query)

    # ---- COMPARISON ----
    if " vs " in query_lower or "," in query_lower:
        raw_parts = re.split(r",| vs ", original_query)

        entities = []

        for part in raw_parts:
            cleaned = part

            if attribute:
                for word in ASPECT_KEYWORDS[attribute]:
                    cleaned = re.sub(rf"\b{word}\b", "", cleaned, flags=re.IGNORECASE)

            for word in NON_ASPECT_TERMS:
                cleaned = re.sub(rf"\b{word}\b", "", cleaned, flags=re.IGNORECASE)

            cleaned = re.sub(r"(under|less than|above|over|greater than)\s+\d+", "", cleaned, flags=re.IGNORECASE)
            cleaned = cleaned.strip()

            if cleaned:
                entities.append(cleaned)

        return {
            "mode": "product",
            "type": "comparison",
            "original": original_query,
            "entities": entities,
            "attribute": attribute,
            "filter": filter_data
        }

    # ---- DEFAULT ----
    cleaned = clean_query.strip().lower()

    # reject weak entities:
    if (
        not cleaned
        or len(cleaned) < 3
        or cleaned in UNIT_ASPECT_MAPPING.keys()
    ):
        entities = []
    else:
        entities = [cleaned]

    return {
        "mode": "product",
        "type": "simple",
        "original": original_query,
        "entities": entities,
        "attribute": attribute,
        "filter": filter_data
    }