"""
Diagnostic tool to test Query-to-URL selection, categorization, and scoring precision.
Tests iPhone 13 variants and OnePlus specs vs comparison logic.
"""
import sys
import os
import re

# Add project root to path
sys.path.append(os.getcwd())

from backend.services.search_service import _do_ddg_sync

TEST_QUERIES = [
    "iPhone 13",
    "OnePlus 9",
    "OnePlus 13"
]

def run_diagnostic(query: str):
    print(f"\n" + "="*80)
    print(f" DIAGNOSTIC: Query = '{query}'")
    print("="*80)
    
    # Perform Search - using sync version for test
    results = _do_ddg_sync(query, 10)
    
    if not results:
        print("❌ No results found or all filtered out.")
        return

    print(f"{'Score':<6} | {'Category':<12} | {'Title':<45} | {'URL'}")
    print("-" * 140)
    
    for r in results:
        score = r.get("score", 0)
        category = r.get("category", "unknown")
        title = r.get("title", "")[:42] + "..." if len(r.get("title", "")) > 45 else r.get("title", "")
        url = r.get("url", "")
        
        print(f"{score:<6} | {category:<12} | {title:<45} | {url}")
        
        # Decisions Trace
        trace = r.get("trace", [])
        if trace:
            print("       REFINEMENT TRACE:")
            for step in trace:
                print(f"        - {step}")
        print("-" * 140)

if __name__ == "__main__":
    for q in TEST_QUERIES:
        run_diagnostic(q)
    
    print("\n✅ Diagnostic Complete.")
