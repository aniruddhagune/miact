# HTML requests get blocked, using DDG Search service.

from ddgs import DDGS

def fetch_search_results(query: str, num_results: int = 10):
    results = []

    with DDGS() as ddgs:
        for r in ddgs.text(query, max_results=num_results):
            results.append({
                "title": r.get("title"),
                "url": r.get("href"),
                "snippet": r.get("body"),
                "source": r.get("href").split("/")[2]
            })

    return results