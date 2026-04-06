"""
Shared sentiment lexicon for the MIACT data pipeline.
Commonly used positive and negative terms for rule-based scoring.
"""

POSITIVE_WORDS = {
    "good", "great", "excellent", "amazing", "fantastic", "awesome", "solid",
    "smooth", "fast", "responsive", "snappy", "fluid", "reliable", "stable",
    "bright", "sharp", "crisp", "clear", "premium", "comfortable", "impressive",
    "worth", "value", "love", "recommend", "quiet", "durable",
    "secure", "safe", "trusted",
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

POLARITY_INVERTERS = {
    "less", "least", "lower", "minimal", "lowly", "hardly", "barely"
}
