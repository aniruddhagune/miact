from fastapi import APIRouter
from fastapi.responses import StreamingResponse
import json
from backend.services.search_service import fetch_search_results_async
from backend.services.query_parser import parse_query
from backend.domains.tech import get_trusted_domains as get_tech_domains
from backend.domains.news import get_trusted_domains as get_news_domains
from backend.domains.domain_signals import infer_query_type

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

@router.post("/clear-db")
def clear_db():
    try:
        from backend.database.connection import get_connection
        conn = get_connection()
        cursor = conn.cursor()
        # Truncate tables to clear all cache
        cursor.execute("TRUNCATE TABLE facts, documents, entities, sources CASCADE")
        conn.commit()
        cursor.close()
        conn.close()
        return {"status": "success", "message": "Cache cleared successfully"}
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
        # If we found any results for the entities in the database, use them.
        use_db = len(db_results["data"]) > 0

        if use_db:
            grouped_db_results = {}
            db_urls = {}
            
            for item in db_results["data"]:
                ent = item.get("entity", "global")
                if ent not in grouped_db_results:
                    grouped_db_results[ent] = []
                    db_urls[ent] = {"query": ent, "urls": []}
                
                # Reconstruct results format
                grouped_db_results[ent].append(item)
                
                # Reconstruct URLs for the sources popup
                source_url = item.get("source")
                if source_url and source_url not in db_urls[ent]["urls"]:
                    db_urls[ent]["urls"].append(source_url)

            final_resp = {
                "step": "result",
                "source": "database",
                "parsed": parsed,
                "results": grouped_db_results,
                "urls": db_urls
            }
            yield f"data: {json.dumps(final_resp)}\n\n"
            return

        # ---- STEP 3: FALLBACK TO SEARCH ----
        results = {}
        urls_dict = {}

        # ---- CLASSIFY QUERY TYPE for trusted domain selection ----
        entities = parsed.get("entities", [])
        filter_data = parsed.get("filter")
        query_type = infer_query_type(query, entities=entities)
        parsed["query_type"] = query_type

        if parsed["mode"] == "news" or query_type.startswith("news"):
            news_domains = get_news_domains(query_type)
            search_results = await fetch_search_results_async(query, num_results=5, trusted_domains=news_domains)
            urls_list = [r["url"] for r in search_results]
            urls_dict["news"] = {"query": query, "urls": urls_list}
            yield f"data: {json.dumps({'step': 'urls_extracted', 'urls': urls_dict})}\n\n"

            extracted_results = []
            for r in search_results:
                url = r["url"]
                snippet = r.get("snippet", "")
                yield f"data: {json.dumps({'step': 'partial', 'entity': 'News', 'url': url})}\n\n"
                try:
                    import asyncio
                    # Pass snippet as fallback
                    pipeline_results = await asyncio.to_thread(process_query_url, parsed, url, fallback_text=snippet)
                    if pipeline_results:
                        extracted_results.extend(pipeline_results)
                except Exception as e:
                    print(f"Error processing news URL {url}: {e}")

            results["news"] = extracted_results
            yield f"data: {json.dumps({'step': 'processing', 'message': 'Grouping Results...'})}\n\n"
            results = group_variants_and_persist(results)
            yield f"data: {json.dumps({'step': 'result', 'source': 'web', 'parsed': parsed, 'results': results, 'urls': urls_dict})}\n\n"
            return

        # Select fact cascade domains based on inferred type
        if query_type == "tech_laptop":
            fact_cascade_domains = ["notebookcheck.net", "wikipedia.org", "rtings.com"]
        elif query_type == "tech_phone":
            fact_cascade_domains = ["gsmarena.com", "wikipedia.org", "devicespecifications.com"]
        else:  # news_* or general
            fact_cascade_domains = ["wikipedia.org"]

        if entities:
            for entity in entities:
                extracted_results = []
                fact_urls = []
                
                # Entity-specific parsed: treat this entity as if it were the only one
                # so the pipeline behaves the same as single-entity mode
                entity_parsed = {**parsed, "entities": [entity], "original": entity}
                
                # --- SYNCHRONOUS FACT CASCADE (per-type domains) ---
                has_enough_facts = False
                for domain in fact_cascade_domains:
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
                            
                            if query_type.startswith("tech"):
                                found_aspects = {x["aspect"] for x in extracted_results if x.get("type", "") == "table"}
                                if "display" in found_aspects and "battery" in found_aspects:
                                    has_enough_facts = True
                                    break
                            else:
                                if len(extracted_results) > 10:
                                    has_enough_facts = True
                                    break
                
                # --- ASYNC OPINIONS CASCADE ---
                is_tech = query_type.startswith("tech")
                review_query = f"{entity} review" if is_tech else f"{entity} opinions analysis"
                
                yield f"data: {json.dumps({'step': 'processing', 'message': f'Fetching Analysis for {entity}...'})}\n\n"
                review_results = await fetch_search_results_async(review_query, num_results=5 if is_tech else 3)
                review_urls = []
                
                for r in review_results:
                    url = r["url"]
                    if url not in fact_urls:
                        review_urls.append(url)
                        yield f"data: {json.dumps({'step': 'partial', 'entity': f'{entity} Views', 'url': url})}\n\n"
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
            general_domains = get_tech_domains(query_type)
            search_results = await fetch_search_results_async(search_query, num_results=5, trusted_domains=general_domains)
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