import sys
import os
sys.path.append('.')

from backend.nlp.relevance_engine import calculate_relevance_score
from backend.services.url_filter import URLFilter

def test():
    query = "OnePlus 9"
    cases = [
        ("OnePlus 9 - User opinions and reviews - page 23 - GSMArena.com", "https://www.gsmarena.com/oneplus_9-reviews-10747.php"),
        ("OnePlus9smartphonereview: Strong... - NotebookCheck.netReviews", "https://www.notebookcheck.net/OnePlus-9-Review.533261.0.html"),
        ("OnePlus9review: Serious business in a cheap suit", "https://www.theverge.com/22345524/oneplus-9-review"),
        ("OnePlus9Review: History Repeats Itself", "https://gadgets360.com/mobiles/reviews/oneplus-9-review-price-india-2396347"),
        ("gsmarena.com/oneplus_9-10747.php", "https://www.gsmarena.com/oneplus_9-10747.php")
    ]

    print("\nRELEVANCE & FILTER TEST")
    print("="*100)
    for title, url in cases:
        score, cat, trace = calculate_relevance_score(query, title, url)
        filter_cat = URLFilter.classify_url(url)
        is_valid = score >= 0.15 # My new threshold
        
        status = "PASS" if is_valid else "FAIL"
        print(f"URL: {url}")
        print(f"Title: {title}")
        print(f"Score: {score} | Category: {cat} | Filter: {filter_cat} | Status: {status}")
        print(f"Trace: {trace}")
        print("-" * 100)
    print("="*100 + "\n")

if __name__ == "__main__":
    test()
