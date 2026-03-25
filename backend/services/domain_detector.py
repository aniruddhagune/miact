def detect_domain(query: str):
    query_lower = query.lower()

    phone_keywords = [
        "iphone",
        "samsung",
        "oneplus",
        "xiaomi",
        "huawei",
        "phone",
        
        "battery", "camera", "display"
    ]

    if any(word in query_lower for word in phone_keywords):
        return "phone"

    return "generic"