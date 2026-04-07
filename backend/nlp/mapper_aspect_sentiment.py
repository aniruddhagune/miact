import re
from backend.extractors.extractor_aspect import extract_aspects
from backend.nlp.objectivity_classifier import classify_sentence
from backend.nlp.grammar_structural import classify_clause
from backend.nlp.sentiment_lexicon import POSITIVE_WORDS, NEGATIVE_WORDS
from backend.config.variables import DEBUG

try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    analyzer = SentimentIntensityAnalyzer()
except ImportError:
    analyzer = None
    if DEBUG:
        print("[mapper] WARNING: vaderSentiment not found. Falling back to structural-only scoring.")


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

    prev_grammar: dict | None = None  # context window for incomplete sentences

    for part in parts:
        aspects = extract_aspects(part, domain)
        raw_sentiment = classify_sentence(part)

        # Pass previous result for incomplete-sentence context inheritance
        grammar = classify_clause(part, prev_result=prev_grammar)

        for metaphor_aspect in grammar["metaphor_aspects"]:
            if metaphor_aspect not in aspects:
                aspects.append(metaphor_aspect)

        # If sentence is incomplete and no aspects found, borrow aspect from previous
        if grammar["completeness"] == "incomplete" and not aspects and grammar.get("inherited_aspect"):
            aspects = [grammar["inherited_aspect"]]
            if DEBUG:
                print(f"[mapper] Inherited aspect '{grammar['inherited_aspect']}' for incomplete: '{part}'")

        # Pure factual questions with no sentiment words → skip
        if grammar["is_question"] and grammar["sentiment"] == "neutral" and not grammar["matched_terms"]:
            if DEBUG:
                print(f"[mapper] Skipping neutral question: '{part}'")
            prev_grammar = grammar
            continue

        if grammar["sentiment"] != "neutral":
            sentiment = grammar["sentiment"]
        elif "positive" in raw_sentiment:
            sentiment = "positive"
        elif "negative" in raw_sentiment:
            sentiment = "negative"
        else:
            sentiment = "neutral"

        unique_aspects = set(aspects)
        
        # VADER Fallback
        vader_score = 0.0
        if analyzer:
            vader_score = analyzer.polarity_scores(part)["compound"]
        
        score = grammar["score"] if (grammar["sentiment"] != "neutral" or not analyzer) else vader_score

        if not unique_aspects and abs(score) >= 0.25:
            unique_aspects.add("overall impression")

        if not unique_aspects:
            prev_grammar = grammar
            continue

        if DEBUG:
            print(f"[mapper] '{part[:60]}' → aspects={unique_aspects}, sentiment={sentiment}, score={score:.3f}")

        if len(unique_aspects) > 1:
            aspect = "multiple"
        else:
            aspect = list(unique_aspects)[0]

        results.append({
            "aspect": aspect,
            "sentiment": sentiment,
            "score": score,
            "text": part,
            "metadata": {
                "grammar_terms": grammar["matched_terms"],
                "comparison_cues": grammar["comparison_cues"],
                "is_question": grammar["is_question"],
                "completeness": grammar["completeness"],
            }
        })

        # Update context window for next part
        prev_grammar = {**grammar, "aspect": aspect}

    return results
