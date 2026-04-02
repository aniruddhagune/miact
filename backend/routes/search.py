from fastapi import APIRouter
from fastapi.responses import StreamingResponse
import json
from backend.services.search_service import fetch_search_results
from backend.services.query_parser import parse_query

from backend.services.db_query_service import fetch_from_db
from backend.services.pipeline_service import process_query_url

router = APIRouter()

@router.get("/search")
async def search(query: str):
    parsed = parse_query(query)

    async def event_generator():
        yield f"data: {json.dumps({'step': 'parsed', 'parsed': parsed})}\n\n"

        # ---- STEP 1: CHECK DATABASE ----
        db_results = fetch_from_db(parsed)

        # ---- STEP 2: INTELLIGENT DB CHECK ----
        attribute = parsed.get("attribute")

        use_db = False
        if attribute:
            if attribute in db_results["found_aspects"]:
                use_db = True
        else:
            if db_results["data"]:
                use_db = True

        if use_db:
            final_resp = {
                "step": "result",
                "source": "database",
                "parsed": parsed,
                "results": db_results["data"]
            }
            yield f"data: {json.dumps(final_resp)}\n\n"
            return

        # ---- STEP 3: FALLBACK TO SEARCH ----
        results = {}
        urls_dict = {}

        if parsed["mode"] == "news":
            news_results = fetch_search_results(query)
            urls_dict["news"] = {"query": query, "urls": [r["url"] for r in news_results]}
            yield f"data: {json.dumps({'step': 'urls_extracted', 'urls': urls_dict})}\n\n"
            results["news"] = news_results
            yield f"data: {json.dumps({'step': 'result', 'source': 'web', 'parsed': parsed, 'results': results, 'urls': urls_dict})}\n\n"
            return

        entities = parsed.get("entities", [])
        filter_data = parsed.get("filter")

        if entities:
            for entity in entities:
                search_query = entity

                if attribute:
                    search_query += f" {attribute}"

                if filter_data:
                    search_query += f" {filter_data['value']}"

                search_results = fetch_search_results(search_query, num_results=5)
                urls_list = [r["url"] for r in search_results]
                urls_dict[entity] = {"query": search_query, "urls": urls_list}
                
                yield f"data: {json.dumps({'step': 'urls_extracted', 'urls': urls_dict})}\n\n"

                extracted_results = []
                for r in search_results:
                    try:
                        pipeline_results = process_query_url(parsed, r["url"])
                    except Exception as e:
                        print(f"Error processing URL {r['url']}: {e}")
                        pipeline_results = None

                    if pipeline_results:
                        extracted_results.extend(pipeline_results)
                        yield f"data: {json.dumps({'step': 'partial', 'entity': entity, 'url': r['url']})}\n\n"

                results[entity] = extracted_results

        else:
            search_query = ""

            if attribute:
                search_query += attribute + " "

            if filter_data:
                search_query += str(filter_data["value"]) + " "

            search_query = search_query.strip()
            search_results = fetch_search_results(search_query, num_results=5)
            urls_list = [r["url"] for r in search_results]
            urls_dict["global"] = {"query": search_query, "urls": urls_list}
            yield f"data: {json.dumps({'step': 'urls_extracted', 'urls': urls_dict})}\n\n"

            extracted_results = []
            for r in search_results:
                try:
                    pipeline_results = process_query_url(parsed, r["url"])
                except Exception as e:
                    print(f"Error processing URL {r['url']}: {e}")
                    pipeline_results = None

                if pipeline_results:
                    extracted_results.extend(pipeline_results)
                    yield f"data: {json.dumps({'step': 'partial', 'entity': 'global', 'url': r['url']})}\n\n"

            results["global"] = extracted_results

        yield f"data: {json.dumps({'step': 'result', 'source': 'web', 'parsed': parsed, 'results': results, 'urls': urls_dict})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")