from backend.extractors.utils import clean_text, split_into_sentences

from backend.extractors.extractor_content import extract_content
from backend.services.mapper_domain import detect_domain
from backend.extractors.detector_subjects import extract_subjects, build_subject_aliases, detect_subjects, is_shared_context, split_comparison

from backend.extractors.extractor_data import extract_attributes, extract_tables, parse_table_numeric
from backend.services.utils import deduplicate_attributes
from backend.domains.opinion_aspects import map_to_canonical_aspect

# Modern NLP Imports
from backend.nlp.grammar_structural import classify_clause
from backend.nlp.mapper_aspect_sentiment import analyze_aspect_sentiment # Ensure this uses structural too


def is_valid_opinion(text, aspect, score, structural_info=None):
    # If structural analysis (spaCy) found it's incomplete or a question, skip.
    if structural_info:
        if structural_info.get("completeness") == "incomplete":
            return False
        if structural_info.get("is_question"):
            return False

    # Discard exactly-zero scores (neutral)
    if score is None or score == 0:
        return False

    # Tangible check for quality signal
    text_lower = text.lower()
    TANGIBLE_TERMS = ["feel", "build", "performance", "speed", "camera", "battery",
                      "display", "screen", "price", "value", "design", "quality",
                      "software", "smooth", "fast", "slow", "hot", "heat", "lag",
                      "charging", "speakers", "audio", "storage", "graphics"]
    
    # Tangible check for quality signal - e.g., "Camera is great" (3 words)
    # General check - e.g., "I really like it" (4 words, fails) -> 6 words
    WORDS_MINIMUM = 3 if any(t in text_lower for t in TANGIBLE_TERMS) else 6
    if len(text.split()) < WORDS_MINIMUM:
        return False

    return True


def process_query_url(parsed: dict, url: str, only_objective=False, only_subjective=False):
    query = parsed.get("original", "")
    domain = detect_domain(query)

    subjects = parsed.get("entities", [])
    if not subjects:
        subjects = extract_subjects(query)

    alias_map = build_subject_aliases(subjects)

    data = extract_content(url)

    if not data:
        return None

    results = []
    seen_objective_aspects = set()

    tables = data.get("tables", []) if not only_subjective else []
    print("\n[DEBUG] TABLES COUNT:", len(tables))

    for row in tables:
        if "battery" in row["aspect"]:
            print("[DEBUG] BATTERY ROW:", row)

    for row in tables:
        parsed_numeric = parse_table_numeric(row["value"])
        
        final_value = parsed_numeric["value"] if parsed_numeric else row["value"]
        final_unit = parsed_numeric["unit"] if parsed_numeric else None

        matched_subjects = detect_subjects(row["value"], alias_map)

        # ---- FALLBACK: assume main subject if nothing matched ----
        if not matched_subjects and len(subjects) == 1:
            matched_subjects = subjects

        for subject in matched_subjects:
            key = (subject, row["aspect"])
            if key in seen_objective_aspects:
                continue
            seen_objective_aspects.add(key)

            from backend.services.utils import expand_variants
            variants = expand_variants(row["aspect"], row["value"])
            
            for v in variants:
                results.append({
                    "entity": subject,
                    "aspect": row["aspect"],
                    "value": final_value if len(variants) == 1 else v, # use original parsed if only 1, else split strings
                    "unit": final_unit if len(variants) == 1 else None,
                    "type": "table",
                    "source": url
                })

    if not data:
        return None

    # ---- OPINION RESTRICTOR ----
    is_review = any(x in url.lower() for x in ["review", "opinion", "hands-on", "verdict", "test", "depth"]) or domain in ["gsmarena", "theverge", "engadget", "tomsguide", "zdnet", "techradar", "tech", "gadget", "notebookcheck"]

    cleaned = clean_text(data["text"])
    sentences = split_into_sentences(cleaned)

    seen_global = set()
    seen_subjective_texts = set()

    for s in sentences:
        parts = split_comparison(s)
        sentence_subjects = detect_subjects(s, alias_map)

        shared = (
            is_shared_context(s)
            or len(sentence_subjects) > 1
        )

        for part in parts:
            matched_subjects = detect_subjects(part, alias_map)

            if shared:
                matched_subjects = subjects

            if not matched_subjects:
                # ---- FALLBACK: if single subject query, assume main subject for all snippets ----
                if len(subjects) == 1:
                    matched_subjects = subjects
                else:
                    continue

            attributes = []
            if not only_subjective:
                attributes = extract_attributes(part, domain)
                attributes = deduplicate_attributes(attributes)
            
            sentiment_aspects = []
            if is_review and not only_objective:
                sentiment_aspects = analyze_aspect_sentiment(part, domain)

            query_attribute = parsed.get("attribute")

            # ---- META ATTRIBUTES (do NOT filter) ----
            META_ATTRIBUTES = ["specifications", "specs"]

            if query_attribute and query_attribute not in META_ATTRIBUTES:
                attributes = [
                    a for a in attributes
                    if a.get("aspect") == query_attribute
                ]
                sentiment_aspects = [
                    sa for sa in sentiment_aspects
                    if sa.get("aspect") == query_attribute
                ]

            for subject in matched_subjects:
                for attr in attributes:
                    key = (subject, attr["aspect"])

                    if key in seen_objective_aspects:
                        continue

                    seen_objective_aspects.add(key)

                    results.append({
                        "entity": subject,
                        "aspect": attr["aspect"],
                        "value": attr["value"],
                        "unit": attr.get("unit"),
                        "type": attr.get("type"),
                        "source": url
                    })
                
                for sa in sentiment_aspects:
                    raw_text = sa["text"].strip().lower()

                    # Modern: Use Structural Classifier
                    structural = classify_clause(sa["text"])

                    if not is_valid_opinion(sa["text"], sa["aspect"], sa["score"], structural):
                        continue

                    text_key = (subject, raw_text)
                    if text_key in seen_subjective_texts:
                        continue
                    
                    seen_subjective_texts.add(text_key)

                    # Update score with structural score if it's more nuanced
                    final_score = sa["score"]
                    if structural.get("score") is not None:
                        # Blend if sa["score"] was generic
                        final_score = structural["score"]

                    results.append({
                        "entity": subject,
                        "aspect": map_to_canonical_aspect(sa["aspect"]) or sa["aspect"],
                        "sentiment": sa["sentiment"],
                        "score": final_score,
                        "text": sa["text"],
                        "type": "subjective",
                        "source": url
                    })

    # ---- GSMARENA OPINIONS (NEW) ----
    if not only_objective:
        gsm_opinions = data.get("opinions", [])
        for op in gsm_opinions:
            op_text = op["text"]
            # Treat each opinion like a review sentence
            sentiment_aspects = analyze_aspect_sentiment(op_text, domain)
            
            # Determine subjects (assume main subjects if not mentioned)
            matched_subjects = detect_subjects(op_text, alias_map)
            if not matched_subjects:
                matched_subjects = subjects

            for subject in matched_subjects:
                for sa in sentiment_aspects:
                    if not is_valid_opinion(sa["text"], sa["aspect"], sa["score"]):
                        continue
                        
                    text_key = (subject, sa["text"].lower())
                    if text_key in seen_subjective_texts:
                        continue
                    seen_subjective_texts.add(text_key)

                    canonical_aspect = map_to_canonical_aspect(sa["aspect"]) or sa["aspect"]

                    results.append({
                        "entity": subject,
                        "aspect": canonical_aspect,
                        "sentiment": sa["sentiment"],
                        "score": sa["score"],
                        "text": sa["text"],
                        "type": "subjective",
                        "source": url,
                        "metadata": {"user_review": True} # Flag for UI
                    })

    return results