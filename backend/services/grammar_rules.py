from __future__ import annotations

import re


POSITIVE_WORDS = {
    "good", "great", "excellent", "amazing", "fantastic", "awesome", "solid",
    "smooth", "fast", "responsive", "snappy", "fluid", "reliable", "stable",
    "bright", "sharp", "crisp", "clear", "premium", "comfortable", "impressive",
    "worth", "value", "love", "like", "recommend", "quiet", "durable",
}

NEGATIVE_WORDS = {
    "bad", "poor", "terrible", "awful", "horrible", "disappointing",
    "underwhelming", "mediocre", "slow", "laggy", "sluggish", "weak", "cheap",
    "dim", "blurry", "buggy", "unstable", "fragile", "overpriced", "hate",
    "worse", "limited", "issue", "problem", "hot", "noisy", "drain",
}

NEGATION_WORDS = {
    "not", "never", "hardly", "barely", "no", "without", "isn't", "wasn't",
    "doesn't", "don't", "didn't", "can't", "couldn't", "won't",
}

INTENSIFIERS = {
    "very": 0.12,
    "really": 0.12,
    "extremely": 0.2,
    "super": 0.18,
    "quite": 0.08,
    "pretty": 0.08,
    "slightly": -0.08,
    "somewhat": -0.06,
    "bit": -0.06,
}

COMPARISON_PATTERNS = {
    "better_than": re.compile(r"\bbetter than\b", re.IGNORECASE),
    "worse_than": re.compile(r"\bworse than\b", re.IGNORECASE),
    "like": re.compile(r"\blike\b", re.IGNORECASE),
    "unlike": re.compile(r"\bunlike\b", re.IGNORECASE),
    "compared_to": re.compile(r"\bcompared (?:to|with)\b", re.IGNORECASE),
    "other_than": re.compile(r"\bother than\b", re.IGNORECASE),
    "rest_of_the": re.compile(r"\brest of the\b", re.IGNORECASE),
    "except": re.compile(r"\bexcept(?: for)?\b", re.IGNORECASE),
}

METAPHOR_PATTERNS = {
    "performance": [
        re.compile(r"\bbuttery smooth\b", re.IGNORECASE),
        re.compile(r"\bflies through\b", re.IGNORECASE),
    ],
    "build": [
        re.compile(r"\bbuilt like a tank\b", re.IGNORECASE),
    ],
    "battery": [
        re.compile(r"\bbattery (?:is|feels) like a beast\b", re.IGNORECASE),
        re.compile(r"\bbattery beast\b", re.IGNORECASE),
    ],
}


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z']+", text.lower())


def _apply_negation(tokens: list[str], idx: int, base: int) -> int:
    window = tokens[max(0, idx - 3):idx]
    if any(token in NEGATION_WORDS for token in window):
        return -base
    return base


def _intensity_adjustment(tokens: list[str], idx: int) -> float:
    window = tokens[max(0, idx - 2):idx]
    adjustment = 0.0
    for token in window:
        adjustment += INTENSIFIERS.get(token, 0.0)
    return adjustment


def detect_comparison_cues(text: str) -> list[str]:
    found = []
    for label, pattern in COMPARISON_PATTERNS.items():
        if pattern.search(text):
            found.append(label)
    return found


def detect_metaphor_aspects(text: str) -> list[str]:
    matched = []
    for aspect, patterns in METAPHOR_PATTERNS.items():
        if any(pattern.search(text) for pattern in patterns):
            matched.append(aspect)
    return matched


def score_clause(text: str) -> tuple[float, list[str]]:
    tokens = _tokenize(text)
    score = 0.0
    matched_terms = []

    for idx, token in enumerate(tokens):
        if token in POSITIVE_WORDS:
            signed = _apply_negation(tokens, idx, 1)
            score += signed + (_intensity_adjustment(tokens, idx) * (1 if signed > 0 else -1))
            matched_terms.append(token)
        elif token in NEGATIVE_WORDS:
            signed = _apply_negation(tokens, idx, -1)
            score += signed + (_intensity_adjustment(tokens, idx) * (1 if signed > 0 else -1))
            matched_terms.append(token)

    lowered = text.lower()
    if "not bad" in lowered or "no issues" in lowered or "no problem" in lowered:
        score += 1.0
    if "could be better" in lowered or "falls short" in lowered:
        score -= 1.0

    comparison_cues = detect_comparison_cues(text)
    if "better_than" in comparison_cues:
        score += 0.75
    if "worse_than" in comparison_cues:
        score -= 0.75
    if any(cue in comparison_cues for cue in ["other_than", "except"]):
        score -= 0.15

    return score, matched_terms


def classify_clause(text: str) -> dict:
    score, matched_terms = score_clause(text)
    metaphors = detect_metaphor_aspects(text)
    comparisons = detect_comparison_cues(text)

    if score > 0.2:
        sentiment = "positive"
    elif score < -0.2:
        sentiment = "negative"
    else:
        sentiment = "neutral"

    return {
        "sentiment": sentiment,
        "score": max(-1.0, min(1.0, round(score / 3.0, 3))),
        "matched_terms": matched_terms,
        "metaphor_aspects": metaphors,
        "comparison_cues": comparisons,
    }
