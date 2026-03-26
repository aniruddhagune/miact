# ---- Imports ---- 

import re
import spacy

from services.aspect_extractor import extract_aspects

from domains.tech import (
    TECH_NUMERIC_PATTERNS,
    TECH_NAMED_PATTERNS,
    TECH_DATE_KEYWORDS,
    NAMED_ENTITY_MAPPING,
    UNIT_ASPECT_MAPPING
)

from domains.news import (
    NEWS_CATEGORIES,
    NEWS_NUMERIC_KEYWORDS,
    NEWS_DATE_KEYWORDS
)

nlp = spacy.load("en_core_web_sm")
 
# ---- Numeric ---- 

def extract_numeric(sentence, aspects):
    results = []
    sentence_lower = sentence.lower()

    for pattern in TECH_NUMERIC_PATTERNS:
        matches = re.finditer(pattern, sentence_lower)

        for match in matches:
            value = float(match.group(1))
            unit = match.group(2)

            # normalize unit (important)
            unit = unit.lower()

            aspect = UNIT_ASPECT_MAPPING.get(unit)
            if not aspect:
                continue

            results.append({
                "aspect": aspect,
                "value": value,
                "unit": unit,
                "type": "numeric"
            })

    return results

# ---- Date ---- 

def is_valid_date(text):
    import re

    months = [
        "january","february","march","april","may","june",
        "july","august","september","october","november","december"
    ]

    text_lower = text.lower()

    if any(m in text_lower for m in months):
        return True

    if re.search(r"\b(19|20)\d{2}\b", text):
        return True

    return False


def extract_dates(sentence, domain="tech"):
    doc = nlp(sentence)
    results = []

    sentence_lower = sentence.lower()

    if domain == "tech":
        keywords = TECH_DATE_KEYWORDS
    else:
        keywords = NEWS_DATE_KEYWORDS

    for ent in doc.ents:
        if ent.label_ == "DATE":
            text = ent.text.strip()

            if not is_valid_date(text):
                continue

            label = "date"

            for key, words in keywords.items():
                if any(w in sentence_lower for w in words):
                    label = key

            results.append({
                "aspect": label,
                "value": text,
                "type": "date"
            })

    return results


# ---- Named Values ----

def extract_named_values(sentence, aspects):
    results = []
    sentence_lower = sentence.lower()

    for pattern in TECH_NAMED_PATTERNS:
        matches = re.findall(pattern, sentence_lower)

        for match in matches:
            if isinstance(match, tuple):
                match = match[0]

            match_lower = match.lower()

            aspect = None

            for key, keywords in NAMED_ENTITY_MAPPING.items():
                if any(k in match_lower for k in keywords):
                    aspect = key
                    break

            if not aspect:
                aspect = aspects[0] if aspects else "unknown"

            results.append({
                "aspect": aspect,
                "value": match.strip(),
                "unit": None,
                "type": "named"
            })

    return results

# ---- Function ----

def extract_attributes(sentence, domain="generic"):
    results = []

    aspects = extract_aspects(sentence, domain=domain)

    # ---- domain fallback ----
    if domain == "generic":
        if aspects:
            domain = "tech"   # for now, simple rule

    results.extend(extract_numeric(sentence, aspects))
    results.extend(extract_dates(sentence, domain))
    results.extend(extract_named_values(sentence, aspects))

    # ---- Remove duplicates ----
    unique = []
    seen = set()

    for r in results:
        key = (r["aspect"], str(r["value"]), str(r.get("unit")))
        if key not in seen:
            seen.add(key)
            unique.append(r)

    return unique