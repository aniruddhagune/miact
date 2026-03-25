ASPECT_KEYWORDS = {
    "battery": ["battery", "battery life", "mah"],
    "camera": ["camera", "cameras", "lens", "mp"],
    "display": ["display", "screen"],
    "performance": ["performance", "processor", "chip"],
    "design": ["design", "build", "body"],
    "price": ["price", "cost"],
    "biometric": ["fingerprint", "scanner", "face", "facial"],
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
    "device"
]