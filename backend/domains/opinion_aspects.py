# Opinion-to-Aspect Mapping
# Maps raw extracted aspect words to canonical display aspects

OPINION_ASPECT_MAP = {
    "camera": [
        "camera", "cameras", "photography", "photo", "photos", "portrait",
        "portraits", "pictures", "picture", "low light", "night mode", "night shot",
        "selfie", "selfies", "image", "images", "shot", "shots", "zoom", "lens",
        "bokeh", "ultrawide", "telephoto", "macro", "35mm", "aperture", "f/",
        "hasselblad", "optical", "pdaf", "ois", "stabilization"
    ],
    "display": [
        "display", "screen", "brightness", "refresh rate", "amoled", "oled",
        "resolution", "colors", "colour", "color", "nits", "hdr", "hdr10",
        "dolby vision", "vibrance", "vivid", "saturation", "panel", "ltpo",
        "fluid", "adaptive", "peak brightness"
    ],
    "performance": [
        "performance", "speed", "fast", "faster", "slow", "benchmark", "snapdragon",
        "processor", "cpu", "gaming", "lag", "smooth", "smoother", "gen",
        "gen 2", "gen 3", "throughput", "multitasking", "heat", "thermal",
        "throttle", "antutu", "geekbench"
    ],
    "battery": [
        "battery", "endurance", "drain", "standby", "life", "runtime", "overnight"
    ],
    "charging": [
        "charging", "wired", "wireless", "warp", "vooc", "supervooc", "fast charge",
        "quick charge", "pd", "power delivery", "charge time", "charger"
    ],
    "software": [
        "software", "ui", "ux", "interface", "android", "oxygen", "oxygenos",
        "coloros", "one ui", "miui", "update", "updates", "bloatware",
        "skin", "clean", "minimal", "smooth ui", "bugs", "glitch"
    ],
    "build": [
        "build", "design", "construction", "feel", "texture", "material",
        "glass", "aluminum", "metal", "weight", "size", "compact", "premium",
        "grip", "finish", "matte", "glossy", "curvy", "flat", "dimensions",
        "ip rating", "ip64", "ip68"
    ],
    "audio": [
        "speakers", "speaker", "audio", "sound", "lufs", "stereo", "mono",
        "earpiece", "volume", "bass", "treble", "clarity", "dolby atmos", "hi-res"
    ],
    "value": [
        "price", "value", "worth", "money", "cost", "flagship", "budget",
        "bang for", "affordable", "expensive", "overpriced", "cheap", "deal"
    ],
    "connectivity": [
        "bluetooth", "wifi", "wi-fi", "5g", "4g", "lte", "nfc", "connection",
        "signal", "network", "reception", "hotspot"
    ],
    "storage": [
        "storage", "internal storage", "ufs", "capacity", "space", "gb",
        "tb", "file", "data", "microsd", "sd card"
    ],
    "graphics": [
        "gpu", "graphics", "adreno", "mali", "rendering", "gaming performance",
        "frame rate", "fps", "ray tracing", "visual", "texture detail"
    ],
    "overall": [
        "phone", "device", "smartphone", "oneplus", "samsung", "apple", "pixel",
        "overall", "recommend", "worth it", "buying", "buy", "flagship",
        "all round", "complete package", "winner"
    ],
}

# Flat reverse map: keyword -> canonical aspect
_FLAT_MAP = {}
for canonical, keywords in OPINION_ASPECT_MAP.items():
    for kw in keywords:
        _FLAT_MAP[kw.lower()] = canonical


def map_to_canonical_aspect(aspect_text: str) -> str | None:
    """
    Given a raw aspect label (e.g. 'portrait', 'speed', 'charging'),
    returns the canonical aspect name (e.g. 'camera', 'performance', 'charging').
    Returns None if no mapping found.
    """
    text_lower = aspect_text.lower().strip()
    # Exact match first
    if text_lower in _FLAT_MAP:
        return _FLAT_MAP[text_lower]
    # Partial containment — find longest keyword match
    best = None
    best_len = 0
    for kw, canonical in _FLAT_MAP.items():
        if kw in text_lower and len(kw) > best_len:
            best = canonical
            best_len = len(kw)
    return best
