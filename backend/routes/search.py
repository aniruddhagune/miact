from fastapi import APIRouter
from backend.services.search_service import fetch_search_results
from backend.services.query_parser import parse_query

from backend.services.db_query_service import fetch_from_db
from backend.services.pipeline_service import process_query_url

router = APIRouter()


@router.get("/search")
def search(query: str):
    parsed = parse_query(query)

    # ---- STEP 1: CHECK DATABASE ----
    db_results = fetch_from_db(parsed)

    # ---- STEP 2: INTELLIGENT DB CHECK ----
    attribute = parsed.get("attribute")

    if attribute:
        if attribute in db_results["found_aspects"]:
            return {
                "source": "database",
                "parsed": parsed,
                "results": db_results["data"]
            }
    else:
        if db_results["data"]:
            return {
                "source": "database",
                "parsed": parsed,
                "results": db_results["data"]
            }

    # ---- STEP 3: FALLBACK TO SEARCH ----
    results = {}

    if parsed["mode"] == "news":
        results["news"] = fetch_search_results(query)

    else:
        entities = parsed.get("entities", [])
        attribute = parsed.get("attribute")
        filter_data = parsed.get("filter")

        if entities:
            for entity in entities:
                search_query = entity

                if attribute:
                    search_query += f" {attribute}"

                if filter_data:
                    search_query += f" {filter_data['value']}"

                search_results = fetch_search_results(search_query, num_results=5)

                extracted_results = []

                for r in search_results:
                    pipeline_results = process_query_url(parsed, r["url"])

                    if pipeline_results:
                        extracted_results.extend(pipeline_results)

                results[entity] = extracted_results

        else:
            search_query = ""

            if attribute:
                search_query += attribute + " "

            if filter_data:
                search_query += str(filter_data["value"]) + " "

            search_query = search_query.strip()

            search_results = fetch_search_results(search_query, num_results=5)

            extracted_results = []

            for r in search_results:
                pipeline_results = process_query_url(parsed, r["url"])

                if pipeline_results:
                    extracted_results.extend(pipeline_results)

            results["global"] = extracted_results

    return {
        "source": "web",
        "parsed": parsed,
        "results": results
    }