from fastapi import APIRouter
from fastapi.responses import StreamingResponse
import json
from backend.services.search_service import fetch_search_results_async
from backend.services.query_parser import parse_query
from backend.domains.tech import TRUSTED_DOMAINS 

from backend.services.db_query_service import fetch_from_db
from backend.services.pipeline_service import process_query_url
from backend.services.processing_service import group_variants_and_persist

router = APIRouter()

@router.get("/db-status")
def db_status():
    try:
        from backend.database.connection import get_db
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM entities")
        e_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM documents")
        d_count = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        return {"status": "connected", "entities": e_count, "documents": d_count}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@router.get("/search")
async def search(query: str, t: str = None):
    parsed = parse_query(query)

    async def event_generator():
        yield f"data: {json.dumps({'step': 'parsed', 'parsed': parsed})}\n\n"

        # ---- STEP 1: CHECK DATABASE ----
        db_results = fetch_from_db(parsed)

        # ---- STEP 2: INTELLIGENT DB CHECK ----
        attribute = parsed.get("attribute")

        use_db = False
        # if attribute:
        #     if attribute in db_results["found_aspects"]:
        #         use_db = True
        # else:
        #     if db_results["data"]:
        #         use_db = True

        if use_db:
            grouped_db_results = {}
            for item in db_results["data"]:
                ent = item.get("entity", "global")
                if ent not in grouped_db_results:
                    grouped_db_results[ent] = []
                item["type"] = item.get("type", "table")
                grouped_db_results[ent].append(item)

            final_resp = {
                "step": "result",
                "source": "database",
                "parsed": parsed,
                "results": grouped_db_results
            }
            yield f"data: {json.dumps(final_resp)}\n\n"
            return

        # ---- STEP 3: FALLBACK TO SEARCH ----
        results = {}
        urls_dict = {}

        if parsed["mode"] == "news":
            news_results = await fetch_search_results_async(query)
            urls_dict["news"] = {"query": query, "urls": [r["url"] for r in news_results]}
            yield f"data: {json.dumps({'step': 'urls_extracted', 'urls': urls_dict})}\n\n"
            results["news"] = news_results
            yield f"data: {json.dumps({'step': 'result', 'source': 'web', 'parsed': parsed, 'results': results, 'urls': urls_dict})}\n\n"
            return

        entities = parsed.get("entities", [])
        filter_data = parsed.get("filter")

        if entities:
            for entity in entities:
                extracted_results = []
                fact_urls = []
                
                # Entity-specific parsed: treat this entity as if it were the only one
                # so the pipeline behaves the same as single-entity mode
                entity_parsed = {**parsed, "entities": [entity], "original": entity}
                
                # --- SYNCHRONOUS FACT CASCADE ---
                has_enough_facts = False
                for domain in ["gsmarena.com", "wikipedia.org", "devicespecifications.com"]:
                    if has_enough_facts:
                        break
                        
                    search_query = f"{entity} site:{domain}"
                    if filter_data:
                        search_query += f" {filter_data['value']}"
                        
                    domain_results = await fetch_search_results_async(search_query, num_results=2)
                    if not domain_results:
                        continue
                        
                    for r in domain_results:
                        url = r["url"]
                        if url in fact_urls:
                            continue
                            
                        fact_urls.append(url)
                        yield f"data: {json.dumps({'step': 'partial', 'entity': entity, 'url': url})}\n\n"
                        try:
                            import asyncio
                            pipeline_results = await asyncio.to_thread(process_query_url, entity_parsed, url, only_objective=True)
                        except Exception as e:
                            print(f"Error processing URL {url}: {e}")
                            pipeline_results = None
                            
                        if pipeline_results:
                            extracted_results.extend([x for x in pipeline_results if x.get("type", "") in ["table", "text"]])
                            
                            found_aspects = {x["aspect"] for x in extracted_results if x.get("type", "") == "table"}
                            if "display" in found_aspects and "battery" in found_aspects and ("ram" in found_aspects or "storage" in found_aspects):
                                has_enough_facts = True
                                break
                
                # --- ASYNC OPINIONS CASCADE ---
                yield f"data: {json.dumps({'step': 'processing', 'message': f'Fetching Reviews for {entity}...'})}\n\n"
                review_query = f"{entity} review"
                review_results = await fetch_search_results_async(review_query, num_results=5)
                review_urls = []
                
                for r in review_results:
                    url = r["url"]
                    if url not in fact_urls:
                        review_urls.append(url)
                        yield f"data: {json.dumps({'step': 'partial', 'entity': f'{entity} Reviews', 'url': url})}\n\n"
                        try:
                            import asyncio
                            pipeline_results = await asyncio.to_thread(process_query_url, entity_parsed, url, only_subjective=True)
                        except Exception as e:
                            print(f"Error processing review URL {url}: {e}")
                            pipeline_results = None
                        
                        if pipeline_results:
                            extracted_results.extend([x for x in pipeline_results if x.get("type", "") == "subjective"])
                            
                urls_dict[entity] = {"query": entity, "urls": fact_urls + review_urls}
                yield f"data: {json.dumps({'step': 'urls_extracted', 'urls': urls_dict})}\n\n"
                
                results[entity] = extracted_results

            yield f"data: {json.dumps({'step': 'processing', 'message': 'Validating and Grouping Variants...'})}\n\n"
            results = group_variants_and_persist(results)

        else:
            search_query = ""

            if attribute:
                search_query += attribute + " "

            if filter_data:
                search_query += str(filter_data["value"]) + " "

            search_query = search_query.strip()
            search_results = await fetch_search_results_async(search_query, num_results=5, trusted_domains=TRUSTED_DOMAINS)
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
            yield f"data: {json.dumps({'step': 'processing', 'message': 'Validating and Grouping Variants...'})}\n\n"
            results = group_variants_and_persist(results)

        yield f"data: {json.dumps({'step': 'result', 'source': 'web', 'parsed': parsed, 'results': results, 'urls': urls_dict})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")