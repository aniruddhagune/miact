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
from backend.utils.logger import logger

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
        logger.error("SEARCH", f"Database status check failed: {e}")
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
        logger.info("SEARCH", "Database cache cleared manually via API.")
        return {"status": "success", "message": "Cache cleared successfully"}
    except Exception as e:
        logger.error("SEARCH", f"Failed to clear database cache: {e}")
        return {"status": "error", "message": str(e)}

@router.get("/search")
async def search(query: str, t: str = None):
    logger.info("SEARCH", f"Received search request: '{query}'")
    parsed = parse_query(query)
    logger.debug("SEARCH", f"Parsed query data", data=parsed)

    async def event_generator():
        yield f"data: {json.dumps({'step': 'parsed', 'parsed': parsed})}\n\n"

        # ---- STEP 1: CHECK DATABASE ----
        logger.info("SEARCH", "Checking database for cached results...")
        db_results = fetch_from_db(parsed)

        # ---- STEP 2: INTELLIGENT DB CHECK ----
        use_db = len(db_results["data"]) > 0

        if use_db:
            logger.info("SEARCH", f"Found {len(db_results['data'])} cached results in database.")
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
        logger.info("SEARCH", "No cache found. Proceeding to web search.")
        results = {}
        urls_dict = {}

        # ---- CLASSIFY QUERY TYPE for trusted domain selection ----
        entities = parsed.get("entities", [])
        filter_data = parsed.get("filter")
        query_type = infer_query_type(query, entities=entities)
        parsed["query_type"] = query_type
        logger.info("SEARCH", f"Inferred query type: {query_type}")

        if parsed["mode"] == "news" or query_type.startswith("news"):
            news_domains = get_news_domains(query_type)
            logger.info("SEARCH", f"Fetching news from trusted domains: {news_domains}")
            search_results = await fetch_search_results_async(query, num_results=5, trusted_domains=news_domains)
            urls_list = [r["url"] for r in search_results]
            urls_dict["news"] = {"query": query, "urls": urls_list}
            yield f"data: {json.dumps({'step': 'urls_extracted', 'urls': urls_dict})}\n\n"

            extracted_results = []
            for r in search_results:
                url = r["url"]
                snippet = r.get("snippet", "")
                logger.debug("SEARCH", f"Processing News URL: {url}")
                yield f"data: {json.dumps({'step': 'partial', 'entity': 'News', 'url': url})}\n\n"
                try:
                    # process_query_url is now async
                    pipeline_results = await process_query_url(parsed, url, fallback_text=snippet)
                    if pipeline_results:
                        extracted_results.extend(pipeline_results)
                        logger.debug("SEARCH", f"Extracted {len(pipeline_results)} items from {url}")
                except Exception as e:
                    logger.error("SEARCH", f"Error processing news URL {url}: {e}")

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
        
        logger.info("SEARCH", f"Fact cascade domains: {fact_cascade_domains}")

        if entities:
            for entity in entities:
                logger.info("SEARCH", f"Processing entity: {entity}")
                extracted_results = []
                fact_urls = []
                
                # Entity-specific parsed: treat this entity as if it were the only one
                entity_parsed = {**parsed, "entities": [entity], "original": entity}
                
                # --- SYNCHRONOUS FACT CASCADE (per-type domains) ---
                has_enough_facts = False
                for domain in fact_cascade_domains:
                    if has_enough_facts:
                        break
                    
                    logger.debug("SEARCH", f"Searching facts for '{entity}' on {domain}")
                    search_query = f"{entity} site:{domain}"
                    if filter_data:
                        search_query += f" {filter_data['value']}"
                        
                    domain_results = await fetch_search_results_async(search_query, num_results=2)
                    if not domain_results:
                        logger.debug("SEARCH", f"No results for {entity} on {domain}")
                        continue
                        
                    for r in domain_results:
                        url = r["url"]
                        if url in fact_urls:
                            continue
                            
                        fact_urls.append(url)
                        logger.debug("SEARCH", f"Processing Fact URL: {url}")
                        yield f"data: {json.dumps({'step': 'partial', 'entity': entity, 'url': url})}\n\n"
                        try:
                            # process_query_url is now async
                            pipeline_results = await process_query_url(entity_parsed, url, only_objective=True)
                        except Exception as e:
                            logger.error("SEARCH", f"Error processing URL {url}: {e}")
                            pipeline_results = None
                            
                        if pipeline_results:
                            extracted_results.extend([x for x in pipeline_results if x.get("type", "") in ["table", "text"]])
                            logger.debug("SEARCH", f"Extracted {len(pipeline_results)} facts from {url}")
                            
                            if query_type.startswith("tech"):
                                found_aspects = {x["aspect"] for x in extracted_results if x.get("type", "") == "table"}
                                if "display" in found_aspects and "battery" in found_aspects:
                                    logger.info("SEARCH", f"Enough facts found for {entity} from {domain}")
                                    has_enough_facts = True
                                    break
                            else:
                                if len(extracted_results) > 10:
                                    logger.info("SEARCH", f"Enough facts found for {entity} from {domain}")
                                    has_enough_facts = True
                                    break
                
                # --- ASYNC OPINIONS CASCADE ---
                is_tech = query_type.startswith("tech")
                review_query = f"{entity} review" if is_tech else f"{entity} opinions analysis"
                
                logger.info("SEARCH", f"Fetching opinions for '{entity}' with query: '{review_query}'")
                yield f"data: {json.dumps({'step': 'processing', 'message': f'Fetching Analysis for {entity}...'})}\n\n"
                review_results = await fetch_search_results_async(review_query, num_results=5 if is_tech else 3)
                review_urls = []
                
                for r in review_results:
                    url = r["url"]
                    if url not in fact_urls:
                        review_urls.append(url)
                        logger.debug("SEARCH", f"Processing Review URL: {url}")
                        yield f"data: {json.dumps({'step': 'partial', 'entity': f'{entity} Views', 'url': url})}\n\n"
                        try:
                            # process_query_url is now async
                            pipeline_results = await process_query_url(entity_parsed, url, only_subjective=True)
                        except Exception as e:
                            logger.error("SEARCH", f"Error processing review URL {url}: {e}")
                            pipeline_results = None
                        
                        if pipeline_results:
                            extracted_results.extend([x for x in pipeline_results if x.get("type", "") == "subjective"])
                            logger.debug("SEARCH", f"Extracted {len(pipeline_results)} opinions from {url}")
                            
                urls_dict[entity] = {"query": entity, "urls": fact_urls + review_urls}
                yield f"data: {json.dumps({'step': 'urls_extracted', 'urls': urls_dict})}\n\n"
                
                results[entity] = extracted_results

            yield f"data: {json.dumps({'step': 'processing', 'message': 'Validating and Grouping Variants...'})}\n\n"
            results = group_variants_and_persist(results)

        else:
            # Global search logic (no specific entities)
            logger.info("SEARCH", "No specific entities detected, using global search.")
            search_query = ""
            attribute = parsed.get("attribute")

            if attribute:
                search_query += attribute + " "

            if filter_data:
                search_query += str(filter_data["value"]) + " "

            search_query = search_query.strip()
            if not search_query:
                search_query = query

            general_domains = get_tech_domains(query_type)
            logger.info("SEARCH", f"Global search query: '{search_query}' on domains: {general_domains}")
            search_results = await fetch_search_results_async(search_query, num_results=5, trusted_domains=general_domains)
            urls_list = [r["url"] for r in search_results]
            urls_dict["global"] = {"query": search_query, "urls": urls_list}
            yield f"data: {json.dumps({'step': 'urls_extracted', 'urls': urls_dict})}\n\n"

            extracted_results = []
            for r in search_results:
                logger.debug("SEARCH", f"Processing Global URL: {r['url']}")
                try:
                    # process_query_url is now async
                    pipeline_results = await process_query_url(parsed, r["url"])
                except Exception as e:
                    logger.error("SEARCH", f"Error processing URL {r['url']}: {e}")
                    pipeline_results = None

                if pipeline_results:
                    extracted_results.extend(pipeline_results)
                    logger.debug("SEARCH", f"Extracted {len(pipeline_results)} items from {r['url']}")
                    yield f"data: {json.dumps({'step': 'partial', 'entity': 'global', 'url': r['url']})}\n\n"

            results["global"] = extracted_results
            yield f"data: {json.dumps({'step': 'processing', 'message': 'Validating and Grouping Variants...'})}\n\n"
            results = group_variants_and_persist(results)

        logger.info("SEARCH", "Search completed successfully.")
        yield f"data: {json.dumps({'step': 'result', 'source': 'web', 'parsed': parsed, 'results': results, 'urls': urls_dict})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
