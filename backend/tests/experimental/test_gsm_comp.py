import sys, os
sys.path.append('.')
from backend.extractors.site_extractors.gsmarena import extract

urls = [
    "https://www.gsmarena.com/oneplus_9-10747.php",
    "https://www.gsmarena.com/oneplus_9-review-2240.php",
    "https://www.gsmarena.com/oneplus_9-reviews-10747.php",
    "https://www.gsmarena.com/reviewcomm-2240.php"
]

for url in urls:
    res = extract(url)
    if not res:
        print(f"FAIL: {url}")
        continue
    m = res.get('method')
    t = len(res.get('tables', []))
    o = len(res.get('opinions', []))
    txt = len(res.get('text', ""))
    print(f"OK | Method: {m:<25} | Tables: {t:<3} | Opins: {o:<3} | Text: {txt:<5} | URL: {url}")
