# MIACT Unified Configuration
# This file centralizes the categorization logic for both Backend (NLP) and Frontend (UI).

TECH_GROUPS = {
    "Dates": ["announced", "status", "released", "release_date", "announcement_date"],
    "Core": ["os", "chipset", "cpu", "gpu", "platform", "system on chip", "processor", "graphics"],
    "Memory": ["card slot", "internal", "ram", "memory", "storage"],
    "Connectivity": ["wlan", "bluetooth", "positioning", "nfc", "radio", "usb", "connectivity", "wi-fi", "wifi"],
    "Display": ["type", "size", "resolution", "protection", "refresh rate", "screen", "display", "nits"]
}

GENERAL_GROUPS = {
    "Personal Info": ["born", "died", "birth", "death", "spouse", "children", "nationality", "age"],
    "Background": ["education", "alma mater", "religion", "residence", "parents"],
    "Professional": ["career", "known for", "office", "political party", "occupation", "role", "years active"],
    "Legal Info": ["enacted by", "date enacted", "date effective", "citation", "territorial extent", "status", "jurisdiction"],
    "Works": ["books", "writings", "notable works", "publications", "awards", "achievements"]
}

NEWS_GROUPS = {
    "AI News Highlights": ["ai highlights", "summary", "brief summary", "updates", "news category", "event cause", "people involved", "places affected"],
    "Regional News": ["india", "usa", "global", "local"],
    "News Metadata": ["published", "author", "source_type"]
}

def get_unified_config():
    return {
        "tech": TECH_GROUPS,
        "general": GENERAL_GROUPS,
        "news": NEWS_GROUPS
    }
