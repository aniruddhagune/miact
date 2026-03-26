from services.aspect_extractor import extract_aspects
from backend.services.objectivity_classifier import classify_sentence

import re

def split_sentence(sentence: str):
    parts = re.split(
        r"\bbut\b|\band\b|\bwhile\b|\bhowever\b|;|,",
        sentence,
        flags=re.IGNORECASE
    )
    return [p.strip() for p in parts if p.strip()]


def analyze_aspect_sentiment(sentence: str, domain: str = "generic"):
    results = []

    parts = split_sentence(sentence)

    for part in parts:
        aspects = extract_aspects(part, domain)
        sentiment = classify_sentence(part)

        unique_aspects = set(aspects)

    for aspect in unique_aspects:
        results.append({
            "aspect": aspect,
            "sentiment": sentiment,
            "text": part
        })

    return results