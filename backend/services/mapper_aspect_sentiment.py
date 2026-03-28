import re
from backend.services.extractor_aspect import extract_aspects
from services.objectivity_classifier import classify_sentence


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
        raw_sentiment = classify_sentence(part)

        if "positive" in raw_sentiment:
            sentiment = "positive"
        elif "negative" in raw_sentiment:
            sentiment = "negative"
        else:
            sentiment = "neutral"

        unique_aspects = set(aspects)

        for aspect in unique_aspects:
            results.append({
                "aspect": aspect,
                "sentiment": sentiment,
                "text": part
            })

    return results