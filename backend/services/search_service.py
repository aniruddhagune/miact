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
    return True

def _do_ddg_sync(query: str, num_results: int):
    results = []
    try:
        with DDGS() as ddgs:
            raw_results = list(ddgs.text(query, max_results=num_results))
            print(f"[DEBUG] Raw search results for '{query}': {len(raw_results)}")
            for r in raw_results:
                title = r.get("title", "")
                if is_valid_match(query, title):
                    results.append({
                        "title": title,
                        "url": r.get("href"),
                        "snippet": r.get("body"),
                        "source": r.get("href").split("/")[2] if "://" in r.get("href") else ""
                    })
                else:
                    print(f"[DEBUG] Filtered out title: {title}")
    except:
        pass
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