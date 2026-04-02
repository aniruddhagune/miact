import re
from backend.services.preprocessing import *

from backend.services.extractor_content import extract_content
from backend.services.mapper_domain import detect_domain
from backend.services.detector_subjects import *

from backend.services.extractor_data import extract_attributes, extract_tables, parse_table_numeric
from backend.services.utils import deduplicate_attributes
from backend.services.mapper_aspect_sentiment import analyze_aspect_sentiment


def is_valid_opinion(text, aspect, score):
    # Discard exactly-zero scores (neutral)
    if score is None or score == 0:
        return False

    text_str = text.strip()
    text_lower = text_str.lower()
    words = text_str.split()

    # Tangible terms / direct aspect match
    TANGIBLE_TERMS = ["feel", "build", "performance", "speed", "camera", "battery",
                      "display", "screen", "price", "value", "design", "quality",
                      "software", "smooth", "fast", "slow", "hot", "heat", "lag"]
    is_tangible = any(t in text_lower for t in TANGIBLE_TERMS)
    is_overall = any(k in text_lower for k in ["phone", "device", "overall", "recommend", "worth"])

    # Direct aspect phrase: e.g. "great camera", "poor battery" — allow short if clear sentiment word
    SENTIMENT_WORDS = ["great", "excellent", "good", "bad", "terrible", "poor", "amazing",
                       "love", "hate", "worst", "best", "awful", "incredible", "disappointing",
                       "impressive", "mediocre", "solid", "decent", "weak", "strong"]
    is_direct_aspect = is_tangible and any(s in text_lower for s in SENTIMENT_WORDS)

    # Fragment checks
    if text_str and text_str[0].islower() and not is_direct_aspect:
        return False  # Likely a mid-sentence fragment
    if text_str and text_str[-1] in (',', ':', '-', '–'):
        return False  # Trailing incomplete punctuation

    # Minimum length — short only allowed for direct aspect matches
    if len(words) < 7 and not is_direct_aspect:
        return False

    # Reject high digit ratio — likely a technical spec, not an opinion
    digit_words = sum(1 for w in words if re.match(r'^\d+[\d.,x%GBMHzms]*$', w))
    if len(words) > 0 and digit_words / len(words) > 0.3:
        return False

    # Require some word variety
    if len(set(w.lower() for w in words)) < 3:
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
    is_review = any(x in url.lower() for x in ["review", "opinion", "hands-on", "verdict"]) or domain in ["gsmarena", "theverge", "engadget", "tomsguide", "zdnet", "techradar"]

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

                    text_key = (subject, raw_text)
                    if text_key in seen_subjective_texts:
                        continue
                    
                    seen_subjective_texts.add(text_key)

                    key = (
                        subject,
                        sa["aspect"],
                        "subjective",
                        sa["sentiment"]
                    )

                    if key in seen_global:
                        continue

                    seen_global.add(key)

                    results.append({
                        "entity": subject,
                        "aspect": sa["aspect"],
                        "sentiment": sa["sentiment"],
                        "score": sa["score"],
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

                    results.append({
                        "entity": subject,
                        "aspect": sa["aspect"],
                        "sentiment": sa["sentiment"],
                        "score": sa["score"],
                        "text": sa["text"],
                        "type": "subjective",
                        "source": url,
                        "metadata": {"user_review": True} # Flag for UI
                    })

    return results