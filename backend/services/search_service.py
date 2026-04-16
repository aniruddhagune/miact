import asyncio
from ddgs import DDGS
import re
from backend.utils.logger import logger

def is_valid_match(query: str, title: str):
    entity_lower = query.lower()
    title_lower = title.lower()

    modifiers = ["pro", "plus", "max", "ultra", "mini"]
    for mod in modifiers:
        if mod not in entity_lower and re.search(rf"\b{mod}\b", title_lower):
            return False
    return True

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
    logger.debug("SEARCH", f"Executing DDG sync for: '{query}'")
    results = []
    try:
        # Use DDGS with regional settings (India - English)
        with DDGS() as ddgs:
            raw_results = list(ddgs.text(query, region='in-en', max_results=num_results))
            logger.debug("SEARCH", f"Raw search results received: {len(raw_results)}")
            for r in raw_results:
                title = r.get("title", "")
                url = r.get("href", "")
                snippet = r.get("body", "")

                # Language Guard: Force English Wikipedia
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
                    logger.debug("SEARCH", f"Filtered out irrelevant result: {title}", data={"url": url, "trace": trace})
    except Exception as e:
        logger.error("SEARCH", f"DuckDuckGo search error: {e}")
    return results

async def execute_ddg(query: str, num_results: int):
    return await asyncio.to_thread(_do_ddg_sync, query, num_results)

async def fetch_search_results_async(query: str, num_results: int = 10, trusted_domains: list = None):
    logger.info("SEARCH", f"Fetching results for: '{query}'", data={"num_results": num_results, "trusted": trusted_domains})
    results = []
    if trusted_domains:
        site_query = " OR ".join([f"site:{d}" for d in trusted_domains])
        full_query = f"{query} {site_query}".strip()
        
        # Execute Trusted Domain search
        trusted_results = await execute_ddg(full_query, num_results)
        for p in trusted_results:
            results.append(p)
            
        # Fallback query if insufficient
        if len(results) < 2:
            logger.debug("SEARCH", "Insufficient results from trusted domains. Running broad fallback.")
            fallback_results = await execute_ddg(query, num_results - len(results))
            for f in fallback_results:
                if not any(x["url"] == f["url"] for x in results):
                    results.append(f)
    else:
        results = await execute_ddg(query, num_results)

    logger.info("SEARCH", f"Total relevant results found: {len(results)}")
    return results
