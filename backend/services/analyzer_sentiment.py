
# Adjectives, and data used for classification.

OPINION_WORDS = [
    "good", "bad", "excellent", "poor", "amazing",
    "terrible", "great", "awful", "best", "worst",
    "impressive", "disappointing"
]

NEUTRAL_WORDS = [
    "okay", "fine", "average", "decent", "acceptable"
]

POSITIVE_WORDS = [
    "excellent", "great", "amazing", "fantastic", "awesome",
    "good", "solid", "impressive", "outstanding", "superb",
    "smooth", "fast", "responsive", "snappy", "fluid",
    "reliable", "stable", "efficient",
    "bright", "vivid", "sharp", "crisp", "clear",
    "long-lasting", "durable", "powerful",
    "well-built", "premium", "comfortable"
]

NEGATIVE_WORDS = [
    "controversy", "controversial", "throttle", "throttling", "limit", "limited",
    "slower", "worse", "drop", "issue", "problem", "manipulation",
    "bad", "poor", "terrible", "awful", "horrible",
    "disappointing", "underwhelming", "mediocre",
    "slow", "laggy", "unresponsive", "sluggish",
    "dim", "blurry", "dull", "washed",
    "overheating", "unstable", "buggy", "inconsistent",
    "weak", "fragile", "cheap",
    "short", "drains", "limited"
]

POSITIVE_PATTERNS = [
    "works well",
    "performs well",
    "does a great job",
    "holds up well",
    "more than enough",
    "better than expected",
    "no issues",
    "no problems",
    "very good",
    "highly responsive",
    "well optimized",
    "too good"
]

NEGATIVE_PATTERNS = [
    "could be better",
    "needs improvement",
    "not enough",
    "not good",
    "not great",
    "not impressive",
    "not very",
    "falls short",
    "lacks",
    "suffers from",
    "issues with",
    "problem with",
    "struggles with",
    "fails to",
    "disappoints",
    "a bit slow",
    "too slow",
    "too heavy",
    "too expensive"
]

NEGATION_PATTERNS = [
    "not good",
    "not great",
    "not bad",        # tricky → positive
    "not impressive",
    "not worth",
]



def get_sentiment(text: str) -> str:
    """
    Returns:
        "positive", "negative", or "neutral"
    """
    text = text.lower()

    # ---- Strong patterns ----
    for pattern in NEGATIVE_PATTERNS:
        if pattern in text:
            return "negative"

    for pattern in POSITIVE_PATTERNS:
        if pattern in text:
            return "positive"

    # ---- Word-level ----
    for word in NEGATIVE_WORDS:
        if word in text:
            return "negative"

    for word in POSITIVE_WORDS:
        if word in text:
            return "positive"

    return "neutral"