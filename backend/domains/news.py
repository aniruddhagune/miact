# News Trusted Domains
TRUSTED_DOMAINS = [
    # International
    "bbc.com",
    "reuters.com",
    "apnews.com",
    "theguardian.com",
    "nytimes.com",
    "aljazeera.com",
    # India
    "hindustantimes.com",
    "ndtv.com",
    "timesofindia.indiatimes.com",
    "indiatoday.in",
    "indianexpress.com",
    "thehindu.com",
]


def get_trusted_domains(query_type: str = "news_generic") -> list:
    """Return news trusted domains (same list for all news subtypes)."""
    return TRUSTED_DOMAINS


NEWS_KEYWORDS = [
    "news", "latest", "update", "war", "election",
    "launch", "announcement", "report"
]

NEWS_CATEGORIES = {
    "casualties": [
        "killed", "dead", "died", "injured", "wounded", "missing"
    ],
    "accident": [
        "crash", "collision", "explosion", "fire", "accident"
    ],
    "events": [
        "meeting", "summit", "election", "festival", "ceremony"
    ],
    "price_change": [
        "price", "cost", "increase", "decrease", "inflation", "rate"
    ]
}

# Numeric

NEWS_NUMERIC_KEYWORDS = [
    "people", "persons", "victims",
    "killed", "injured", "dead",
    "percent", "%"
]


# -------------------------------
# DATE CONTEXT
# -------------------------------

NEWS_DATE_KEYWORDS = {
    "event_date": ["on", "during", "at"],
    "report_date": ["reported", "announced"],
    "effective": ["effective"]
}


# -------------------------------
# LOCATION KEYWORDS (light hinting)
# -------------------------------

NEWS_LOCATION_HINTS = [
    "in", "at", "near", "from"
]