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
        r"forum\.", r"forums\.", r"/tags/", r"/tag/", r"\.pdf$",
        r"pinterest\.com", r"linkedin\.com", r"quora\.com",
        r"amazon\..*/s\?", r"flipkart\.com/search\?", r"ebay\.com/sch/",
        r"\.xml$", r"\.json$", r"\.rss$",
        # Language Guards: Block common non-English subdomains
        r"^(?:https?://)?(?:hi|fr|es|de|it|pt|ru|zh|ja|ko|ar|bn|mr|te|ta|ml|kn)\."
    ]

    @staticmethod
    def normalize_url(url: str) -> str:
        """
        Strips tracking parameters, fragments, and normalizes subdomains.
        E.g. "https://m.gsmarena.com/apple_iphone_15-12559.php?utm_source=foo#comments"
        -> "https://www.gsmarena.com/apple_iphone_15-12559.php"
        """
        try:
            parsed = urlparse(url)
            # 1. Normalize Host (remove mobile subdomains)
            host = parsed.netloc.lower()
            if host.startswith("m."):
                host = host[2:]
            if not host.startswith("www.") and host.count('.') == 1: # e.g. gsmarena.com -> www.gsmarena.com
                # Optional: standardize to www for consistency
                # but keep it simple: just ensured it's not 'm.'
                pass
            
            # 2. Reconstruct without parameters or fragments
            clean_url = f"{parsed.scheme}://{host}{parsed.path}"
            
            # 3. Remove trailing slash
            if clean_url.endswith("/") and len(parsed.path) > 1:
                clean_url = clean_url[:-1]
                
            return clean_url
        except:
            return url

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
        """
        Check if a URL is worth scraping.
        Note: We check the blacklist against the RAW url to catch parameter-based noise.
        """
        u_lower = url.lower()
        for pattern in URLFilter.BLACKLIST_PATTERNS:
            if re.search(pattern, u_lower):
                return False
        
        category = URLFilter.classify_url(url)
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
