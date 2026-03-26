# Categories

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