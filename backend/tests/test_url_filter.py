import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.services.url_filter import URLFilter

def test_url_classification():
    test_cases = [
        # ---- GSMArena Specs ----
        ("https://www.gsmarena.com/oneplus_9-10747.php",                     "fact"),
        ("https://www.gsmarena.com/apple_iphone_15-12559.php",               "fact"),
        ("https://www.gsmarena.com/samsung_galaxy_s24-12024.php",            "fact"),

        # ---- GSMArena Expert Reviews ----
        ("https://www.gsmarena.com/oneplus_9-review-2240.php",               "review"),
        ("https://www.gsmarena.com/oneplus_9-review-2240p2.php",             "review"),
        ("https://www.gsmarena.com/oneplus_9-review-2240p6.php",             "review"),

        # ---- GSMArena User Opinions ----
        ("https://www.gsmarena.com/oneplus_9-reviews-10747.php",             "review"),
        ("https://www.gsmarena.com/oneplus_9-reviews-10747p2.php",           "review"),

        # ---- GSMArena Review Comments ----
        ("https://www.gsmarena.com/reviewcomm-2240.php",                     "review"),
        ("https://www.gsmarena.com/reviewcomm-2240p2.php",                   "review"),

        # ---- Other Sources ----
        ("https://www.devicespecifications.com/en/model/499359e8",           "fact"),
        ("https://en.wikipedia.org/wiki/IPhone_15",                          "fact"),
        ("https://www.notebookcheck.net/Apple-M4-MacBook-Pro.Specs.0.html",  "fact"),

        ("https://www.theverge.com/phones/apple-iphone-15-review",           "review"),
        ("https://www.engadget.com/apple-iphone-15-pro-review-assessment",   "review"),
        ("https://www.androidcentral.com/phones/oneplus-9-review",           "review"),
        ("https://www.9to5google.com/2024/01/oneplus-9-verdict/",            "review"),
        ("https://www.techradar.com/news/iphone-15-hands-on",                "review"),
        ("https://www.digitaltrends.com/phone-reviews/oneplus-9-review/",    "review"),
        ("https://www.phonearena.com/reviews/oneplus-9-review_id5001",       "review"),

        # ---- Irrelevant ----
        ("https://www.gsmarena.com/res.php3?sSearchTerm=iphone",             "irrelevant"),
        ("https://www.gsmarena.com/search.php3",                             "irrelevant"),
        ("https://www.reddit.com/r/iphone/comments/12345/",                  "irrelevant"),
        ("https://www.facebook.com/apple/posts/12345",                       "irrelevant"),
        ("https://twitter.com/gsmarena_com/status/12345",                    "irrelevant"),
        ("https://forum.xda-developers.com/t/topic.12345/",                  "irrelevant"),
    ]

    print(f"\n{'URL':<75} | {'EXPECTED':<12} | {'RESULT':<12} | STATUS")
    print("-" * 120)

    passed = 0
    for url, expected in test_cases:
        result = URLFilter.classify_url(url)
        status = "✓ PASS" if result == expected else "✗ FAIL"
        if result == expected:
            passed += 1
        print(f"{url[:75]:<75} | {expected:<12} | {result:<12} | {status}")

    print("-" * 120)
    print(f"\nRESULTS: {passed}/{len(test_cases)} tests passed.\n")

    # Also test GSMArena-specific page type detection
    print("=== GSMArena Page Type Classification ===")
    gsma_cases = [
        ("https://www.gsmarena.com/oneplus_9-10747.php",           "specs"),
        ("https://www.gsmarena.com/oneplus_9-review-2240.php",     "review"),
        ("https://www.gsmarena.com/oneplus_9-review-2240p3.php",   "review"),
        ("https://www.gsmarena.com/oneplus_9-reviews-10747.php",   "user_opinions"),
        ("https://www.gsmarena.com/oneplus_9-reviews-10747p2.php", "user_opinions"),
        ("https://www.gsmarena.com/reviewcomm-2240.php",           "review_comments"),
        ("https://www.gsmarena.com/reviewcomm-2240p2.php",         "review_comments"),
    ]
    pg_passed = 0
    for url, expected in gsma_cases:
        result = URLFilter.classify_gsmarena_page_type(url)
        status = "✓ PASS" if result == expected else "✗ FAIL"
        if result == expected:
            pg_passed += 1
        print(f"  {url:<65} → {result:<16} {status}")
    print(f"\nPage type results: {pg_passed}/{len(gsma_cases)} passed.\n")


if __name__ == "__main__":
    test_url_classification()
