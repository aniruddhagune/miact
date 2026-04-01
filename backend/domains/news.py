# Categories
TRUSTED_DOMAINS = [
    # See if can be scrapped reliably.
    "https://www.hindustantimes.com/",
    "https://www.ndtv.com/",
    "https://timesofindia.indiatimes.com/",
    "https://www.indiatoday.in/",
    "https://indianexpress.com/",
]

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