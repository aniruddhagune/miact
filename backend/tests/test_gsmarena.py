import json
from backend.services.query_parser import parse_query
from backend.services.search_service import fetch_search_results_async
from backend.services.pipeline_service import process_query_url
from backend.services.processing_service import group_variants_and_persist
import asyncio

async def test_gsm():
    print("Testing GSMArena extraction...")
    query = "oneplus 9"
    parsed = parse_query(query)
    url = "https://www.gsmarena.com/oneplus_9-10747.php"
    print(f"Scraping: {url}")
    
    extracted_results = []
    
    # Process
    pipeline_results = process_query_url(parsed, url)
    if pipeline_results:
        extracted_results.extend([x for x in pipeline_results if x.get("type", "") in ["table", "text"]])
        
    print(f"Extracted {len(extracted_results)} objective items.")
    
    # Check Opinions
    opinions = [x for x in pipeline_results if x.get("type", "") == "subjective"]
    print(f"Extracted {len(opinions)} opinions from GSMArena.")
    if opinions:
        print("\n--- SAMPLE OPINION ---")
        print(f"[{opinions[0]['aspect'].upper()}] ({opinions[0]['sentiment']}): {opinions[0]['text'][:100]}...")
    
    # Let's see the coverage:
    found_aspects = {x["aspect"] for x in extracted_results if x.get("type", "") == "table"}
    print(f"Found Table Aspects (Native coverage): {found_aspects}")
    
    # Group results
    results = {query: extracted_results}
    grouped = group_variants_and_persist(results)
    
    print("\n--- FINAL GROUPED RECORD ---")
    for r in grouped.get(query, []):
        print(f"[{r['aspect'].upper()}] : {r['value']}")

if __name__ == "__main__":
    asyncio.run(test_gsm())
