from backend.extractors.utils import clean_text, split_into_sentences
from backend.extractors.extractor_content import extract_content
from backend.services.mapper_domain import detect_domain
from backend.extractors.detector_subjects import extract_subjects, build_subject_aliases, detect_subjects, is_shared_context, split_comparison
from backend.extractors.extractor_data import extract_attributes, extract_tables, parse_table_numeric
from backend.utils.utils import deduplicate_attributes
from backend.domains.opinion_aspects import map_to_canonical_aspect
from backend.services.ai_service import summarize_news_ai
from backend.nlp.relevance_engine import is_english_text
from backend.utils.logger import logger
import asyncio

# Modern NLP Imports
from backend.nlp.grammar_structural import classify_clause
from backend.nlp.mapper_aspect_sentiment import analyze_aspect_sentiment, analyze_sentiment_vader


def is_valid_opinion(text, aspect, score, structural_info=None):
    # If structural analysis (spaCy) found it's a question, skip.
    if structural_info and structural_info.get("is_question"):
        return False

    # Lowered Threshold: Capture more nuances
    if score is None or abs(score) < 0.15:
        return False

    text_lower = text.lower()
    # If it's a known 'issue' or 'problem', it's almost always valid
    if any(k in text_lower for k in ["issue", "problem", "bug", "fault", "error", "fail"]):
        return True

    # Relaxed word counts
    TANGIBLE_TERMS = ["battery", "screen", "camera", "display", "speed", "performance", "build", "feel", "price"]
    WORDS_MINIMUM = 2 if any(t in text_lower for t in TANGIBLE_TERMS) else 4
    
    if len(text.split()) < WORDS_MINIMUM:
        return False

    return True


async def process_query_url(parsed: dict, url: str, only_objective=False, only_subjective=False, fallback_text=None):
    logger.info("PIPELINE", f"Start: {url}")
    query = parsed.get("original", "")
    domain = detect_domain(query)

    subjects = parsed.get("entities", [])
    if not subjects:
        subjects = extract_subjects(query)
    
    logger.debug("PIPELINE", f"Entities: {subjects} | Domain: {domain}")

    alias_map = build_subject_aliases(subjects)
    
    # Try actual scraping
    logger.debug("PIPELINE", f"Dispatching extraction for: {url}")
    data = await extract_content(url)

    # ---- SCRAPING FALLBACK ----
    if (not data or not data.get("text")) and fallback_text:
        logger.warning("PIPELINE", f"Live Scraping FAILED/BLOCKED for {url}. Using search snippet fallback.")
        data = {
            "title": "Search Summary",
            "text": fallback_text,
            "tables": [],
            "opinions": [],
            "source": url,
            "is_snippet": True
        }

    if not data:
        logger.error(f"Extraction failed completely for {url}")
        return None

    clean_text_content = data.get("text", "")
    if clean_text_content and not is_english_text(clean_text_content):
        logger.warning("PIPELINE", f"LanguageGuard: Article content is non-English for {url}. Skipping.")
        return []

    logger.debug(f"Successfully retrieved {len(clean_text_content)} chars from {url}")

    results = []
    
    # If it's a snippet, we'll label the aspect as "Summary" so it's visible
    if data.get("is_snippet"):
        logger.debug("PIPELINE", "Processing as Snippet Fallback")
        for subject in subjects:
            results.append({
                "entity": subject,
                "aspect": "Brief Summary",
                "value": data["text"],
                "type": "table",
                "source": url
            })
        return results

    seen_objective_aspects = set()
    seen_subjective_texts = set()

    tables = data.get("tables", []) if not only_subjective else []
    if tables:
        logger.info("PIPELINE", f"Processing {len(tables)} table entries from {url}")
    
    for row in tables:
        parsed_numeric = parse_table_numeric(row["value"])
        final_value = parsed_numeric["value"] if parsed_numeric else row["value"]
        final_unit = parsed_numeric["unit"] if parsed_numeric else None

        matched_subjects = detect_subjects(row["value"], alias_map) or (subjects if len(subjects) == 1 else [])
        for subject in matched_subjects:
            key = (subject, row["aspect"])
            if key in seen_objective_aspects: continue
            seen_objective_aspects.add(key)

            from backend.utils.utils import expand_variants
            for v in expand_variants(row["aspect"], row["value"]):
                results.append({
                    "entity": subject, "aspect": row["aspect"],
                    "value": final_value if len(row["value"]) == 1 else v,
                    "unit": final_unit, "type": "table", "source": url
                })

    # ---- OPINION RESTRICTOR ----
    is_review = any(x in url.lower() for x in ["review", "opinion", "hands-on", "verdict", "test", "depth"]) or \
                any(d in url.lower() for d in ["gsmarena.com", "theverge.com", "engadget.com"])

    sentences = split_into_sentences(clean_text(data.get("text", "")))
    logger.debug("PIPELINE", f"Analyzing {len(sentences)} sentences for opinions in {url}")
    
    for s in sentences:
        parts = split_comparison(s)
        for part in parts:
            matched_subjects = detect_subjects(part, alias_map) or (subjects if len(subjects) == 1 else [])
            if not matched_subjects: continue

            sentiment_aspects = []
            if is_review and not only_objective:
                sentiment_aspects = analyze_aspect_sentiment(part, domain)
                
                # FALLBACK: If sa was empty but sentiment is high, use "Overall Impression"
                if not sentiment_aspects:
                    v_score = analyze_sentiment_vader(part)
                    if abs(v_score) > 0.4:
                        sentiment_aspects.append({
                            "text": part, "aspect": "overall",
                            "sentiment": "positive" if v_score > 0 else "negative", "score": v_score
                        })

            for subject in matched_subjects:
                for sa in sentiment_aspects:
                    structural = classify_clause(sa["text"])
                    if not is_valid_opinion(sa["text"], sa["aspect"], sa["score"], structural):
                        continue

                    text_key = (subject, sa["text"].lower())
                    if text_key in seen_subjective_texts: continue
                    seen_subjective_texts.add(text_key)

                    results.append({
                        "entity": subject,
                        "aspect": map_to_canonical_aspect(sa["aspect"]) or sa["aspect"],
                        "sentiment": sa["sentiment"], "score": sa["score"],
                        "text": sa["text"], "type": "subjective", "source": url,
                        "metadata": {"is_professional": is_review}
                    })

    # ---- GSMARENA OPINIONS ----
    if not only_objective:
        gsma_ops = data.get("opinions", [])
        if gsma_ops:
            logger.debug("PIPELINE", f"Processing {len(gsma_ops)} site-extracted opinions from {url}")
        for op in gsma_ops:
            op_text = op["text"]
            sentiment_aspects = analyze_aspect_sentiment(op_text, domain)
            
            if not sentiment_aspects:
                v_score = analyze_sentiment_vader(op_text)
                if abs(v_score) > 0.2:
                    sentiment_aspects.append({
                        "text": op_text, "aspect": "overall",
                        "sentiment": "positive" if v_score > 0 else "negative", "score": v_score
                    })

            matched_subjects = detect_subjects(op_text, alias_map) or subjects
            for subject in matched_subjects:
                for sa in sentiment_aspects:
                    if not is_valid_opinion(sa["text"], sa["aspect"], sa["score"]): continue
                    text_key = (subject, sa["text"].lower())
                    if text_key in seen_subjective_texts: continue
                    seen_subjective_texts.add(text_key)

                    results.append({
                        "entity": subject,
                        "aspect": map_to_canonical_aspect(sa["aspect"]) or sa["aspect"],
                        "sentiment": sa["sentiment"], "score": sa["score"],
                        "text": sa["text"], "type": "subjective", "source": url,
                        "metadata": {"user_review": True, "is_professional": False}
                    })

    logger.info("PIPELINE", f"Finished: {url} | Found {len(results)} total items.")
    return results

async def process_news_url(parsed: dict, url: str, fallback_text: str = None) -> list:
    """
    Extracts a full news article and generates an AI summary.
    """
    logger.info("PIPELINE", f"Processing News URL: {url}")
    
    # Use existing extract_content
    data = await extract_content(url)
    
    clean_text_content = ""
    if data and data.get("text"):
        clean_text_content = data["text"]
    elif fallback_text:
        logger.warning("PIPELINE", f"Extraction failed for news URL {url}. Using fallback snippet.")
        clean_text_content = fallback_text
    
    if not clean_text_content:
        logger.error("PIPELINE", f"No content available for news URL: {url}")
        return []

    if not is_english_text(clean_text_content):
        logger.warning("PIPELINE", f"LanguageGuard: News article content is non-English for {url}. Skipping.")
        return []

    # Summarize via AI
    summary = await summarize_news_ai(clean_text_content)
    
    # Determine Entity
    entities = parsed.get("entities", [])
    target_entity = entities[0] if entities else "News Summary"
    
    published_at = data.get("published_at") if data else None

    return [{
        "entity": target_entity,
        "aspect": "AI Highlights",
        "value": summary,
        "type": "table",
        "source": url,
        "date": published_at
    }]
