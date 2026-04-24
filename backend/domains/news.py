# News Categorized Domains
NEWS_GENERIC_DOMAINS = [
    "bbc.com", "reuters.com", "apnews.com", "theguardian.com", 
    "thehindu.com", "indianexpress.com", "aljazeera.com"
]

NEWS_FINANCIAL_DOMAINS = [
    "economictimes.indiatimes.com", "moneycontrol.com", "livemint.com", 
    "wsj.com", "bloomberg.com", "reuters.com", "businesstoday.in"
]

NEWS_BREAKING_DOMAINS = [
    "ndtv.com", "hindustantimes.com", "timesofindia.indiatimes.com", 
    "indiatoday.in", "firstpost.com", "news18.com"
]

def get_trusted_domains(query_type: str = "news_generic") -> list:
    """Return news trusted domains based on the detected news sub-type."""
    if query_type == "news_change":
        return NEWS_FINANCIAL_DOMAINS
    elif query_type == "news_accident":
        return NEWS_BREAKING_DOMAINS
    
    # Default to generic/high-authority news
    return NEWS_GENERIC_DOMAINS


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