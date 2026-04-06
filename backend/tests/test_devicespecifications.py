import json
from backend.services.query_parser import parse_query
from backend.services.search_service import fetch_search_results_async
from backend.services.pipeline_service import process_query_url
from backend.services.processing_service import group_variants_and_persist
import asyncio

async def test_devicespecs():
    print("Testing DeviceSpecifications extraction...")
    query = "oneplus 9"
    parsed = parse_query(query)
    
    print("Fetching URL from duckduckgo...")
    # Add 'model specifications' to prioritize model pages
    search_query = f"{query} model specifications site:devicespecifications.com"
    search_results = await fetch_search_results_async(search_query, num_results=10)
    
    if not search_results:
        print("No results found from duckduckgo for devicespecifications!")
        return
        
    # Prioritize model pages
    model_results = [r for r in search_results if "/en/model/" in r["url"]]
    if not model_results:
        print("No specific model pages found in top 10 results. Fallback to first result.")
        url = search_results[0]["url"]
    else:
        url = model_results[0]["url"]
        
    print(f"Scraping: {url}")
    
    extracted_results = []
    
    # Process
    pipeline_results = process_query_url(parsed, url)
    if pipeline_results:
        extracted_results.extend([x for x in pipeline_results if x.get("type", "") in ["table", "text"]])
        
    print(f"Extracted {len(extracted_results)} objective items.")
    
    # Group results
    results = {query: extracted_results}
    grouped = group_variants_and_persist(results)
    
    print("\n--- FINAL GROUPED RECORD ---")
    for r in grouped.get(query, []):
        print(f"[{r['aspect'].upper()}] : {r['value']}")

if __name__ == "__main__":
    asyncio.run(test_devicespecs())
