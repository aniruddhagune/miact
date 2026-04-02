# Regional Shortform Mapping

REGIONS = {
    "EU": "Europe",
    "NA": "North America",
    "USA": "United States",
    "UK": "United Kingdom",
    "IN": "India",
    "CN": "China",
    "JP": "Japan",
    "KR": "South Korea",
    "GLOBAL": "Global",
    "INTL": "International",
    "APAC": "Asia-Pacific",
    "MEA": "Middle East & Africa",
    "LATAM": "Latin America",
    "SEA": "Southeast Asia"
}

def resolve_region(shortform: str) -> str:
    sf = shortform.upper().strip()
    return REGIONS.get(sf, shortform)
