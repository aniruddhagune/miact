import re
from urllib.parse import urlparse

class URLFilter:
    """
    Classifies URLs before scraping to optimize which pages are fetched.
    Categories: 'fact', 'review', 'irrelevant', 'general'
    """

    TRUSTED_REVIEW_DOMAINS = {
        "theverge.com", "engadget.com", "techradar.com", "tomsguide.com",
        "zdnet.com", "notebookcheck.net", "androidcentral.com", "9to5google.com",
        "9to5mac.com", "pocket-lint.com", "digitaltrends.com", "gizmodo.com",
        "slashgear.com", "phonearena.com", "gsmarena.com", "rtings.com",
        "laptopmag.com", "xda-developers.com"
    }

    BLACKLIST_PATTERNS = [
        r"reddit\.com", r"facebook\.com", r"twitter\.com", r"instagram\.com",
        r"tiktok\.com", r"youtube\.com/watch\?v=", r"/search[\?#]",
        r"gsmarena\.com/res\.php", r"gsmarena\.com/search\.php",
        r"/login", r"/signup", r"/register", r"/account", r"/profile",
        r"forum\.", r"forums\.", r"/tags/", r"/tag/", r"\.pdf$"
    ]

    @staticmethod
    def classify_url(url: str) -> str:
        u_lower = url.lower()
        
        # 1. Blacklist
        for pattern in URLFilter.BLACKLIST_PATTERNS:
            if re.search(pattern, u_lower):
                return "irrelevant"

        # 2. GSMArena Special Handling (Most Important)
        if "gsmarena.com" in u_lower:
            # Order matters: check more specific review patterns first
            if "reviewcomm-" in u_lower:
                return "review"
            if "-reviews-" in u_lower:
                return "review" # User opinions
            if "-review-" in u_lower:
                return "review" # Expert review
            if re.search(r"-\d+\.php", u_lower):
                return "fact"
            return "general"

        # 3. Other High-Confidence Facts
        if "devicespecifications.com" in u_lower and "/model/" in u_lower:
            return "fact"
        if "wikipedia.org/wiki/" in u_lower:
            return "fact"
        if "notebookcheck.net" in u_lower and "-specs" in u_lower:
            return "fact"

        # 4. Keyword-based Reviews
        review_keywords = ["/review/", "/reviews/", "verdict", "hands-on", "pro-con"]
        if any(k in u_lower for k in review_keywords):
            return "review"

        # 5. Trusted Review Domains Fallback
        try:
            domain = urlparse(url).netloc.lower().replace("www.", "")
            if domain in URLFilter.TRUSTED_REVIEW_DOMAINS:
                return "review"
        except:
            pass

        return "general"

    @staticmethod
    def is_worth_scraping(url: str, category_needed: str = None) -> bool:
        category = URLFilter.classify_url(url)
        if category == "irrelevant":
            return False
        if category_needed and category != category_needed:
            return False
        return True

    @staticmethod
    def classify_gsmarena_page_type(url: str) -> str:
        u_lower = url.lower()
        if "reviewcomm-" in u_lower:
            return "review_comments"
        if "-reviews-" in u_lower:
            return "user_opinions"
        if "-review-" in u_lower:
            return "review"
        if re.search(r"-\d+\.php", u_lower):
            return "specs"
        return "other"
