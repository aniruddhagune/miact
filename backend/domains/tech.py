# Aspect Detection
ASPECT_KEYWORDS = {
    "battery": ["battery", "battery life", "mah"],
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
}


NON_ASPECT_TERMS = [
    "smartphone", "phone", "mobile", "device",
    "max", "pro", "series",
    "version",
]

# to be removed soon
VALID_ASPECT_NOUNS = [
    "battery", "camera", "display", "screen",
    "processor", "chip", "performance",
    "speaker", "audio", "ram", "storage",
    "sensor", "design", "frame", "color", "sound"
]

# Numeric Extraction

TECH_NUMERIC_PATTERNS = [
    r"(\d+(\.\d+)?)\s*(mah)",
    r"(\d+(\.\d+)?)\s*(mp|megapixel|megapixels)",
    r"(\d+(\.\d+)?)\s*(mm)",
    r"(\d+(\.\d+)?)\s*(px|pixels|ppi)",
    r"(\d+(\.\d+)?)\s*(hz|hertz)",
    r"(\d+(\.\d+)?)\s*(kb|mb|gb|tb|pb)",
    r"(\d+(\.\d+)?)\s*(w|watts)",
    r"(\d+(\.\d+)?)\s*(inch|inches|cm)",
    r"(\d+(\.\d+)?)\s*(db|decibels)",
]


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

]

# Dates

TECH_DATE_KEYWORDS = {
    "release_date": ["release", "released", "unveiled", "launched"],
    "update_date": ["update", "updated", "updates until"]
}