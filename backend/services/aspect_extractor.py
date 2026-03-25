import spacy
import re

nlp = spacy.load("en_core_web_sm")


def extract_aspects(sentence: str, domain: str = "generic"):
    # ---- load domain-specific config ----
    if domain == "phone":
        from domains.phone_aspects import (
            ASPECT_KEYWORDS,
            ASPECT_MAPPING,
            NON_ASPECT_TERMS
        )
    else:
        ASPECT_KEYWORDS = {}
        ASPECT_MAPPING = {}
        NON_ASPECT_TERMS = []

    # ---- ALWAYS initialize these ----
    sentence_lower = sentence.lower()
    found_aspects = set()

    # ---- keyword detection ----
    for aspect, keywords in ASPECT_KEYWORDS.items():
        for word in keywords:
            if re.search(rf"\b{word}\b", sentence_lower):
                found_aspects.add(aspect)

    if found_aspects:
        return list(found_aspects)

    # ---- fallback ----
    doc = nlp(sentence)

    for token in doc:
        if token.pos_ == "NOUN":
            if token.dep_ in ["dobj", "nsubj", "pobj", "attr"]:
                text = token.text.lower()

                # ignore numbers/specs
                if any(char.isdigit() for char in text):
                    continue

                # ignore domain-specific non-aspects
                if any(term in text for term in NON_ASPECT_TERMS):
                    continue

                found_aspects.add(text)

    # ---- normalization ----
    final_aspects = set()

    for aspect in found_aspects:
        if aspect in ASPECT_MAPPING:
            final_aspects.add(ASPECT_MAPPING[aspect])
        else:
            final_aspects.add(aspect)

    return list(final_aspects)