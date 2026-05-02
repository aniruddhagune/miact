from backend.nlp.relevance_engine import calculate_relevance_score

test_cases = [
    {
        "query": "OnePlus 9",
        "title": "OnePlus 9 Specs - GSM Arena",
    },
    {
        "query": "OnePlus 9",
        "title": "OnePlus 9 Pro Android Smartphone",
    },
    {
        "query": "OnePlus 9",
        "title": "OnePlus 8 vs OnePlus 9 Comparison",
    },
    {
        "query": "India Tax 2025",
        "title": "Taxation in India - Wikipedia",
    },
    {
        "query": "India Tax 2025",
        "title": "New India Income Tax Slabs for 2025-26",
    },
    {
        "query": "India Tax 2025",
        "title": "2024 Election Results India",
    }
]

for case in test_cases:
    score = calculate_relevance_score(case["query"], case["title"])
    print(f"Query: {case['query']}")
    print(f"Title: {case['title']}")
    print(f"Score: {score}")
    print("-" * 20)
