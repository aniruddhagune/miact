# Trusted Sources
TRUSTED_DOMAINS = [
    # Generic
    "wikipedia.org",
    # Phones
    "gsmarena.com",
    "devicespecifications.com",
    # Laptops
    
    # Phone Company Sites
    "oneplus.in",
    "apple.com",
    "samsuing.com",
    "mi.com",
    "realme.com/in/",
    "vivo.com",
    "oppo.com",
    "motorola.in"

]

SHOPPING_DOMAINS = [
    "amazon.in",
    "flipkart.com"
]

# Aspect Detection
ASPECT_KEYWORDS = {
    "battery": ["battery", "battery life",],
    "camera": ["camera", "cameras", "lens", "mp"],
    "display": ["display", "screen", "resolution", "oled", "amoled", "lcd", "refresh rate"],
    "processor": ["processor", "chip", "cpu", "chipset"],
    "graphics": ["graphics", "gpu"],
    "ram": ["ram", "memory"],
    "storage": ["storage"],
    "design": ["design", "build", "body"],
    "price": ["price", "cost"],
    "biometric": ["fingerprint", "scanner", "face", "facial"],
    "certification": ["ip", "water-resistant", "waterproof"],
    "speakers": ["speaker", "speakers", "stereo", "mono"],
    "performance": ["performance", "speed", "fast", "slow"],
    "audio": ["audio", "sound"],
    "power": ["power"]
}

ASPECT_MAPPING = {
    "noise cancellation": "audio",
    "speaker": "audio",
    "lens": "camera",
    "fingerprint": "biometric",
    "gpu": "graphics",
    "cpu": "processor",
}


NON_ASPECT_TERMS = [
    "smartphone", "phone", "mobile", "device",
    "max", "pro", "series",
    "model", "version", "edition", "specs", "specifications"
]

# Numeric Extraction

TECH_NUMERIC_PATTERNS = [
    r"(\d+(?:\.\d+)?)\s*(mah)",
    r"(\d+(?:\.\d+)?)\s*(mp|megapixel|megapixels)",
    r"(\d+(?:\.\d+)?)\s*(mm)",
    r"(\d+(?:\.\d+)?)\s*(px|pixels|ppi)",
    r"(\d+(?:\.\d+)?)\s*(hz|hertz)",
    r"(\d+(?:\.\d+)?)\s*(kb|mb|gb|tb|pb)",
    r"(\d+(?:\.\d+)?)\s*(w|watts)",
    r"(\d+(?:\.\d+)?)\s*(inch|inches|cm)",
    r"(\d+(?:\.\d+)?)\s*(db|decibels)",
]

# ---- NUMERIC VALUE → ASPECT REFINEMENT ----

UNIT_ASPECT_MAPPING = {
    "gb": "storage",
    "tb": "storage",
    "mb": "storage",

    "mah": "battery",

    "hz": "display",
    "ppi": "display",
    "px": "display",

    "inch": "display",
    "inches": "display",
    "cm": "display",

    "mp": "camera",
    "mm": "camera",

    "w": "power",
    "watts": "power"
}

# Processor Specific

TECH_NAMED_PATTERNS = [
    # Handheld
    r"(snapdragon\s?\d+)",
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
    r"(ddr\d+)"
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
}

# Dates

TECH_DATE_KEYWORDS = {
    "release_date": ["release", "released", "unveiled", "launched"],
    "update_date": ["update", "updated", "updates until"]
}