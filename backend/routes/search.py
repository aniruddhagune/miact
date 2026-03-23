from fastapi import APIRouter
from backend.services.search_service import fetch_search_results
from backend.services.query_parser import parse_query

router = APIRouter()


@router.get("/search")
def search(query: str):
    parsed = parse_query(query)

    results = {}

    # ---- NEWS MODE ----
    if parsed["mode"] == "news":
        results["news"] = fetch_search_results(query)

    # ---- PRODUCT MODE ----
    else:
        for entity in parsed["entities"]:
            search_query = entity

            if parsed.get("attribute"):
                search_query += f" {parsed['attribute']}"

            results[entity] = fetch_search_results(search_query)

    return {
        "parsed": parsed,
        "results": results
    }