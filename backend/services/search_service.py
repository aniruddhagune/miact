import asyncio
from ddgs import DDGS

import re

def is_valid_match(query: str, title: str):
    entity_lower = query.lower()
    title_lower = title.lower()

    modifiers = ["pro", "plus", "max", "ultra", "mini"]
    for mod in modifiers:
        if mod not in entity_lower and re.search(rf"\b{mod}\b", title_lower):
            return False
def score_match(query: str, title: str, url: str = "", snippet: str = "") -> tuple[bool, int, str, list[str]]:
    """
    Score a search result match for relevance using the new spaCy engine.
    Returns (is_valid, score, category, trace).
    """
    from backend.nlp.relevance_engine import calculate_relevance_score
    from backend.domains.tech import TRUSTED_DOMAINS_PHONE

    relevance_01, category, trace = calculate_relevance_score(query, title, url)
    
    # Convert 0.0-1.0 score to 0-20 scale for search sorting
    score = int(relevance_01 * 20)
    
    # 1. Filter Threshold
    if relevance_01 < 0.35:
        # Check snippet as fallback overlap
        snippet_keywords = set(re.sub(r'[^a-z0-9 ]', '', snippet.lower()).split())
        query_keywords = set(re.sub(r'[^a-z0-9 ]', '', query.lower()).split())
        if not (query_keywords & snippet_keywords):
            trace.append("Filter Triggered: Score < 0.35 and no snippet overlap.")
            return False, 0, category, trace

    # 2. Domain Trust Bonus
    u_norm = url.split("/")[2] if "://" in url else url
    if any(d in u_norm for d in TRUSTED_DOMAINS_PHONE):
        score += 5
        trace.append("Bonus +5: Trusted Tech Domain.")
        
    return True, score, category, trace

def _do_ddg_sync(query: str, num_results: int):
    results = []
    try:
        # Use DDGS with regional settings (India - English)
        # kl='in-en' for India/English. Can be customized.
        with DDGS() as ddgs:
            raw_results = list(ddgs.text(query, region='in-en', max_results=num_results))
            print(f"[DEBUG] Raw search results for '{query}': {len(raw_results)}")
            for r in raw_results:
                title = r.get("title", "")
                url = r.get("href", "")
                snippet = r.get("body", "")

                # Language Guard: Force English Wikipedia to avoid foreign language results
                if "wikipedia.org" in url and not url.startswith("https://en.wikipedia.org"):
                    continue

                is_valid, score, category, trace = score_match(query, title, url, snippet)
                if is_valid:
                    results.append({
                        "title": title,
                        "url": url,
                        "snippet": snippet,
                        "source": url.split("/")[2] if "://" in url else "",
                        "score": score,
                        "category": category,
                        "trace": trace
                    })
                else:
                    print(f"[DEBUG] Filtered out title: {title}")
    except Exception as e:
        print(f"[SEARCH ERROR] {e}")
    return results

async def execute_ddg(query: str, num_results: int):
    return await asyncio.to_thread(_do_ddg_sync, query, num_results)

async def fetch_search_results_async(query: str, num_results: int = 10, trusted_domains: list = None):
    results = []
    if trusted_domains:
        site_query = " OR ".join([f"site:{d}" for d in trusted_domains])
        full_query = f"{query} {site_query}".strip()
        
        # Execute Trusted Domain search
        trusted_results = await execute_ddg(full_query, num_results)
        for p in trusted_results:
            results.append(p)
            
        # Fallback query if insufficient
        if len(trusted_results) < 2:
            # We execute fallback without site constraints
            fallback_results = await execute_ddg(query, num_results - len(trusted_results))
            for f in fallback_results:
                if not any(x["url"] == f["url"] for x in results):
                    results.append(f)
    else:
        results = await execute_ddg(query, num_results)

    return results