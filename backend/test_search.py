from services.search_service import fetch_search_results

results = fetch_search_results("OnePlus 9 specs", 5)

for r in results:
    print(r["title"])
    print(r["url"])
    print("----")