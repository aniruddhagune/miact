from backend.services.search_service import score_match

test_cases = [
    {
        "query": "OnePlus 9",
        "title": "OnePlus 9 review",
        "url": "https://www.theverge.com/22345094/oneplus-9-review",
        "snippet": "The OnePlus 9 is a great phone..."
    },
    {
        "query": "OnePlus 9",
        "title": "OnePlus 9 Pro specs",
        "url": "https://www.gsmarena.com/oneplus_9_pro-10806.php",
        "snippet": "OnePlus 9 Pro Android smartphone."
    },
    {
        "query": "OnePlus 9",
        "title": "OnePlus 9 vs OnePlus 9 Pro comparison",
        "url": "https://www.tomsguide.com/face-off/oneplus-9-vs-oneplus-9-pro",
        "snippet": "OnePlus 9 vs OnePlus 9 Pro: Which should you buy?"
    },
    {
        "query": "OnePlus 13",
        "title": "OnePlus 13 - Full phone specifications - GSMArena.com",
        "url": "https://www.gsmarena.com/oneplus_13-10000.php",
        "snippet": "OnePlus 13 Specifications"
    }
]

for case in test_cases:
    valid, score = score_match(case["query"], case["title"], case["url"], case["snippet"])
    print(f"Query: {case['query']}")
    print(f"Title: {case['title']}")
    print(f"Score: {score}")
    print(f"Valid: {valid}")
    print("-" * 20)
