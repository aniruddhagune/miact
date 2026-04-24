import re
from backend.services.mapper_domain import detect_domain
from backend.domains.tech import ASPECT_KEYWORDS, UNIT_ASPECT_MAPPING
from backend.domains.news import NEWS_KEYWORDS
from backend.domains.domain_signals import infer_query_type
from backend.nlp.query_intent import analyze_query_intent
from backend.domains.regions import REGIONS
from backend.utils.logger import logger


SOURCE_KEYWORDS = [
    "wikipedia",
    "gsmarena",
    "amazon",
    "flipkart"
    ]


# -------------------------------
# LOCALITY
# -------------------------------
def detect_locality(query_lower: str):
    """
    Detect if the query has a regional/local context.
    Returns (region_code, region_full_name) or (None, None).
    """
    # 1. Check for "in [Country]"
    for code, name in REGIONS.items():
        if f"in {name.lower()}" in query_lower or f"in {code.lower()}" in query_lower:
            return code, name
    
    # 2. Check for standalone regional markers
    for code, name in REGIONS.items():
        if f" {name.lower()} " in f" {query_lower} " or f" {code.lower()} " in f" {query_lower} ":
            return code, name

    return None, None


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

    # ---- CLASSIFY MODE ----
    # 1. Get fine-grained type
    query_type = infer_query_type(query_lower)
    
    # 2. Map to top-level mode
    if any(word in query_lower for word in NEWS_KEYWORDS) or query_type.startswith("news_"):
        mode = "news"
    elif query_type.startswith("tech_"):
        mode = "product"
    elif query_type == "general":
        mode = "general"
    else:
        # Fallback for ambiguous cases
        mode = "product" if any(brand in query_lower for brand in ["iphone", "samsung", "oneplus"]) else "general"

    # ---- INTENT ANALYSIS (NLP) ----
    intent = analyze_query_intent(original_query)

    # ---- DATA EXTRACTION ----
    attribute = detect_attribute(query_lower)
    source = detect_source(query_lower)
    filter_data = detect_filter(query_lower)

    # ---- ENTITY EXTRACTION ----
    if mode == "product":
        entities = extract_entity(query_lower, attribute, source)
    else:
        # For news/general, use NLP entities or aspects as subjects
        entities = intent.get("entities", [])
        if not entities and intent.get("aspects"):
            entities = intent["aspects"]
        
        # If still no entities, use the original query (cleaned)
        if not entities:
            entities = [original_query]

    # ---- LOCALITY DETECTION ----
    region_code, region_name = detect_locality(query_lower)

    # ---- MODE OVERRIDE (News Default-Mode) ----
    if mode == "general" and region_code:
        mode = "news"
        if attribute == "price":
            query_type = "news_change" # Financial news for price updates
        else:
            query_type = "news_generic"

    # ---- LAYOUT SUGGESTION ----
    if mode == "news":
        layout = "news_feed"
    elif mode == "product" and len(entities) > 1:
        layout = "comparison_table"
    elif mode == "product":
        layout = "single_spec_view"
    else:
        layout = "general_list"

    # ---- FINAL RESULT ----
    res = {
        "mode": mode,
        "query_type": query_type,
        "type": "comparison" if len(entities) > 1 else "simple",
        "original": original_query,
        "entities": entities,
        "attribute": attribute,
        "filter": filter_data,
        "source": source,
        "locality": {"code": region_code, "name": region_name},
        "layout": layout,
        "intent": intent
    }

    logger.info("PARSER", f"Parsed: mode={res['mode']}, qtype={res['query_type']}, locality={region_code}, layout={layout}")
    return res
