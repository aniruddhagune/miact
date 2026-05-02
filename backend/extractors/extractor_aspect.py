from backend.nlp.spacy_loader import nlp
import re


def extract_aspects(sentence: str, domain: str = "generic"):
    # ---- load domain-specific config ----
    if domain.startswith("tech"):
        from backend.domains.tech import (
            ASPECT_KEYWORDS,
            ASPECT_MAPPING,
            NOISE_TERMS,
            CATEGORY_TERMS
        )
    else:
        ASPECT_KEYWORDS = {}
        ASPECT_MAPPING = {}
        NOISE_TERMS = {}
        CATEGORY_TERMS = {}

    sentence_lower = sentence.lower()
    found_aspects = set()

    # ---- keyword detection (primary signal) ----
    for aspect, keywords in ASPECT_KEYWORDS.items():
        for word in keywords:
            if re.search(rf"\b{word}\b", sentence_lower):
                found_aspects.add(aspect)

    if found_aspects:
        return list(found_aspects)

    # ---- fallback (LIGHTWEIGHT) ----
    doc = nlp(sentence)

    for token in doc:
        if token.pos_ in ["NOUN", "PROPN"]:
            if token.dep_ in ["dobj", "nsubj", "pobj", "attr"]:
                word = token.text.lower()

                if any(char.isdigit() for char in word):
                    continue

                if word in NOISE_TERMS:
                    continue

                if word in CATEGORY_TERMS:
                    continue

                if len(word) <= 2:
                    continue

                if word in ["thing", "part", "feature", "system"]:
                    continue

                found_aspects.add(word)

    # ---- normalization ----
    final_aspects = set()

    for aspect in found_aspects:
        if aspect in ASPECT_MAPPING:
            final_aspects.add(ASPECT_MAPPING[aspect])
        else:
            final_aspects.add(aspect)

    return list(final_aspects)