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

async def execute_search(query: str, t: str = None):
    parsed = parse_query(query)

    async def event_generator():
        yield f"data: {json.dumps({'step': 'parsed', 'parsed': parsed})}\n\n"

        # ---- CANONICAL ENTITY RESOLUTION ----
        yield f"data: {json.dumps({'step': 'processing', 'message': 'Resolving Entities...'})}\n\n"
        if parsed.get("entities"):
            original_entities = parsed["entities"]
            canonical_entities = await resolve_canonical_entities(original_entities)
            parsed["entities"] = canonical_entities
            
            # Show a brief update if it was resolved differently
            from backend.config.variables import DEBUG
            if DEBUG and original_entities != canonical_entities:
                yield f"data: {json.dumps({'step': 'processing', 'message': f'Resolved: {canonical_entities}'})}\n\n"

        # ---- QUERY INTENT ANALYSIS ----
        intent = analyze_query_intent(query)
        parsed["intent"] = intent

        # ---- STEP 1: CHECK DATABASE ----
        db_results = fetch_from_db(parsed)

        # ---- STEP 2: INTELLIGENT DB CHECK ----
        attribute = parsed.get("attribute")
        use_db = False

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

        # ---- CLASSIFY QUERY TYPE for trusted domain selection ----
        entities = parsed.get("entities", [])
        filter_data = parsed.get("filter")
        query_type = infer_query_type(query, entities=entities)
        parsed["query_type"] = query_type

        if parsed["mode"] == "news" or query_type.startswith("news"):
            news_domains = get_news_domains(query_type)
            news_results = await fetch_search_results_async(query, num_results=5, trusted_domains=news_domains)
            urls_dict["news"] = {"query": query, "urls": [r["url"] for r in news_results]}
            yield f"data: {json.dumps({'step': 'urls_extracted', 'urls': urls_dict})}\n\n"
            results["news"] = news_results
            yield f"data: {json.dumps({'step': 'result', 'source': 'web', 'parsed': parsed, 'results': results, 'urls': urls_dict})}\n\n"
            return

        # Select fact cascade domains based on inferred type
        if query_type == "tech_laptop":
            fact_cascade_domains = ["notebookcheck.net", "wikipedia.org", "rtings.com"]
        else:  # tech_phone or general
            fact_cascade_domains = ["gsmarena.com", "wikipedia.org", "devicespecifications.com"]

        if entities:
            for entity in entities:
                extracted_results = []
                fact_urls = []
                
                # Entity-specific parsed: treat this entity as if it were the only one
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
