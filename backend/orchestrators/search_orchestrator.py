from fastapi.responses import StreamingResponse
import json
import asyncio
from backend.services.search_service import fetch_search_results_async
from backend.services.query_parser import parse_query
from backend.domains.tech import get_trusted_domains as get_tech_domains
from backend.domains.news import get_trusted_domains as get_news_domains
from backend.domains.domain_signals import infer_query_type

from backend.services.db_query_service import fetch_from_db
from backend.services.pipeline_service import process_query_url, process_news_url, process_research_url
from backend.services.processing_service import group_variants_and_persist
from backend.services.entity_resolver_service import resolve_canonical_entities
from backend.nlp.query_intent import analyze_query_intent
from backend.utils.logger import logger

async def execute_search(query: str, t: str = None):
    logger.info("ORCHESTRATOR", f"Starting segregated streaming search for: '{query}'")
    parsed = parse_query(query)

    async def event_generator():
        yield f"data: {json.dumps({'step': 'parsed', 'parsed': parsed})}\n\n"
        
        facts_data = {}
        research_news_data = {}
        analysis_data = {}
        urls_dict = {}

        def stream_update():
            # Helper to yield current state
            res = {'facts': facts_data, 'research': research_news_data, 'analysis': analysis_data}
            logger.debug("ORCHESTRATOR", f"Streaming Update: Facts={len(facts_data)}, Research={len(research_news_data)}, Analysis={len(analysis_data)}")
            return f"data: {json.dumps({'step': 'partial_result', 'results': res, 'urls': urls_dict})}\n\n"

        def add_to_segregated(items, source_url, entity_name):
            if not items: return
            
            for item in items:
                itype = item.get("type", "table")
                # Normalize entity name to Title Case to match across sources
                raw_ent = item.get("entity", entity_name) or "Global"
                ent = str(raw_ent).title().strip()
                
                # Routing logic
                if itype in ["news", "research"]:
                    target = research_news_data
                elif itype in ["subjective", "conflict", "score"]:
                    target = analysis_data
                else:
                    target = facts_data
                
                if ent not in target: target[ent] = []
                # Avoid duplicates in the same list
                if not any(x.get("aspect") == item.get("aspect") and x.get("value") == item.get("value") for x in target[ent]):
                    target[ent].append(item)
                
                if ent not in urls_dict:
                    urls_dict[ent] = {"query": ent, "urls": []}
                if source_url not in urls_dict[ent]["urls"]:
                    urls_dict[ent]["urls"].append(source_url)

        # ---- CANONICAL ENTITY RESOLUTION ----
        yield f"data: {json.dumps({'step': 'processing', 'message': 'Resolving Entities...'})}\n\n"
        if parsed.get("entities") and parsed.get("mode") == "product":
            canonical_entities = await resolve_canonical_entities(parsed["entities"])
            parsed["entities"] = canonical_entities

        entities = parsed.get("entities", [])
        query_type = parsed.get("query_type", "general")
        attribute = parsed.get("attribute")
        search_region = "in-en"

        # ---- NEWS MODE ----
        if parsed["mode"] == "news":
            news_domains = get_news_domains(query_type)
            # Use timelimit='w' for fresh news (past week)
            news_results = await fetch_search_results_async(query, num_results=6, trusted_domains=news_domains, region=search_region, timelimit="w")
            
            primary_entity = entities[0] if entities else "News"
            summary_list = []
            
            yield f"data: {json.dumps({'step': 'processing', 'message': 'Fetching Latest News...'})}\n\n"
            
            for r in news_results[:5]:
                url = r["url"]
                yield f"data: {json.dumps({'step': 'partial', 'entity': 'News', 'url': url})}\n\n"
                try:
                    p_res = await process_news_url(parsed, url, fallback_text=r.get("snippet"))
                    if p_res:
                        add_to_segregated(p_res, url, primary_entity)
                        for item in p_res:
                            if "Summary:" in item.get("aspect", "") and "value" in item:
                                summary_list.append(item["value"])
                        yield stream_update()
                except Exception as e:
                    logger.error("ORCHESTRATOR", f"Error in news: {e}")

            # Background Wiki Check
            if entities:
                ent = entities[0]
                wiki_res = await fetch_search_results_async(f"{ent} site:wikipedia.org", num_results=1)
                if wiki_res:
                    p_res = await process_query_url(parsed, wiki_res[0]["url"], only_objective=True)
                    add_to_segregated(p_res, wiki_res[0]["url"], ent)
                    yield stream_update()

            # Final Executive Summary
            if summary_list:
                yield f"data: {json.dumps({'step': 'processing', 'message': 'Writing Executive Summary...'})}\n\n"
                from backend.services.ai_service import generate_global_news_summary
                global_sum = await generate_global_news_summary(summary_list)
                if global_sum:
                    yield f"data: {json.dumps({'step': 'ai_summary', 'summary': global_sum})}\n\n"

        # ---- PRODUCT / GENERAL MODE ----
        else:
            # Step 1: Trusted Facts (Fast)
            # Default factual domains
            fact_domains = ["wikipedia.org"]
            if query_type.startswith("tech_phone"): 
                fact_domains = ["gsmarena.com"] + fact_domains
            elif query_type.startswith("tech_laptop"):
                fact_domains = ["notebookcheck.net"] + fact_domains
            
            # For general entities (like people), we want both Facts (Wiki) and Latest News
            for ent in (entities[:1] if entities else ["Global"]):
                yield f"data: {json.dumps({'step': 'processing', 'message': f'Retrieving facts for {ent}...'})}\n\n"
                
                # FACTUAL PHASE
                for domain in fact_domains:
                    s_res = await fetch_search_results_async(f"{ent} site:{domain}", num_results=1)
                    if s_res:
                        url = s_res[0]["url"]
                        yield f"data: {json.dumps({'step': 'partial', 'entity': ent, 'url': url})}\n\n"
                        p_res = await process_query_url(parsed, url)
                        add_to_segregated(p_res, url, ent)
                        yield stream_update()

                # NEWS PHASE (If not a specific tech spec query)
                if not attribute and query_type == "general":
                    yield f"data: {json.dumps({'step': 'processing', 'message': f'Checking latest updates for {ent}...'})}\n\n"
                    # Search for recent news (past month)
                    news_results = await fetch_search_results_async(f"{ent} news", num_results=3, timelimit="m")
                    for r in news_results:
                        url = r["url"]
                        yield f"data: {json.dumps({'step': 'partial', 'entity': ent, 'url': url})}\n\n"
                        try:
                            # Process as news to get summaries
                            p_res = await process_news_url(parsed, url, fallback_text=r.get("snippet"))
                            if p_res:
                                add_to_segregated(p_res, url, ent)
                                yield stream_update()
                        except Exception as e:
                            logger.error("ORCHESTRATOR", f"Error in hybrid news for {ent}: {e}")

            # Step 2: Research & Opinions (Deep)
            yield f"data: {json.dumps({'step': 'processing', 'message': 'Deep Researching...'})}\n\n"
            research_results = await fetch_search_results_async(f"{query} analysis", num_results=3)
            for r in research_results:
                url = r["url"]
                yield f"data: {json.dumps({'step': 'partial', 'entity': 'Research', 'url': url})}\n\n"
                p_res = await process_research_url(parsed, url)
                add_to_segregated(p_res, url, "Research")
                yield stream_update()

        # Final Persistence and cleanup
        yield f"data: {json.dumps({'step': 'processing', 'message': 'Finalizing Results...'})}\n\n"
        final_facts = group_variants_and_persist(facts_data)
        final_research = group_variants_and_persist(research_news_data)
        final_analysis = group_variants_and_persist(analysis_data)
        
        yield f"data: {json.dumps({'step': 'urls_extracted', 'urls': urls_dict})}\n\n"
        
        results = {"facts": final_facts, "research": final_research, "analysis": final_analysis}
        yield f"data: {json.dumps({'step': 'result', 'source': 'web', 'parsed': parsed, 'results': results, 'urls': urls_dict})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
