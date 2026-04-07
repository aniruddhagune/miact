import re
from urllib.parse import urlparse


class URLFilter:
    """
    Classifies URLs before scraping to optimize which pages are fetched.

    Categories:
      - 'fact'        : High-confidence specification pages (GSMArena product, Wikipedia, DeviceSpecs)
      - 'review'      : Expert or user review/opinion pages
      - 'irrelevant'  : Noise — social media, login pages, search result pages
      - 'general'     : Everything else (still scraped, but lower priority)
    """

    # ---- FACT PATTERNS ----
    # Match only PRODUCT pages, not listing/search/news pages.
    FACT_PATTERNS = [
        # GSMArena product specs:  oneplus_9-10747.php
        # Exclude: -review-NNNN, -reviews-NNNN, reviewcomm-NNNN
        r"gsmarena\.com/(?!reviewcomm)[^/]+(?<!-review)-(?<!-reviews-)(\d+)\.php(?:\?.*)?$",
        # DeviceSpecifications model pages
        r"devicespecifications\.com/.+/model/",
        # Wikipedia device articles
        r"wikipedia\.org/wiki/.+",
        # Notebookcheck product specs
        r"notebookcheck\.net/[^/]+-Specs\.[\w]+\.0\.html",
    ]

    # ---- REVIEW/OPINION PATTERNS ----
    # Keyword patterns anywhere in the URL path
    REVIEW_PATH_PATTERNS = [
        r"-review-\d+",          # GSMArena expert review: -review-2240.php
        r"-reviews-\d+",         # GSMArena user opinions: -reviews-10747.php
        r"reviewcomm-\d+",       # GSMArena review comments
        r"/reviews?/",           # Generic /review/ or /reviews/ path segment
        r"hands-on",
        r"verdict",
        r"assessment",
        r"in-depth",
        r"first-look",
    ]

    # ---- TRUSTED REVIEW DOMAINS ----
    # Any URL from these domains is treated as 'review' even without path keywords
    REVIEW_DOMAINS = [
        "theverge.com",
        "engadget.com",
        "techradar.com",
        "tomsguide.com",
        "zdnet.com",
        "notebookcheck.net",
        "androidcentral.com",
        "9to5google.com",
        "9to5mac.com",
        "pocket-lint.com",
        "digitaltrends.com",
        "gizmodo.com",
        "slashgear.com",
        "phonearena.com",
        "gsmarena.com",   # gsmarena pages not matched by FACT are review/opinion
        "rtings.com",
        "laptopmag.com",
        "xda-developers.com",
    ]

    # ---- BLACKLIST ----
    # These are skipped entirely regardless of domain or path.
    BLACKLIST = [
        r"reddit\.com",
        r"facebook\.com",
        r"twitter\.com",
        r"instagram\.com",
        r"tiktok\.com",
        r"youtube\.com/watch\?v=",      # video pages
        r"/search[\?#]",                # search result pages
        r"gsmarena\.com/res\.php",      # gsmarena search
        r"gsmarena\.com/search\.php",
        r"/login(?:\.php)?",
        r"/signup(?:\.php)?",
        r"/register(?:\.php)?",
        r"/account(?:\.php)?",
        r"/profile(?:\.php)?",
        r"forum\.",
        r"forums\.",
        r"/tags/",
        r"/tag/",
        r"\.pdf$",
    ]

    @staticmethod
    def classify_url(url: str) -> str:
        url_lower = url.lower()

        # 1. Blacklist (immediate reject)
        for pattern in URLFilter.BLACKLIST:
            if re.search(pattern, url_lower):
                return "irrelevant"

        # 2. Fact patterns
        for pattern in URLFilter.FACT_PATTERNS:
            if re.search(pattern, url_lower):
                return "fact"

        # 3. Review path keywords
        for pattern in URLFilter.REVIEW_PATH_PATTERNS:
            if re.search(pattern, url_lower):
                return "review"

        # 4. Trusted review domains fallback
        domain = urlparse(url).netloc.lower().lstrip("www.")
        if any(d in domain for d in URLFilter.REVIEW_DOMAINS):
            return "review"

        return "general"

    @staticmethod
    def is_worth_scraping(url: str, category_needed: str = None) -> bool:
        """
        Returns True if the URL should be scraped.

        If category_needed is specified (e.g. 'fact'), only return True for that category.
        'irrelevant' URLs always return False.
        """
        category = URLFilter.classify_url(url)
        if category == "irrelevant":
            return False
        if category_needed and category != category_needed:
            return False
        return True

    @staticmethod
    def classify_gsmarena_page_type(url: str) -> str:
        """
        Specifically classify which GSMArena page type a URL represents.
        Returns: 'specs', 'review', 'user_opinions', 'review_comments', or 'other'
        """
        path = urlparse(url).path.lower()
        if re.search(r"reviewcomm-\d+", path):
            return "review_comments"
        if re.search(r"-reviews-\d+", path):
            return "user_opinions"
        if re.search(r"-review-\d+", path):
            return "review"
        if re.search(r"-\d+\.php$", path):
            return "specs"
        return "other"
