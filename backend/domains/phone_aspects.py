ASPECT_KEYWORDS = {
    "battery": ["battery", "battery life", "mah"],
    "camera": ["camera", "cameras", "lens", "mp"],
    "display": ["display", "screen", "resolution", "pixel", "ppi", "px", "OLED", "AMOLED", "LCD"],
    "processor": ["processor", "chip", "cpu", "chipset"],
    "design": ["design", "build", "body"],
    "price": ["price", "cost"],
    "biometric": ["fingerprint", "scanner", "face", "facial"],
    "certification": ["IP"],
    "speakers": ["speaker", "speakers", "db", "decibel", "decibels"]
}

ASPECT_MAPPING = {
    "cancellation": "audio",
    "speaker": "audio",
    "sensor": "camera",
    "fingerprint": "biometric",
}

NON_ASPECT_TERMS = [
    "pro",
    "series",
    "version",
    "smartphone",
    "phone",
    "mobile",
    "device"
]

VALID_ASPECT_NOUNS = [
    "battery", "camera", "display", "screen",
    "processor", "chip", "performance",
    "speaker", "audio", "ram", "storage",
    "sensor", "design", "frame", "color", "sound"
]