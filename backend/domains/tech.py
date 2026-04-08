# Trusted Sources — per query type
TRUSTED_DOMAINS_PHONE = [
    "gsmarena.com",
    "devicespecifications.com",
    "wikipedia.org",
    # Phone manufacturer sites
    "oneplus.in", "oneplus.com",
    "apple.com",
    "samsung.com",
    "mi.com",
    "realme.com",
    "vivo.com",
    "oppo.com",
    "motorola.com",
    "google.com/phones",
    "nothing.tech",
]

TRUSTED_DOMAINS_LAPTOP = [
    "notebookcheck.net",
    "rtings.com",
    "wikipedia.org",
    "laptopmag.com",
    "tomsguide.com",
    "techradar.com",
    "lenovo.com",
    "dell.com",
    "hp.com",
    "asus.com",
    "apple.com",
]

TRUSTED_DOMAINS_GENERAL = [
    "wikipedia.org",
]

# Legacy flat list — kept for backward compatibility
TRUSTED_DOMAINS = TRUSTED_DOMAINS_PHONE + TRUSTED_DOMAINS_LAPTOP

SHOPPING_DOMAINS = [
    "amazon.in",
    "flipkart.com"
]


def get_trusted_domains(query_type: str) -> list:
    """Return the right trusted domain list based on parsed query type."""
    if query_type == "tech_phone":
        return TRUSTED_DOMAINS_PHONE
    if query_type == "tech_laptop":
        return TRUSTED_DOMAINS_LAPTOP
    # news is handled in news.py
    return TRUSTED_DOMAINS_GENERAL

# Aspect Detection
ASPECT_KEYWORDS = {
    "battery": ["battery", "battery life",],
    "camera": ["camera", "cameras", "lens", "mp"],
    "display": ["display", "screen", "resolution", "oled", "amoled", "lcd", "refresh rate", "nits"],
    "processor": ["processor", "chip", "cpu", "chipset"],
    "graphics": ["graphics", "gpu"],
    "ram": ["ram", "memory"],
    "storage": ["storage"],
    "design": ["design", "build", "body"],
    "price": ["price", "cost"],
    "biometric": ["fingerprint", "scanner", "face", "facial"],
    "specifications": ["ip", "water-resistant", "waterproof"],
    "speakers": ["speaker", "speakers", "stereo", "mono", "lufs"],
    "performance": ["performance", "speed", "fast", "slow"],
    "audio": ["audio", "sound"],
    "power": ["power"],
    "charging": ["charging", "wireless charging", "wired charging", "fast charging", "Quick Charge", "Warp Charge", "SuperVOOC", "HyperCharge", "SuperCharge", "Power Delivery"],
    "connectivity": ["bluetooth", "wi-fi", "wifi", "wlan", "wireless"]
}

ASPECT_MAPPING = {
    "noise cancellation": "audio",
    "speaker": "audio",
    "lens": "camera",
    "fingerprint": "biometric",
    "gpu": "graphics",
    "cpu": "processor",
}


NOISE_TERMS = [
    "model", "version", "edition",
    "specs", "specification", "specifications"
]

CATEGORY_TERMS = [
    "smartphone", "phone", "mobile", "device",
    "laptop", "notebook"
]

DESCRIPTOR_TERMS = [
    "max", "pro", "plus", "ultra", "series", "mini", "se", "lite", "fe", "compact", "standard"
]

# URL Categorization Keywords
URL_TYPE_KEYWORDS = {
    "specs": ["specs", "specification", "specifications", "features", "full-specifications"],
    "review": ["review", "hands-on", "rating", "assessment", "analysis"],
    "comparison": ["vs", "compare", "comparison", "versus", "or"],
    "news": ["news", "article", "story", "updates", "flash"],
    "rumored": ["rumor", "rumoured", "leak", "leaked", "upcoming", "concept"]
}

# Numeric Extraction

TECH_NUMERIC_PATTERNS = [
    r"([\d,]+(?:\.\d+)?)\s*(mah)",
    r"(\d+(?:\.\d+)?)\s*(mp|megapixel|megapixels)",
    r"(\d+(?:\.\d+)?)\s*(mm)",
    r"(\d+(?:\.\d+)?)\s*(px|pixels|ppi)",
    r"(\d+(?:\.\d+)?)\s*(hz|hertz)",
    r"(\d+(?:\.\d+)?)\s*(kb|mb|gb|tb|pb)",
    r"(\d+(?:\.\d+)?)\s*(w|watts)",
    r"(\d+(?:\.\d+)?)\s*(inch|inches|cm)",
    r"(\d+(?:\.\d+)?)\s*(db|decibels)",
    r"(\d+(?:\.\d+)?)\s*(nits|nit)",
    r"(-?\d+(?:\.\d+)?)\s*(lufs)",
]

# ---- NUMERIC VALUE → ASPECT REFINEMENT ----

UNIT_ASPECT_MAPPING = {
    "gb": "storage",
    "tb": "storage",
    "mb": "storage",

    "mah": "battery",
    "mA·h": "battery",
    "mA h": "battery",

    "hz": "display",
    "ppi": "display",
    "px": "display",

    "inch": "display",
    "inches": "display",
    "cm": "display",

    "mp": "camera",
    "mm": "camera",

    "w": "power",
    "watts": "power",

    "nits": "display",
    "nit": "display",
    "lufs": "speakers"
}

# Processor Specific

TECH_NAMED_PATTERNS = [
    # Handheld
    r"(snapdragon\s?\d+(?:\s?gen\s?\d+)?)",
    r"(mediatek\s?\w+\s?\d*)",
    r"(apple\s?\d+\s?\d+\w*)",
    r"(arm\s?\d+\s?\d+\w*)",
    r"(qualcomm\s?\d+\s?\d+\w*)",
    r"(adreno\s?\d+\s?\d+\w*)",

    # PCs
    r"(intel\s?(i[3579]-?\d+\w*))",
    r"(ryzen\s?\d+\s?\d+\w*)",
    r"(amd\s?\d+\s?\d+\w*)",
    r"(radeon\s?\d+\s?\d+\w*)",
    r"(nvidia\s?\d+\s?\d+\w*)",
    r"(gtx\s?\d+\s?\d+\w*)",
    r"(rtx\s?\d+\s?\d+\w*)",

    # Storage
    r"(ufs\s?\d+\.\d+)",
    r"(lpddr\d+)",
    r"(ddr\d+)",

    # Connectivity
    r"(bluetooth\s?\d+(?:\.\d+)?)",
    r"(wi-fi\s?\d+[a-z]*)",
    r"(wifi\s?\d+[a-z]*)"
]

# ---- NAMED VALUE MAPPING ----

NAMED_ENTITY_MAPPING = {
    "processor": [
        "snapdragon", "mediatek", "intel", "ryzen", "apple", "qualcomm"
    ],
    "graphics": [
        "adreno", "rtx", "gtx", "radeon", "nvidia"
    ],
    "display": [
        "amoled", "oled", "lcd", "8-bit", "10-bit",
    ],
    "storage": ["ufs"],
    "ram": ["lpddr", "ddr"],
    "connectivity": ["bluetooth", "wi-fi", "wifi"]
}

# Dates

TECH_DATE_KEYWORDS = {
    "release_date": ["release", "released", "launched"],
    "announcement_date": ["announce", "announced"],
    "revealed_date": ["reveal", "revealed", "showcased", "unveiled"],
    "discontinued_date": ["discontinued", "retired"],
    "update_date": ["update", "updated", "updates until"]
}

# ---- CATEGORIZATION GROUPS (Phase 3 Alignment) ----

TECH_CATEGORY_MAP = {
    # Dates
    "announced": "Dates",
    "status": "Dates",
    "released": "Dates",
    "release_date": "Dates",
    "announcement_date": "Dates",
    
    # Core
    "os": "Core",
    "chipset": "Core",
    "processor": "Core",
    "cpu": "Core",
    "gpu": "Core",
    "graphics": "Core",
    "platform": "Core",
    "system on chip": "Core",
    
    # Memory
    "card slot": "Memory",
    "internal": "Memory",
    "ram": "Memory",
    "memory": "Memory",
    "storage": "Memory",
    
    # Connectivity
    "wlan": "Connectivity",
    "bluetooth": "Connectivity",
    "positioning": "Connectivity",
    "nfc": "Connectivity",
    "radio": "Connectivity",
    "usb": "Connectivity",
    "connectivity": "Connectivity",
    
    # Display
    "type": "Display",
    "size": "Display",
    "resolution": "Display",
    "protection": "Display",
    "refresh rate": "Display",
    "screen": "Display",
    "display": "Display"
}

def get_aspect_group(aspect: str) -> str:
    """Return the high-level category for a tech aspect."""
    return TECH_CATEGORY_MAP.get(aspect.lower(), "Other")

def group_aspects(records: list) -> dict:
    """Group flat aspect records into a categorized dictionary."""
    grouped = {}
    for r in records:
        group = get_aspect_group(r.get("aspect", ""))
        if group not in grouped:
            grouped[group] = []
        grouped[group].append(r)
    return grouped