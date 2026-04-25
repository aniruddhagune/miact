# ---- DOMAIN SIGNALS ----
# Fine-grained query type classification

DOMAIN_SIGNALS = {
    "tech_phone": [
        "phone", "smartphone", "mobile",
        "battery", "camera", "display", "processor", "ram", "storage",
        "snapdragon", "mediatek", "dimensity", "vs",
        "gsmarena", "devicespecifications",
    ],
    "tech_laptop": [
        "laptop", "notebook", "macbook", "chromebook",
        "intel", "ryzen", "amd", "nvidia", "rtx", "gtx",
        "notebookcheck", "rtings",
    ],
    "news_accident": [
        "crash", "collision", "explosion", "fire", "accident",
        "killed", "dead", "died", "injured", "wounded", "missing",
    ],
    "news_change": [
        "price hike", "price cut", "new law", "policy", "regulation",
        "election", "government", "budget", "tax", "reform",
        "inflation", "rate change", "announced",
    ],
    "news_generic": [
        "news", "latest", "update", "report", "incident",
        "war", "summit", "meeting", "festival", "ceremony",
        "revolt", "protest", "riot", "happened", "situation",
        "event", "current", "today", "yesterday",
    ],
    "general": [
        "weather", "who is", "who was", "where is", "when did",
        "how to", "why does", "meaning of", "definition",
        "recipe", "distance", "time in", "population",
    ]
}

# Known phone brands — used for entity-type inference from name alone
PHONE_BRANDS = [
    "oneplus", "samsung", "apple", "iphone", "pixel", "google pixel",
    "xiaomi", "redmi", "poco", "realme", "vivo", "oppo", "motorola",
    "nothing phone", "iqoo", "sony xperia", "nokia",
]

# Known laptop brands / product lines
LAPTOP_BRANDS = [
    "macbook", "thinkpad", "lenovo", "dell xps", "hp spectre", "asus rog",
    "asus zenbook", "acer", "surface pro", "surface laptop", "razer blade",
    "msi", "lg gram",
]


def infer_query_type(query: str, entities: list = None, confirmed_domains: list = None) -> str:
    """
    Primary: infer from entity names (brand patterns).
    Secondary: confirm via domain signals from query text or result URLs.
    Returns a fine-grained type string, e.g. 'tech_phone', 'tech_laptop', 'news_accident'.
    """
    text = query.lower()
    ents = [e.lower() for e in (entities or [])]

    # ---- PRIMARY: entity name inference ----
    for brand in PHONE_BRANDS:
        if any(brand in e for e in ents) or brand in text:
            return "tech_phone"
    for brand in LAPTOP_BRANDS:
        if any(brand in e for e in ents) or brand in text:
            return "tech_laptop"

    # ---- SECONDARY: signal-based classification ----
    scores = {}
    for qtype, signals in DOMAIN_SIGNALS.items():
        scores[qtype] = sum(1 for s in signals if s in text)

    # Also check any confirmed result domains
    if confirmed_domains:
        for domain in confirmed_domains:
            d = domain.lower()
            if any(td in d for td in ["gsmarena", "devicespecifications"]):
                scores["tech_phone"] = scores.get("tech_phone", 0) + 2
            elif any(td in d for td in ["notebookcheck", "rtings", "laptopmag"]):
                scores["tech_laptop"] = scores.get("tech_laptop", 0) + 2
            elif any(td in d for td in ["bbc", "reuters", "ndtv", "hindustantimes"]):
                # Pick most specific news type
                for ntype in ["news_accident", "news_change", "news_generic"]:
                    scores[ntype] = scores.get(ntype, 0) + 1

    if not any(scores.values()):
        return "general"

    return max(scores, key=scores.get)