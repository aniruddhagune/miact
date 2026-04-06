import re

def detect_comparison(sentence: str):
    sentence_lower = sentence.lower()

    strong_patterns = [
        r"\bbetter than\b",
        r"\bworse than\b",
        r"\bcompared to\b",
        r"\bcompared with\b",
        r"\bmore than\b",
        r"\bless than\b",
        # r"\bthe previous generation\b",
        # r"\bthe next generation\b"
    ]

    weak_keywords = [
        "successor", "predecessor", "upgrade", "downgrade", "generation"
    ]

    if any(re.search(p, sentence_lower) for p in strong_patterns):
        return True

    if any(word in sentence_lower for word in weak_keywords):
        return True

    return False