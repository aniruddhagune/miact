import spacy
import re

nlp = spacy.load("en_core_web_sm")


def extract_aspects(sentence: str, domain: str = "generic"):
    # ---- load domain-specific config ----
    if domain == "tech":
        from domains.tech import (
            ASPECT_KEYWORDS,
            ASPECT_MAPPING,
            NON_ASPECT_TERMS
        )
    else:
        ASPECT_KEYWORDS = {}
        ASPECT_MAPPING = {}
        NON_ASPECT_TERMS = []

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
        if token.pos_ == "NOUN":
            if token.dep_ in ["dobj", "nsubj", "pobj", "attr"]:
                word = token.text.lower()

                # skip numbers/spec noise
                if any(char.isdigit() for char in word):
                    continue

                # skip generic noise
                if word in NON_ASPECT_TERMS:
                    continue

                # 🔥 NEW: avoid ultra-generic nouns
                if len(word) <= 2:
                    continue

                # 🔥 NEW: ignore vague nouns
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