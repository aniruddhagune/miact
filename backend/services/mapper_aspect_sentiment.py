import re
from backend.services.extractor_aspect import extract_aspects
from backend.services.objectivity_classifier import classify_sentence
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

analyzer = SentimentIntensityAnalyzer()

def split_sentence(sentence: str):
    # Only split on strong adversative conjunctions — preserve commas so opinions stay complete
    parts = re.split(
        r"\bbut\b|\bhowever\b|\bwhereas\b|\bnevertheless\b|;",
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
        score = analyzer.polarity_scores(part)["compound"]

        if not unique_aspects and abs(score) >= 0.25:
            unique_aspects.add("overall impression")

        if not unique_aspects:
            continue

        if len(unique_aspects) > 1:
            aspect = "multiple"
            results.append({
                "aspect": aspect,
                "sentiment": sentiment,
                "score": score,
                "text": part
            })
        else:
            aspect = list(unique_aspects)[0]
            results.append({
                "aspect": aspect,
                "sentiment": sentiment,
                "score": score,
                "text": part
            })

    return results