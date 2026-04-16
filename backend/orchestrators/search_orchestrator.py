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
from backend.services.entity_resolver_service import resolve_canonical_entities
from backend.nlp.query_intent import analyze_query_intent
from backend.utils.logger import logger

async def execute_search(query: str, t: str = None):
    logger.info("ORCHESTRATOR", f"Starting search execution for: '{query}'")
    from backend.services.utils import get_manual_urls
    manual_urls = get_manual_urls(query)
    parsed = parse_query(query)

    async def event_generator():
        yield f"data: {json.dumps({'step': 'parsed', 'parsed': parsed})}\n\n"

        # ---- MANUAL URL MODE ----
        if manual_urls:
            logger.info("ORCHESTRATOR", f"Manual URL mode detected: {len(manual_urls)} URLs")
            yield f"data: {json.dumps({'step': 'processing', 'message': f'Direct Scrape: {len(manual_urls)} URLs found...'})}\n\n"
            results = {}
            urls_dict = {}
            
            # Use query entities if available, else placeholder for inference
            entities = parsed.get("entities", [])
            inferred_entity = entities[0] if entities else None
            
            for url in manual_urls:
                logger.debug("ORCHESTRATOR", f"Processing manual URL: {url}")
                yield f"data: {json.dumps({'step': 'partial', 'entity': inferred_entity or 'Analyzing...', 'url': url})}\n\n"
                try:
                    import asyncio
                    # Direct URLs get DUAL extraction (Both objective and subjective)
                    pipeline_results = await asyncio.to_thread(process_query_url, parsed, url, only_objective=False, only_subjective=False)
                except Exception as e:
                    logger.error("ORCHESTRATOR", f"Error processing manual URL {url}: {e}")
                    pipeline_results = None
                
                if pipeline_results:
                    found_entity = pipeline_results[0].get("entity") if pipeline_results else None
                    target_ent = inferred_entity or found_entity or "Global"
                    
                    if target_ent not in results:
                        results[target_ent] = []
                        urls_dict[target_ent] = {"query": "Manual Input", "urls": []}
                    
                    results[target_ent].extend(pipeline_results)
                    urls_dict[target_ent]["urls"].append(url)
                    
                    if not inferred_entity and found_entity:
                        inferred_entity = found_entity
            
            yield f"data: {json.dumps({'step': 'urls_extracted', 'urls': urls_dict})}\n\n"
            yield f"data: {json.dumps({'step': 'processing', 'message': 'Grouping results...'})}\n\n"
            results = group_variants_and_persist(results)
            yield f"data: {json.dumps({'step': 'result', 'source': 'direct', 'parsed': parsed, 'results': results, 'urls': urls_dict})}\n\n"
            return


        # ---- CANONICAL ENTITY RESOLUTION ----
        yield f"data: {json.dumps({'step': 'processing', 'message': 'Resolving Entities...'})}\n\n"
        if parsed.get("entities"):
            original_entities = parsed["entities"]
            canonical_entities = await resolve_canonical_entities(original_entities)
            parsed["entities"] = canonical_entities
            
            # Show a brief update if it was resolved differently
            from backend.config.variables import DEBUG
            if DEBUG and original_entities != canonical_entities:
                logger.info("ORCHESTRATOR", f"Entities resolved: {original_entities} -> {canonical_entities}")
                yield f"data: {json.dumps({'step': 'processing', 'message': f'Resolved: {canonical_entities}'})}\n\n"

        # ---- QUERY INTENT ANALYSIS ----
        logger.debug("ORCHESTRATOR", "Analyzing query intent")
        intent = analyze_query_intent(query)
        parsed["intent"] = intent

        # ---- STEP 1: CHECK DATABASE ----
        logger.info("ORCHESTRATOR", "Checking cache")
        db_results = fetch_from_db(parsed)

        # ---- STEP 2: INTELLIGENT DB CHECK ----
        # In this version, we always run a fresh search for now unless use_db is true
        use_db = False

        if use_db and len(db_results["data"]) > 0:
            logger.info("ORCHESTRATOR", "Cache hit, returning stored results")
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
        logger.info("ORCHESTRATOR", "No cache, proceeding to search")
        results = {}
        urls_dict = {}

        # ---- CLASSIFY QUERY TYPE ----
        entities = parsed.get("entities", [])
        filter_data = parsed.get("filter")
        query_type = infer_query_type(query, entities=entities)
        parsed["query_type"] = query_type

        if parsed["mode"] == "news" or query_type.startswith("news"):
            news_domains = get_news_domains(query_type)
            logger.info("ORCHESTRATOR", f"News search on: {news_domains}")
            news_results = await fetch_search_results_async(query, num_results=5, trusted_domains=news_domains)
            urls_dict["news"] = {"query": query, "urls": [r["url"] for r in news_results]}
            yield f"data: {json.dumps({'step': 'urls_extracted', 'urls': urls_dict})}\n\n"
            results["news"] = news_results
            yield f"data: {json.dumps({'step': 'result', 'source': 'web', 'parsed': parsed, 'results': results, 'urls': urls_dict})}\n\n"
            return

        # Select fact cascade domains
        if query_type == "tech_laptop":
            fact_cascade_domains = ["notebookcheck.net", "wikipedia.org", "rtings.com"]
        else:
            fact_cascade_domains = ["gsmarena.com", "wikipedia.org", "devicespecifications.com"]

        if entities:
            for entity in entities:
                logger.info("ORCHESTRATOR", f"Processing entity: {entity}")
                extracted_results = []
                fact_urls = []
                entity_parsed = {**parsed, "entities": [entity], "original": entity}
                
                # --- SYNCHRONOUS FACT CASCADE ---
                has_enough_facts = False
                for domain in fact_cascade_domains:
                    if has_enough_facts: break
                        
                    logger.debug("ORCHESTRATOR", f"Cascade: searching {domain} for {entity}")
                    search_query = f"{entity} site:{domain}"
                    if filter_data:
                        search_query += f" {filter_data['value']}"
                        
                    domain_results = await fetch_search_results_async(search_query, num_results=2)
                    if not domain_results: continue
                        
                    for r in domain_results:
                        url = r["url"]
                        if url in fact_urls: continue
                            
                        fact_urls.append(url)
                        yield f"data: {json.dumps({'step': 'partial', 'entity': entity, 'url': url})}\n\n"
                        try:
                            import asyncio
                            pipeline_results = await asyncio.to_thread(process_query_url, entity_parsed, url, only_objective=True)
                        except Exception as e:
                            logger.error("ORCHESTRATOR", f"Error processing URL {url}: {e}")
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
                            logger.error("ORCHESTRATOR", f"Error processing review URL {url}: {e}")
                            pipeline_results = None
                        
                        if pipeline_results:
                            extracted_results.extend([x for x in pipeline_results if x.get("type", "") == "subjective"])
                            
                urls_dict[entity] = {"query": entity, "urls": fact_urls + review_urls}
                yield f"data: {json.dumps({'step': 'urls_extracted', 'urls': urls_dict})}\n\n"
                results[entity] = extracted_results

            yield f"data: {json.dumps({'step': 'processing', 'message': 'Grouping Variants...'})}\n\n"
            results = group_variants_and_persist(results)

        else:
            # Global search logic
            logger.info("ORCHESTRATOR", "Global search path")
            search_query = parsed.get("attribute", "") + " " + (str(filter_data["value"]) if filter_data else "")
            search_query = search_query.strip() or query

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
                    logger.error("ORCHESTRATOR", f"Error processing URL {r['url']}: {e}")
                    pipeline_results = None

                if pipeline_results:
                    extracted_results.extend(pipeline_results)
                    yield f"data: {json.dumps({'step': 'partial', 'entity': 'global', 'url': r['url']})}\n\n"

            results["global"] = extracted_results
            yield f"data: {json.dumps({'step': 'processing', 'message': 'Grouping Results...'})}\n\n"
            results = group_variants_and_persist(results)

        logger.info("ORCHESTRATOR", "Search sequence complete")
        yield f"data: {json.dumps({'step': 'result', 'source': 'web', 'parsed': parsed, 'results': results, 'urls': urls_dict})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
