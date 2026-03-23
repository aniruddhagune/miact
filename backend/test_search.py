from services.search_service import fetch_search_results

query = "iphone 15 battery"

results = fetch_search_results(query)

for r in results:
    print(r)