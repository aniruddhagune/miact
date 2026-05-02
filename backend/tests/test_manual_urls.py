import sys
import os
sys.path.append('.')

from backend.utils.utils import get_manual_urls

def test():
    cases = [
        ("https://www.gsmarena.com/oneplus_9-10747.php", ["https://www.gsmarena.com/oneplus_9-10747.php"]),
        ("Check this: https://gsmarena.com/oneplus_9-10747.php, and https://wikipedia.org/wiki/OnePlus_9", ["https://gsmarena.com/oneplus_9-10747.php", "https://wikipedia.org/wiki/OnePlus_9"]),
        ("https://google.com  https://bing.com", ["https://google.com", "https://bing.com"]),
        ("No urls here", []),
        ("[https://sample.com/page]", ["https://sample.com/page"]),
        ("https://gsmarena.com/oneplus_9-reviews-10747.php.", ["https://gsmarena.com/oneplus_9-reviews-10747.php"]),
        ("Mixed text https://gsmarena.com/oneplus_9-10747.php oneplus 9 review", ["https://gsmarena.com/oneplus_9-10747.php"])
    ]

    print("\nMANUAL URL EXTRACTION TEST")
    print("="*80)
    for q, expected in cases:
        result = get_manual_urls(q)
        status = "PASS" if result == expected else "FAIL"
        print(f"Query: {q[:70]:<70} | Extracted: {len(result)} | {status}")
        if status == "FAIL":
            print(f"  Expected: {expected}")
            print(f"  Got:      {result}")
    print("="*80 + "\n")

if __name__ == "__main__":
    test()
