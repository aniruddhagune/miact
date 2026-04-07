import sys
import os
import json

# Ensure backend is in the path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.extractors.site_extractors.gsmarena import extract

def test_extractor():
    urls = [
        "https://www.gsmarena.com/oneplus_9-10747.php",          # Specs
        "https://www.gsmarena.com/oneplus_9-review-2240.php",     # Review
        "https://www.gsmarena.com/oneplus_9-reviews-10747.php",   # User Opinions
        "https://www.gsmarena.com/reviewcomm-2240.php"            # Review Comments
    ]

    print("\n" + "="*80)
    print("GSMARENA EXTRACTOR TEST")
    print("="*80 + "\n")

    for url in urls:
        print(f"Testing URL: {url}")
        result = extract(url)
        
        if not result:
            print(f"  [ERROR] Extraction failed for {url}\n")
            continue
            
        print(f"  Title: {result.get('title')}")
        print(f"  Method Used: {result.get('method')}")
        
        # Tables
        tables = result.get('tables', [])
        print(f"  Tables Found: {len(tables)} rows")
        
        # Opinions
        opinions = result.get('opinions', [])
        print(f"  Opinions Found: {len(opinions)}")
        
        # Text
        text = result.get('text', "")
        print(f"  Text Content: {len(text)} characters")
        if text:
            print(f"  Text Preview: {text[:150]}...")
            
        print("-" * 40 + "\n")

if __name__ == "__main__":
    test_extractor()
